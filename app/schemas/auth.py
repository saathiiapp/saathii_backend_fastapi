from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from enum import Enum


class SexEnum(str, Enum):
    male = "male"
    female = "female"


class OTPRequest(BaseModel):
    phone: str = Field(..., example="+919876543210")


class VerifyRequest(BaseModel):
    phone: str
    otp: str
    username: Optional[str] = None
    sex: Optional[SexEnum] = None
    dob: Optional[date] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = []
    profile_photo: Optional[str] = None
    preferred_language: Optional[str] = None
    role: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
