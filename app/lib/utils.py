import random
import string
from typing import Any, Dict
from fastapi import HTTPException
import jwt
from app.config import settings


def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def generate_token(length: int = 32) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_jwt_token(payload: Dict[str, Any], expires_in: int = 3600) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256", expires_in=expires_in)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    try: return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError: raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError: raise HTTPException(status_code=401, detail="Invalid token")
