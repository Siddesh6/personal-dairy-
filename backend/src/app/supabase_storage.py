import os
import requests
import mimetypes

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Use the service_role key to bypass RLS

def upload_file_to_supabase(bucket: str, file_path: str, filename: str) -> str:
    """
    Uploads a local file to a Supabase storage bucket.
    Returns the public URL of the uploaded file.
    If Supabase is not configured, returns None.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
        
    base_url = SUPABASE_URL.rstrip('/')
    url = f"{base_url}/storage/v1/object/{bucket}/{filename}"
    
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
        
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
        "Content-Type": mime_type,
        "x-upsert": "true"
    }
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return f"{base_url}/storage/v1/object/public/{bucket}/{filename}"
        else:
            print(f"Supabase upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error uploading file to Supabase: {e}")
        return None

def upload_bytes_to_supabase(bucket: str, file_data: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """
    Uploads file bytes directly to a Supabase storage bucket.
    Returns the public URL of the uploaded file.
    If Supabase is not configured, returns None.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
        
    base_url = SUPABASE_URL.rstrip('/')
    url = f"{base_url}/storage/v1/object/{bucket}/{filename}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true"
    }
    
    try:
        response = requests.post(url, headers=headers, data=file_data)
        if response.status_code == 200:
            return f"{base_url}/storage/v1/object/public/{bucket}/{filename}"
        else:
            print(f"Supabase upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error uploading bytes to Supabase: {e}")
        return None
