import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base

class CharacterGender(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non-binary"
    other = "other"

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    family_group_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(100), nullable=False)
    nickname = Column(String(100), nullable=True)
    relationship_type = Column(String(100), nullable=False)  # 'relationship' keyword is SQL/SQLAlchemy protected, using relationship_type
    age = Column(Integer, nullable=True)
    gender = Column(Enum(CharacterGender), nullable=False)
    hair_style_prompt = Column(String, nullable=True)
    skin_tone_prompt = Column(String, nullable=True)
    body_type_prompt = Column(String, nullable=True)
    personality_prompt = Column(String, nullable=True)
    voice_clone_id = Column(String(100), nullable=True)
    background_story = Column(String, nullable=True)
    model_lora_path = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    photos = relationship("CharacterPhoto", back_populates="character", cascade="all, delete-orphan")

class CharacterPhoto(Base):
    __tablename__ = "character_photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    photo_url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    character = relationship("Character", back_populates="photos")
