from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserStatusResponse(BaseModel):
    user_id: int
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None


class UpdateStatusRequest(BaseModel):
    is_online: Optional[bool] = None
    is_busy: Optional[bool] = None
    wait_time: Optional[int] = None


class UserPresenceResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None


