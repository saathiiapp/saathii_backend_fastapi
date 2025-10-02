import jwt
import os
import uuid
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TTL_SECONDS = int(os.getenv("JWT_ACCESS_TTL", "1800"))  # 30m default
REFRESH_TTL_SECONDS = int(os.getenv("JWT_REFRESH_TTL", "2592000"))  # 30d default
REGISTRATION_TTL_SECONDS = int(os.getenv("JWT_REGISTRATION_TTL", "600"))  # 10m default


def _create_jwt(payload: dict, expires_delta_seconds: int):
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta_seconds)
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: dict):
    payload = {
        **subject,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return _create_jwt(payload, ACCESS_TTL_SECONDS)


def create_refresh_token(subject: dict):
    payload = {
        **subject,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return _create_jwt(payload, REFRESH_TTL_SECONDS)


def create_registration_token(subject: dict):
    payload = {
        **subject,
        "type": "registration",
        "jti": uuid.uuid4().hex,
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return _create_jwt(payload, REGISTRATION_TTL_SECONDS)


def decode_jwt(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
