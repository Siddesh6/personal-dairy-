from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models.character import Character
from pydantic import BaseModel
from datetime import datetime
from ..dependencies import verify_token

router = APIRouter(prefix="/characters", tags=["characters"])

# Pydantic Schemas
class CharacterBase(BaseModel):
    name: str
    nickname: str | None = None
    relationship_type: str
    age: int | None = None
    gender: str
    hair_style_prompt: str | None = None
    skin_tone_prompt: str | None = None
    body_type_prompt: str | None = None
    personality_prompt: str | None = None
    background_story: str | None = None

class CharacterCreate(CharacterBase):
    user_id: UUID

class CharacterResponse(CharacterBase):
    id: UUID
    user_id: UUID
    is_archived: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CharacterResponse])
def read_characters(db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    user_id = current_user.get("sub")
    return db.query(Character).all()

@router.post("/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(char_in: CharacterCreate, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    user_id = current_user.get("sub") or char_in.user_id
    db_char = Character(
        user_id=user_id,
        name=char_in.name,
        nickname=char_in.nickname,
        relationship_type=char_in.relationship_type,
        age=char_in.age,
        gender=char_in.gender,
        hair_style_prompt=char_in.hair_style_prompt,
        skin_tone_prompt=char_in.skin_tone_prompt,
        body_type_prompt=char_in.body_type_prompt,
        personality_prompt=char_in.personality_prompt,
        background_story=char_in.background_story
    )
    db.add(db_char)
    db.commit()
    db.refresh(db_char)
    return db_char

@router.get("/{character_id}", response_model=CharacterResponse)
def read_character(character_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(verify_token)):
    db_char = db.query(Character).filter(Character.id == character_id).first()
    if not db_char:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_char
