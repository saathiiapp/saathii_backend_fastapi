from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from enum import Enum


class SexEnum(str, Enum):
    male = "male"
    female = "female"


class UserResponse(BaseModel):
    user_id: int
    phone: str
    username: Optional[str] = None
    sex: Optional[SexEnum] = None
    dob: Optional[date] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    rating: Optional[int] = None
    country: Optional[str] = None
    role: Optional[str] = None


class EditUserRequest(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
