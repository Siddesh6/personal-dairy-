import datetime
from sqlalchemy import Column, String, Boolean, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True)
    phone_number = Column(String(50), unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    profile_pic_url = Column(String, nullable=True)
    firebase_uid = Column(String(128), unique=True, index=True, nullable=False)
    is_premium = Column(Boolean, default=False)
    pin_hash = Column(String(60), nullable=True)
    encryption_salt = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
