from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ReportUserRequest(BaseModel):
    reported_id: int = Field(..., description="ID of the user to report")
    reason: Optional[str] = Field(None, description="Optional reason for reporting")


class ReportActionResponse(BaseModel):
    success: bool
    message: str
    reported_id: int
    is_reported: bool


class ReportedUser(BaseModel):
    user_id: int
    username: Optional[str] = None
    sex: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    reason: Optional[str] = None
    reported_at: datetime


class ReportedUsersResponse(BaseModel):
    reported_users: List[ReportedUser]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool


class AdminReportedUser(BaseModel):
    report_id: str
    reporter_id: int
    reporter_username: Optional[str] = None
    reported_id: int
    reported_username: Optional[str] = None
    reported_sex: Optional[str] = None
    reported_bio: Optional[str] = None
    reported_profile_image_url: Optional[str] = None
    reason: Optional[str] = None
    reported_at: datetime


class AdminReportedUsersResponse(BaseModel):
    reported_users: List[AdminReportedUser]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_previous: bool
