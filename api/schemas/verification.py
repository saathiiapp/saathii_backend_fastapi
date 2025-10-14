from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VerificationStatusResponse(BaseModel):
    verification_status: bool  # true = verified, false = not verified
    verification_message: Optional[str] = None
    verified_on: Optional[datetime] = None
