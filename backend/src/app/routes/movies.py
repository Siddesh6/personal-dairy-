from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models.movie import Movie, MovieScene
from ..models.user import User
from ..websocket_manager import manager
from pydantic import BaseModel
from datetime import datetime
from ..dependencies import get_current_user_db

router = APIRouter(prefix="/movies", tags=["movies"])

# Pydantic Schemas
class MovieBase(BaseModel):
    title: str
    style_preset: str
    summary: str | None = None

class MovieCreate(MovieBase):
    user_id: UUID

class MovieProgress(BaseModel):
    user_id: UUID
    message: str

class MovieResponse(MovieBase):
    id: UUID
    user_id: UUID
    status: str
    rendered_video_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[MovieResponse])
def read_movies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    return db.query(Movie).filter(Movie.user_id == current_user.id).all()

@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
def create_movie(movie_in: MovieCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    db_movie = Movie(
        user_id=current_user.id,
        title=movie_in.title,
        style_preset=movie_in.style_preset,
        summary=movie_in.summary,
        status="pending"
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@router.get("/{movie_id}", response_model=MovieResponse)
def read_movie(movie_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id, Movie.user_id == current_user.id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie job not found")
    return db_movie

@router.post("/{movie_id}/trigger-render", response_model=MovieResponse)
def trigger_render(movie_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id, Movie.user_id == current_user.id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie job not found")
    db_movie.status = "rendering"
    db.commit()
    db.refresh(db_movie)
    return db_movie

@router.post("/{movie_id}/progress", status_code=status.HTTP_200_OK)
async def update_movie_progress(movie_id: UUID, progress_in: MovieProgress, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie job not found")
    
    await manager.broadcast_to_user(
        client_id=str(progress_in.user_id),
        message={
            "type": "render_progress",
            "title": db_movie.title,
            "message": progress_in.message
        }
    )
    return {"status": "broadcasted"}
