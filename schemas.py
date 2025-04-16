from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    developer = "developer"
    user = "user"

class LoginUser(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class PostUser(BaseModel):
    email: EmailStr
    username: Optional[str]
    password: str
    role: Optional[UserRole] = UserRole.user

    class Config:
        orm_mode = True
        use_enum_values = True

class NoteEvent(BaseModel):
    note: str
    time: float
    duration: float
    velocity: float = 0.8

class MidiRequest(BaseModel):
    name: str
    instrument_name: str
    notes: List[NoteEvent]


# class UserResponse(BaseModel):
#     id: UUID
#     username: str
#     email: EmailStr

#     class Config:
#         orm_mode = True

# class LoginResponse(BaseModel):
#     access_token: str
#     refresh_token: str