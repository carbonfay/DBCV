from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class AccessToken(BaseModel):
    token_type: str = Field(default="Bearer")
    access_token: str
    expires_at: Optional[float] = None