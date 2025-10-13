from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserStatusResponse(BaseModel):
    user_id: int
    is_online: bool
    last_seen: datetime
    is_busy: bool
    wait_time: Optional[int] = None


# UpdateStatusRequest removed (no longer used)


# Presence schema removed as presence APIs are no longer exposed


