from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import diaries, characters, movies
from typing import Dict, List

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual Flutter web URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# WebSocket Manager for real-time AI render notifications
from .websocket_manager import manager

@websocket_route := app.websocket("/ws/v1/jobs/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle messages from clients if necessary
            await manager.send_personal_message(f"Ping received. Client: {client_id}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)
