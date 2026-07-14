import os
import sys
import time
import uuid
import urllib.parse
import requests
import subprocess
from gtts import gTTS
from PIL import Image, ImageDraw

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.database import SessionLocal
from app.models import Movie, MovieScene, Diary

# Output folder for finished movies (accessible statically from frontend port 8080)
OUTPUT_DIR = r"d:\dairy\frontend_web\movies"
TEMP_DIR = r"d:\dairy\backend\temp_render"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper to translate Windows absolute paths to WSL paths
def win_to_wsl_path(win_path):
    cleaned = win_path.replace('\\', '/')
    drive = cleaned[0].lower()
    path_part = cleaned[2:]
    return f"/mnt/{drive}{path_part}"

# Programmatic fallback image generator
def create_fallback_image(path, text):
    print(f"  [Fallback Image] Generating custom background with text: '{text[:40]}...'")
    img = Image.new('RGB', (1024, 1024), color='#0B0B0F')
    draw = ImageDraw.Draw(img)
    
    # Draw geometric patterns for a high-tech/creative look
    draw.ellipse((100, 100, 924, 924), fill='#0E0E14', outline='#8B5CF6', width=6)
    draw.ellipse((200, 200, 824, 824), fill='#141420', outline='#F472B6', width=4)
    draw.ellipse((350, 350, 674, 674), fill='#1C1C30', outline='#14B8A6', width=2)
    
    # Wrap text
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
        # Draw text at center anchor 'mm'
        draw.text((512, y_text), line, fill='#F3F4F6', align='center', anchor='mm')
        y_text += 35
        
    # Overlay app tag
    draw.text((512, 850), "L I F E M O V I E  A I", fill='#9CA3AF', align='center', anchor='mm')
    
    img.save(path)

def send_progress(movie_id, user_id, message):
    try:
        url = f"http://127.0.0.1:8000/api/v1/movies/{movie_id}/progress"
        r = requests.post(url, json={"user_id": str(user_id), "message": message}, timeout=5)
        print(f"  [Progress Event] sent: '{message}' (Status: {r.status_code})")
    except Exception as e:
        print(f"  [Progress Event Error] Failed to send '{message}': {e}")

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
    
    # 2. Divide narrative into 3 scenes
    full_narrative = " ".join(narrative_texts)
    sentences = [s.strip() for s in full_narrative.split('.') if s.strip()]
    if not sentences:
        sentences = [f"This is the story of {movie.title}."]
        
    chunk_size = max(1, len(sentences) // 3)
    scene_scripts = []
    for i in range(3):
        start = i * chunk_size
        end = None if i == 2 else (i + 1) * chunk_size
        segment = ". ".join(sentences[start:end]) + "."
        if not segment.strip() or segment == ".":
            segment = f"And that concludes our memories of {movie.title}."
        scene_scripts.append(segment)
        
    print(f"[Worker] Split narrative into 3 scene scripts:\n - Scene 1: {scene_scripts[0]}\n - Scene 2: {scene_scripts[1]}\n - Scene 3: {scene_scripts[2]}")

    scene_files = []
    style_suffix = f" in a beautiful {movie.style_preset} cartoon 2d animation style"
    
    # 3. Process each scene
    for idx, script in enumerate(scene_scripts):
        send_progress(movie.id, movie.user_id, f"Processing scene {idx+1} of 3...")
        print(f"[Worker] Processing Scene {idx+1}/3...")
        
        # A. Get visual prompt
        words = script.replace('.', '').replace(',', '').split()
        core_prompt = " ".join(words[:12]) if len(words) > 12 else " ".join(words)
        visual_prompt = f"{core_prompt}{style_suffix}"
        
        # B. Download scene image from Pollinations AI (with retries and backoff)
        encoded_prompt = urllib.parse.quote(visual_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={idx+42}"
        
        temp_img_path = os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.jpg")
        download_success = False
        
        # Retries loop (3 attempts)
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
                
        # If download failed, create programmatic fallback
        if not download_success:
            create_fallback_image(temp_img_path, core_prompt)
            
        # C. Generate scene narration voice (gTTS)
        temp_audio_path = os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.mp3")
        print(f"  Generating TTS narration: '{script[:40]}...'")
        tts = gTTS(text=script, lang='en')
        tts.save(temp_audio_path)
        
        # D. Stitch Image + Audio into temporary video clip using FFmpeg in WSL
        temp_clip_path = os.path.join(TEMP_DIR, f"scene_{movie.id}_{idx}.mp4")
        wsl_img = win_to_wsl_path(temp_img_path)
        wsl_aud = win_to_wsl_path(temp_audio_path)
        wsl_clip = win_to_wsl_path(temp_clip_path)
        
        send_progress(movie.id, movie.user_id, f"Encoding video clip for scene {idx+1}/3...")
        print(f"  Encoding scene video clip via WSL FFmpeg...")
        cmd = [
            "wsl", "ffmpeg", "-y",
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
            cmd_fallback = [
                "wsl", "ffmpeg", "-y",
                "-loop", "1", "-i", wsl_img,
                "-i", wsl_aud,
                "-c:v", "libx264", "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                "-shortest", wsl_clip
            ]
            subprocess.run(cmd_fallback)
            
        scene_files.append(temp_clip_path)
        
        # Create MovieScene record in database
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
    
    cmd_concat = [
        "wsl", "ffmpeg", "-y",
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
    print("      LIFEMOVIE AI VIDEO GENERATOR WORKER")
    print("      Listening for rendering tasks... (Ctrl+C to exit)")
    print("====================================================")
    
    while True:
        db = SessionLocal()
        try:
            # Query for movies in "rendering" status
            rendering_movies = db.query(Movie).filter(Movie.status == "rendering").all()
            for movie in rendering_movies:
                # To prevent double processing, only run if it has no scenes generated yet
                if len(movie.scenes) == 0:
                    process_movie(db, movie)
        except Exception as e:
            print(f"[Worker Error] {e}")
        finally:
            db.close()
            
        time.sleep(5)

if __name__ == "__main__":
    main()
