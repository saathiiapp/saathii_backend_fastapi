from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from enum import Enum


class SexEnum(str, Enum):
    male = "male"
    female = "female"


class OTPRequest(BaseModel):
    phone: str = Field(..., example="+918709996580")


class VerifyRequest(BaseModel):
    phone: str
    otp: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyResponse(BaseModel):
    status: str  # "registered" | "needs_registration"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    registration_token: Optional[str] = None


class RegisterRequest(BaseModel):
    registration_token: str
    username: str
    sex: Optional[SexEnum] = None
    dob: Optional[date] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    profile_image_url: Optional[str] = None
    preferred_language: Optional[str] = None
    role: Optional[str] = None
