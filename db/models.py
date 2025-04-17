import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime, LargeBinary, Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum
from datetime import datetime

MainBase = declarative_base()
FileBase = declarative_base()

class UserRole(Enum):
    developer = "developer"
    user = "user"

class User(MainBase):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.user)

    midi_files = relationship("MidiMetadata", back_populates="user", cascade="all, delete-orphan")

class MidiMetadata(MainBase):
    __tablename__ = "midi_metadata"

    id = Column(UUID, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_id = Column(UUID, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="midi_files")

class MidiFile(FileBase):
    __tablename__ = "midi_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_name = Column(String, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)