from pydantic import BaseModel
from typing import List, Optional


class ListenerPreferencesResponse(BaseModel):
    listener_id: int
    listener_allowed_call_type: List[str]
    listener_audio_call_enable: bool
    listener_video_call_enable: bool


class UpdateListenerPreferencesRequest(BaseModel):
    listener_audio_call_enable: Optional[bool] = None
    listener_video_call_enable: Optional[bool] = None
