from pydantic import BaseModel
from datetime import date, datetime


class BadgeCurrentResponse(BaseModel):
    listener_id: int
    username: str
    current_badge: str
    audio_rate_per_minute: int
    video_rate_per_minute: int
    assigned_date: date
    assigned_at: datetime


