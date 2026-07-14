from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models.diary import Diary, DiaryMedia
from pydantic import BaseModel
from datetime import datetime
from ..dependencies import verify_token

router = APIRouter(prefix="/diaries", tags=["diaries"])

# Pydantic Schemas
class DiaryBase(BaseModel):
    title: str
    content_raw: str | None = None
    location_name: str | None = None
    weather_condition: str | None = None
    weather_temp_c: float | None = None
    mood: str | None = None
    mood_intensity: float | None = 1.0
    privacy_level: str = "standard"
    is_draft: bool = True

class DiaryCreate(DiaryBase):
    user_id: UUID

class DiaryResponse(DiaryBase):
    id: UUID
    user_id: UUID
    captured_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[DiaryResponse])
def read_diaries(db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    # Authenticate and query diaries
    user_id = current_user.get("sub")
    return db.query(Diary).all()

@router.post("/", response_model=DiaryResponse, status_code=status.HTTP_201_CREATED)
def create_diary(diary_in: DiaryCreate, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    # Override user_id from token if present, otherwise fallback to request input
    user_id = current_user.get("sub") or diary_in.user_id
    db_diary = Diary(
        user_id=user_id,
        title=diary_in.title,
        content_raw=diary_in.content_raw,
        location_name=diary_in.location_name,
        weather_condition=diary_in.weather_condition,
        weather_temp_c=diary_in.weather_temp_c,
        mood=diary_in.mood,
        mood_intensity=diary_in.mood_intensity,
        privacy_level=diary_in.privacy_level,
        is_draft=diary_in.is_draft
    )
    db.add(db_diary)
    db.commit()
    db.refresh(db_diary)
    return db_diary

@router.get("/{diary_id}", response_model=DiaryResponse)
def read_diary(diary_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    db_diary = db.query(Diary).filter(Diary.id == diary_id).first()
    if not db_diary:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    return db_diary

@router.delete("/{diary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diary(diary_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    db_diary = db.query(Diary).filter(Diary.id == diary_id).first()
    if not db_diary:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    db.delete(db_diary)
    db.commit()
    return
