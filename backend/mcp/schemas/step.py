"""Step schemas for MCP DBCV Server."""

from typing import Optional
from pydantic import BaseModel, Field


class StepInfo(BaseModel):
    """Step information schema aligned with backend response."""
    
    id: str = Field(..., description="Step ID")
    name: str = Field(..., description="Step name")
    description: Optional[str] = Field(None, description="Step description")
    bot_id: str = Field(..., description="Bot ID")
    is_proxy: bool = Field(False, description="Whether step continues automatically")
    timeout_after: Optional[int] = Field(None, ge=1, le=300, description="Step timeout in seconds")
    pos_x: float = Field(0, description="Canvas X position")
    pos_y: float = Field(0, description="Canvas Y position")
    ## template_instance_id: Optional[str] = Field(None, description="Template instance ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class StepCreate(BaseModel):
    """Step creation schema."""
    
    bot_id: str = Field(..., description="Bot ID")
    name: str = Field(..., min_length=1, max_length=100, description="Step name")
    is_proxy: bool = Field(False, description="Whether step continues automatically")
    description: Optional[str] = Field(None, max_length=500, description="Step description")
    timeout_after: Optional[int] = Field(None, ge=1, le=300, description="Step timeout in seconds")
    pos_x: float = Field(0, description="Canvas X position")
    pos_y: float = Field(0, description="Canvas Y position")
    template_instance_id: Optional[str] = Field(None, description="Template instance ID")


class StepUpdate(BaseModel):
    """Step update schema."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Step name")
    description: Optional[str] = Field(None, max_length=500, description="Step description")
    timeout_after: Optional[int] = Field(None, ge=1, le=300, description="Step timeout in seconds")
    is_proxy: Optional[bool] = Field(None, description="Whether step continues automatically")
    pos_x: Optional[float] = Field(None, description="Canvas X position")
    pos_y: Optional[float] = Field(None, description="Canvas Y position")
    template_instance_id: Optional[str] = Field(None, description="Template instance ID")
