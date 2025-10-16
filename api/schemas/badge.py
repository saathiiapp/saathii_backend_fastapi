from pydantic import BaseModel
from datetime import date, datetime


class BadgeCurrentResponse(BaseModel):
    listener_id: int
    current_badge: str
    audio_rate_per_minute: int
    video_rate_per_minute: int
    date: date
    assigned_at: datetime


