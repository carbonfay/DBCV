from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Timestamp(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
