#!/bin/sh
# Start the video background worker process in the background
python video_worker.py &

# Start the FastAPI uvicorn server in the foreground
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
