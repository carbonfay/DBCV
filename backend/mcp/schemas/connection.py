
"""Connection schemas for MCP DBCV Server."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ConnectionInfo(BaseModel):
    """Connection information schema."""
    
    id: str = Field(..., description="Connection ID")
    next_step_id: str = Field(..., description="Next step ID")
    priority: int = Field(0, description="Connection priority")
    rules: Optional[Any] = Field(None, description="Connection rules")
    filters: Optional[Any] = Field(None, description="Connection filters")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class ConnectionGroupInfo(BaseModel):
    """Connection group information schema."""
    
    id: str = Field(..., description="Connection group ID")
    search_type: str = Field("message", description="Search type: message, response, code")
    priority: int = Field(0, description="Group priority")
    code: Optional[str] = Field(None, description="Group code")
    variables: Optional[str] = Field(None, description="Variables mapping as JSON string")
    bot_id: Optional[str] = Field(None, description="Bot ID (for master connections)")
    step_id: Optional[str] = Field(None, description="Step ID (for step connections)")
    request_id: Optional[str] = Field(None, description="Request ID (for HTTP connections)")
    connections: List[ConnectionInfo] = Field(default_factory=list, description="Connections in group")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class ConnectionCreate(BaseModel):
    """Connection creation schema."""
    
    next_step_id: str = Field(..., description="Next step ID")
    priority: int = Field(0, description="Connection priority")
    rules: Optional[Any] = Field(None, description="Connection rules")
    filters: Optional[Any] = Field(None, description="Connection filters")


class ConnectionGroupCreate(BaseModel):
    """Connection group creation schema."""
    
    search_type: str = Field("message", description="Search type for the group")
    priority: int = Field(0, description="Group priority")
    code: Optional[str] = Field(None, description="Group code")
    variables: Optional[str] = Field(None, description="Variables mapping as JSON string")
    bot_id: Optional[str] = Field(None, description="Bot ID (for master connections)")
    step_id: Optional[str] = Field(None, description="Step ID (for step connections)")
    request_id: Optional[str] = Field(None, description="Request ID (for HTTP connections)")
    connections: List[ConnectionCreate] = Field(default_factory=list, description="Connections to create")


class ConnectionUpdate(BaseModel):
    """Connection update schema."""
    
    id: Optional[str] = Field(None, description="Connection ID (for updates)")
    next_step_id: Optional[str] = Field(None, description="Next step ID")
    priority: Optional[int] = Field(None, description="Connection priority")
    rules: Optional[Any] = Field(None, description="Connection rules")
    filters: Optional[Any] = Field(None, description="Connection filters")


class ConnectionGroupUpdate(BaseModel):
    """Connection group update schema."""
    
    search_type: Optional[str] = Field(None, description="Search type for the group")
    priority: Optional[int] = Field(None, description="Group priority")
    code: Optional[str] = Field(None, description="Group code")
    variables: Optional[str] = Field(None, description="Variables mapping as JSON string")
    bot_id: Optional[str] = Field(None, description="Bot ID (for master connections)")
    step_id: Optional[str] = Field(None, description="Step ID (for step connections)")
    request_id: Optional[str] = Field(None, description="Request ID (for HTTP connections)")
    connections: Optional[List[ConnectionUpdate]] = Field(None, description="Connections to update")
