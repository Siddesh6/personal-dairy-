import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Float, LargeBinary, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base

class MoodType(str, enum.Enum):
    joyful = "joyful"
    nostalgic = "nostalgic"
    calm = "calm"
    excited = "excited"
    melancholy = "melancholy"
    anxious = "anxious"

class PrivacyType(str, enum.Enum):
    standard = "standard"
    hidden = "hidden"
    encrypted = "encrypted"

# Many-to-Many association table for diaries and characters
diary_characters = Table(
    "diary_characters",
    Base.metadata,
    Column("diary_id", UUID(as_uuid=True), ForeignKey("diaries.id", ondelete="CASCADE"), primary_key=True),
    Column("character_id", UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)
)

class Diary(Base):
    __tablename__ = "diaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    family_group_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String(255), nullable=False)
    content_raw = Column(String, nullable=True)
    content_encrypted = Column(LargeBinary, nullable=True)
    voice_transcript = Column(String, nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    location_name = Column(String(255), nullable=True)
    weather_condition = Column(String(100), nullable=True)
    weather_temp_c = Column(Float, nullable=True)
    mood = Column(Enum(MoodType), nullable=True)
    mood_intensity = Column(Float, default=1.0)
    privacy_level = Column(Enum(PrivacyType), default=PrivacyType.standard)
    is_favorite = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    media = relationship("DiaryMedia", back_populates="diary", cascade="all, delete-orphan")
    characters = relationship("Character", secondary=diary_characters)

class DiaryMedia(Base):
    __tablename__ = "diary_media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diary_id = Column(UUID(as_uuid=True), ForeignKey("diaries.id", ondelete="CASCADE"), nullable=False)
    media_url = Column(String, nullable=False)
    media_type = Column(String(50), nullable=False)  # 'image', 'video', 'pdf'
    ocr_text = Column(String, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    diary = relationship("Diary", back_populates="media")
