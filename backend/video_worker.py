import os
import sys
import time
import uuid
import urllib.parse
import requests
import subprocess
import json
from gtts import gTTS
from PIL import Image, ImageDraw

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.database import SessionLocal
from app.models import Movie, MovieScene, Diary
from app.config import settings

# Detect if running in Linux (Docker) or Windows
IS_LINUX = sys.platform.startswith('linux') or os.path.exists('/.dockerenv')

if IS_LINUX:
    OUTPUT_DIR = "/app/movies"
    TEMP_DIR = "/app/temp_render"
else:
    OUTPUT_DIR = r"d:\dairy\frontend_web\movies"
    TEMP_DIR = r"d:\dairy\backend\temp_render"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper to translate Windows absolute paths to WSL paths
def win_to_wsl_path(win_path):
    if IS_LINUX:
        return win_path.replace('\\', '/')
    cleaned = win_path.replace('\\', '/')
    drive = cleaned[0].lower()
    path_part = cleaned[2:]
    return f"/mnt/{drive}{path_part}"

# Helper to prefix ffmpeg commands
def get_ffmpeg_prefix():
    if IS_LINUX:
        return ["ffmpeg"]
    return ["wsl", "ffmpeg"]

# Programmatic fallback image generator
def create_fallback_image(path, text):
    print(f"  [Fallback Image] Generating custom background with text: '{text[:40]}...'")
    img = Image.new('RGB', (1024, 1024), color='#0B0B0F')
    draw = ImageDraw.Draw(img)
    
    draw.ellipse((100, 100, 924, 924), fill='#0E0E14', outline='#8B5CF6', width=6)
    draw.ellipse((200, 200, 824, 824), fill='#141420', outline='#F472B6', width=4)
    draw.ellipse((350, 350, 674, 674), fill='#1C1C30', outline='#14B8A6', width=2)
    
    words = text.split()
    lines = []
    current_line = []
    for w in words:
        if len(" ".join(current_line + [w])) > 25:
            lines.append(" ".join(current_line))
            current_line = [w]
        else:
            current_line.append(w)
    if current_line:
        lines.append(" ".join(current_line))
        
    y_text = 450 - (len(lines) * 15)
    for line in lines:
        draw.text((512, y_text), line, fill='#F3F4F6', align='center', anchor='mm')
        y_text += 35
        
    draw.text((512, 850), "S O U L B O O K", fill='#9CA3AF', align='center', anchor='mm')
    img.save(path)

# Send Progress via WebSocket Broadcast API
def send_progress(movie_id, user_id, message):
    try:
        # If in Docker, use container network URL, otherwise localhost
        host = "backend:8000" if IS_LINUX else "127.0.0.1:8000"
        url = f"http://{host}/api/v1/movies/{movie_id}/progress"
        r = requests.post(url, json={"user_id": str(user_id), "message": message}, timeout=5)
        print(f"  [Progress Event] sent: '{message}' (Status: {r.status_code})")
    except Exception as e:
        print(f"  [Progress Event Error] Failed to send '{message}': {e}")

# Gemini API Integration for cinematic script splitting
def get_story_from_gemini(narrative_text):
    if not settings.GEMINI_API_KEY:
        print("  [Gemini API] Key not set. Falling back to local split.")
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    prompt = f"""
    You are a professional film screenwriter. 
    Take the following personal memories and split them into 3 distinct scenes for a movie. 
    For each scene, return a visual image prompt (description of what we see, styled visually) and a matching voiceover narration script.
    Return the output as a valid JSON array of exactly 3 elements, formatted like this:
    [
      {{"scene": 1, "image_prompt": "cinematic sunset photo of...", "narration": "We started our trip..."}},
      {{"scene": 2, "image_prompt": "cinematic photo of...", "narration": "Then we went to..."}},
      {{"scene": 3, "image_prompt": "cinematic photo of...", "narration": "Finally, we closed the night..."}}
    ]
    Do not include markdown tags like ```json in the output. Just return raw JSON.
    
    Memory context: {narrative_text}
    """
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            result = r.json()
            text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            if text.startswith("```"):
                text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
    except Exception as e:
        print(f"  [Gemini Error] Fallback to sentence split: {e}")
    return None

# ElevenLabs Vocal Synthesis Integration
def generate_elevenlabs_tts(script, path):
    if not settings.ELEVENLABS_API_KEY:
        return False
    
    voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": script,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"  [ElevenLabs Error] Fallback to gTTS: {e}")
    return False

def process_movie(db, movie):
    print(f"\n[Worker] Starting render for movie: {movie.title} (ID: {movie.id})")
    movie.status = "rendering"
    db.commit()
    send_progress(movie.id, movie.user_id, "Gathering narratives and splitting scenes...")
    
    # 1. Gather narrative text
    narrative_texts = []
    if movie.diaries:
        print(f"[Worker] Found {len(movie.diaries)} associated diaries.")
        for d in movie.diaries:
            if d.content_raw:
                narrative_texts.append(d.content_raw)
    
    if not narrative_texts:
        if movie.summary:
            narrative_texts.append(movie.summary)
        else:
            narrative_texts.append(f"A story about a happy memory titled {movie.title}.")
    
    full_narrative = " ".join(narrative_texts)
    
    # 2. Divide narrative into 3 scenes (using Gemini or fallback)
    scene_data = get_story_from_gemini(full_narrative)
    
    scene_scripts = []
    scene_prompts = []
    
    if scene_data and len(scene_data) == 3:
        print("[Worker] Successfully retrieved script breakdown from Gemini API.")
        for item in scene_data:
            scene_scripts.append(item.get("narration", ""))
            scene_prompts.append(item.get("image_prompt", ""))
    else:
        # Fallback to local sentence splitting
        sentences = [s.strip() for s in full_narrative.split('.') if s.strip()]
        if not sentences:
            sentences = [f"This is the story of {movie.title}."]
            
        chunk_size = max(1, len(sentences) // 3)
        for i in range(3):
            start = i * chunk_size
            end = None if i == 2 else (i + 1) * chunk_size
            segment = ". ".join(sentences[start:end]) + "."
            if not segment.strip() or segment == ".":
                segment = f"And that concludes our memories of {movie.title}."
            scene_scripts.append(segment)
            
            # Form simple prompts
            words = segment.replace('.', '').replace(',', '').split()
            core = " ".join(words[:12]) if len(words) > 12 else " ".join(words)
            scene_prompts.append(core)
            
        print("[Worker] Local sentence splitting fallback applied.")

    scene_files = []
    style_suffix = f" in a beautiful {movie.style_preset} cartoon 2d animation style"
    
    # 3. Process each scene
    for idx, script in enumerate(scene_scripts):
        send_progress(movie.id, movie.user_id, f"Processing scene {idx+1} of 3...")
        print(f"[Worker] Processing Scene {idx+1}/3...")
        
        visual_prompt = f"{scene_prompts[idx]}{style_suffix}"
        
        # Download scene image from Pollinations AI
        encoded_prompt = urllib.parse.quote(visual_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={idx+42}"
        
        temp_img_path = os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.jpg")
        download_success = False
        
        for attempt in range(1, 4):
            print(f"  Downloading image (Attempt {attempt}/3) from: {image_url}")
            try:
                r = requests.get(image_url, timeout=12)
                if r.status_code == 200:
                    with open(temp_img_path, 'wb') as f:
                        f.write(r.content)
                    download_success = True
                    break
                elif r.status_code == 429:
                    print("    Rate limited (429). Retrying after 3 seconds...")
                    time.sleep(3)
                else:
                    print(f"    Failed with status code {r.status_code}. Retrying...")
                    time.sleep(2)
            except Exception as e:
                print(f"    Exception occurred: {e}. Retrying...")
                time.sleep(2)
                
        if not download_success:
            create_fallback_image(temp_img_path, scene_prompts[idx])
            
        # Generate scene narration voice (ElevenLabs or fallback gTTS)
        temp_audio_path = os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.mp3")
        print(f"  Generating vocal narration: '{script[:40]}...'")
        
        tts_success = generate_elevenlabs_tts(script, temp_audio_path)
        if not tts_success:
            print("  Falling back to local gTTS synthesis.")
            tts = gTTS(text=script, lang='en')
            tts.save(temp_audio_path)
        
        # Stitch Image + Audio into temporary video clip using FFmpeg
        temp_clip_path = os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.mp4")
        wsl_img = win_to_wsl_path(temp_img_path)
        wsl_aud = win_to_wsl_path(temp_audio_path)
        wsl_clip = win_to_wsl_path(temp_clip_path)
        
        send_progress(movie.id, movie.user_id, f"Encoding video clip for scene {idx+1}/3...")
        print(f"  Encoding scene video clip via FFmpeg...")
        
        cmd = get_ffmpeg_prefix() + [
            "-y",
            "-loop", "1", "-i", wsl_img,
            "-i", wsl_aud,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest", wsl_clip
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  FFmpeg Error (Scene {idx+1}): {res.stderr}. Retrying fallback encoding...")
            cmd_fallback = get_ffmpeg_prefix() + [
                "-y",
                "-loop", "1", "-i", wsl_img,
                "-i", wsl_aud,
                "-c:v", "libx264", "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                "-shortest", wsl_clip
            ]
            subprocess.run(cmd_fallback)
            
        scene_files.append(temp_clip_path)
        
        scene_record = MovieScene(
            movie_id=movie.id,
            scene_order=idx + 1,
            visual_prompt=visual_prompt,
            narration_script=script,
            duration_seconds=max(3, len(script.split()) // 2)
        )
        db.add(scene_record)
        db.commit()

    # 4. Merge/Concatenate the 3 scene clips into final movie
    send_progress(movie.id, movie.user_id, "Concatenating scenes into final movie...")
    print("[Worker] Concatenating scenes into final movie...")
    concat_list_path = os.path.join(TEMP_DIR, f"concat_{movie.id}.txt")
    with open(concat_list_path, 'w') as f:
        for file in scene_files:
            f.write(f"file '{win_to_wsl_path(file)}'\n")
            
    final_output_path = os.path.join(OUTPUT_DIR, f"{movie.id}.mp4")
    
    wsl_list = win_to_wsl_path(concat_list_path)
    wsl_out = win_to_wsl_path(final_output_path)
    
    cmd_concat = get_ffmpeg_prefix() + [
        "-y",
        "-f", "concat", "-safe", "0",
        "-i", wsl_list,
        "-c", "copy",
        wsl_out
    ]
    res_concat = subprocess.run(cmd_concat, capture_output=True, text=True)
    
    if res_concat.returncode == 0:
        print(f"[Worker] Success! Movie written to: {final_output_path}")
        movie.status = "completed"
        movie.rendered_video_url = f"/movies/{movie.id}.mp4"
        movie.duration_seconds = sum(max(3, len(s.split()) // 2) for s in scene_scripts)
        send_progress(movie.id, movie.user_id, "Movie rendering completed successfully!")
    else:
        print(f"[Worker] Concatenation failed: {res_concat.stderr}")
        movie.status = "failed"
        movie.rendering_error = res_concat.stderr
        send_progress(movie.id, movie.user_id, f"Movie rendering failed: {res_concat.stderr}")
        
    db.commit()
    
    # Cleanup temp files
    print("[Worker] Cleaning up temporary files...")
    for idx in range(3):
        try:
            os.remove(os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.jpg"))
            os.remove(os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.mp3"))
            os.remove(os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.mp4"))
        except:
            pass
    try:
        os.remove(concat_list_path)
    except:
        pass

def main():
    print("====================================================")
    print("      SOULBOOK VIDEO GENERATOR WORKER")
    print("      Listening for rendering tasks... (Ctrl+C to exit)")
    print("====================================================")
    
    while True:
        db = SessionLocal()
        try:
            rendering_movies = db.query(Movie).filter(Movie.status == "rendering").all()
            for movie in rendering_movies:
                if len(movie.scenes) == 0:
                    process_movie(db, movie)
        except Exception as e:
            print(f"[Worker Error] {e}")
        finally:
            db.close()
            
        time.sleep(5)

if __name__ == "__main__":
    main()
