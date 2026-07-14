import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from ..database import Base

class JobStatus(str, enum.Enum):
    pending = "pending"
    transcribing = "transcribing"
    storyboard_ready = "storyboard_ready"
    rendering = "rendering"
    completed = "completed"
    failed = "failed"

# Many-to-Many association table for movies and diaries
movie_diaries = Table(
    "movie_diaries",
    Base.metadata,
    Column("movie_id", UUID(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("diary_id", UUID(as_uuid=True), ForeignKey("diaries.id", ondelete="CASCADE"), primary_key=True)
)

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    family_group_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String(255), nullable=False)
    summary = Column(String, nullable=True)
    style_preset = Column(String(50), nullable=False)  # 'pixar', 'cinematic', etc.
    rendered_video_url = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    rendering_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    scenes = relationship("MovieScene", back_populates="movie", cascade="all, delete-orphan")
    diaries = relationship("Diary", secondary=movie_diaries)

class MovieScene(Base):
    __tablename__ = "movie_scenes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    scene_order = Column(Integer, nullable=False)
    visual_prompt = Column(String, nullable=False)
    narration_script = Column(String, nullable=True)
    narration_voice_id = Column(String(100), nullable=True)
    background_music_url = Column(String, nullable=True)
    rendered_clip_url = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=False, default=4)
    camera_movement = Column(String(100), nullable=True)
    weather_override = Column(String(50), nullable=True)
    expression_override = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    movie = relationship("Movie", back_populates="scenes")
