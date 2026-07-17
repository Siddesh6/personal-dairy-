import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .routes import diaries, characters, movies
from .websocket_manager import manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static folder to serve uploaded photos/videos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount movies static folder in backend if needed (worker outputs files to frontend/movies, but we can mount it here as well)
import sys
IS_LINUX = sys.platform.startswith('linux') or os.path.exists('/.dockerenv')
if IS_LINUX:
    MOVIES_DIR = "/app/movies"
else:
    MOVIES_DIR = r"d:\dairy\frontend_web\movies"

os.makedirs(MOVIES_DIR, exist_ok=True)
app.mount("/movies", StaticFiles(directory=MOVIES_DIR), name="movies")


# Register Routers
app.include_router(diaries.router, prefix=settings.API_V1_STR)
app.include_router(characters.router, prefix=settings.API_V1_STR)
app.include_router(movies.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

@websocket_route := app.websocket("/ws/v1/jobs/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Ping received. Client: {client_id}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)
