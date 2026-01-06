import datetime as dt
from typing import Any

import bcrypt
import jwt

from app.config import settings


ACCESS_TOKEN_ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expiration_delta: dt.timedelta) -> str:
    expire = dt.datetime.now(dt.UTC).replace(tzinfo=None) + expiration_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=ACCESS_TOKEN_ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )
