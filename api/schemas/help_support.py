from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class IssueTypeEnum(str, Enum):
    call_session_support = "call_session_support"
    payment_support = "payment_support"
    other = "other"


class SupportStatusEnum(str, Enum):
    active = "active"
    resolved = "resolved"


class CreateSupportTicketRequest(BaseModel):
    issue_type: IssueTypeEnum = Field(..., description="Type of support issue")
    issue: str = Field(..., min_length=1, max_length=500, description="Brief description of the issue")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description of the issue")
    image_s3_urls: Optional[List[str]] = Field(default=[], description="List of S3 URLs for support images")
    require_call: bool = Field(default=False, description="Whether the user requires a call for support")
    call_id: Optional[int] = Field(None, description="Call ID (required for call_session_support)")
    transaction_id: Optional[int] = Field(None, description="Transaction ID (required for payment_support)")


class SupportTicketResponse(BaseModel):
    support_id: int
    user_id: int
    issue_type: IssueTypeEnum
    issue: str
    description: Optional[str] = None
    image_s3_urls: List[str] = []
    require_call: bool
    call_id: Optional[int] = None
    transaction_id: Optional[int] = None
    status: SupportStatusEnum
    admin_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportTicketListResponse(BaseModel):
    tickets: List[SupportTicketResponse]
    total_count: int
    page: int
    page_size: int


class AdminSupportTicketResponse(BaseModel):
    support_id: int
    user_id: int
    username: Optional[str] = None
    phone: Optional[str] = None
    issue_type: IssueTypeEnum
    issue: str
    description: Optional[str] = None
    image_s3_urls: List[str] = []
    require_call: bool
    call_id: Optional[int] = None
    transaction_id: Optional[int] = None
    status: SupportStatusEnum
    admin_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminSupportTicketListResponse(BaseModel):
    tickets: List[AdminSupportTicketResponse]
    total_count: int
    page: int
    page_size: int
