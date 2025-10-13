from fastapi import APIRouter, Depends, HTTPException
from api.schemas.verification import VerifyAudioRequest, VerifyAudioResponse
from api.routes.auth import get_current_user


router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/listener/verification/verify-audio", response_model=VerifyAudioResponse)
async def verify_audio(payload: VerifyAudioRequest, user: dict = Depends(get_current_user)):
    # Quick validation: ensure URL looks like an S3 object and is audio
    url = str(payload.audio_file_url)
    if "s3." not in url and "amazonaws.com" not in url:
        raise HTTPException(status_code=400, detail="URL must be an S3 object URL")
    # Basic extension check
    allowed_ext = (".mp3", ".wav", ".m4a", ".ogg")
    if not any(url.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail="Audio file must be one of: mp3, wav, m4a, ogg")

    # Minimal, fast "verification": accept as verified for now
    # (placeholder for future real-time/live voice verification)
    return VerifyAudioResponse(verified=True, reason="basic_checks_passed")


