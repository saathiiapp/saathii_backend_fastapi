from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class UserResponse(BaseModel):
    user_id: int
    phone: str
    username: Optional[str]
    dob: Optional[date]
    bio: Optional[str]
    interests: Optional[List[str]]
    profile_photo: Optional[str]
    preferred_language: Optional[str]


class EditUserRequest(BaseModel):
    username: Optional[str]
    bio: Optional[str]
    interests: Optional[List[str]]
    profile_photo: Optional[str]
    preferred_language: Optional[str]
