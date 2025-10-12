"""
Badge management schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class BadgeInfo(BaseModel):
    listener_id: int
    date: date
    badge: str
    audio_rate_per_minute: float
    video_rate_per_minute: float
    assigned_at: datetime

class BadgeStats(BaseModel):
    badge: str
    count: int
    avg_audio_rate: float
    avg_video_rate: float

class BadgeStatisticsResponse(BaseModel):
    statistics: List[BadgeStats]
    total_listeners: int
    date_range: str

class ListenerBadgeResponse(BaseModel):
    current_badge: Optional[BadgeInfo]
    yesterday_duration_hours: float
    next_badge_threshold: Optional[float] = None

class BadgeAssignmentResponse(BaseModel):
    message: str
    date: date
    total_listeners: int
    basic_assigned: int
    bronze_assigned: int
    silver_assigned: int
    gold_assigned: int
    errors: int
