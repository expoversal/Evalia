# app/auth/jwt.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel

class Claims(BaseModel):
    sub: str            # user id
    email: str
    role: str
    # envelope this session is locked to, if any (see §2.4)
    envelope_scope: str | None = None
    exp: int

def issue(claims: Claims, secret: str) -> str:
    return jwt.encode(claims.model_dump(), secret, algorithm="HS256")

def verify(token: str, secret: str) -> Claims:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return Claims(**payload)
    except JWTError as e:
        raise AuthError("invalid token") from e
