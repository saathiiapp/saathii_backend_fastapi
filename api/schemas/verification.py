from pydantic import BaseModel, HttpUrl
from typing import Optional


class VerifyAudioRequest(BaseModel):
    audio_file_url: HttpUrl


class VerifyAudioResponse(BaseModel):
    verified: bool
    reason: Optional[str] = None


