from sqlalchemy import Column, String, DateTime, LargeBinary, Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from datetime import datetime

Base = declarative_base()

class UserRole(Enum):
    developer = "developer"
    user = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.user)

class MidiFile(Base):
    __tablename__ = "midi_files"

    id = Column(String, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)