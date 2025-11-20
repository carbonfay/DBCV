"""Bot schemas for MCP DBCV Server."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class BotInfo(BaseModel):
    """Bot information schema aligned with backend response."""
    
    id: str = Field(..., description="Bot ID")
    name: str = Field(..., description="Bot name")
    description: Optional[str] = Field(None, description="Bot description")
    config: Optional[Any] = Field(None, description="Bot configuration")
    owner_id: Optional[str] = Field(None, description="Bot owner ID")
    first_step_id: Optional[str] = Field(None, description="First step ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    is_active: Optional[bool] = Field(True, description="Bot active status")


class BotCreate(BaseModel):
    """Bot creation schema."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Bot name")
    description: Optional[str] = Field(None, max_length=500, description="Bot description")
    config: Optional[Any] = Field(None, description="Bot configuration")


class BotUpdate(BaseModel):
    """Bot update schema."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Bot name")
    description: Optional[str] = Field(None, max_length=500, description="Bot description")
    config: Optional[Any] = Field(None, description="Bot configuration")
    first_step_id: Optional[str] = Field(None, description="First step ID")
    is_active: Optional[bool] = Field(None, description="Bot active status")
