"""Request schemas for MCP DBCV Server."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RequestInfo(BaseModel):
    """HTTP request information schema aligned with backend response."""
    
    id: str = Field(..., description="Request ID")
    name: str = Field(..., description="Request name")
    request_url: str = Field(..., description="Request URL")
    method: str = Field("get", description="HTTP method")
    params: Optional[Any] = Field(None, description="Request parameters")
    content: Optional[str] = Field(None, description="Raw request content")
    data: Optional[Any] = Field(None, description="Request payload data")
    json_field: Optional[Any] = Field(None, description="Request JSON field")
    headers: Optional[str] = Field(None, description="Request headers as JSON string")
    url_params: Optional[Any] = Field(None, description="URL parameters")
    attachments: Optional[str] = Field(None, description="Attachments definition")
    proxies: Optional[str] = Field(None, description="Proxy configuration")
    owner_id: Optional[str] = Field(None, description="Owner ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class RequestCreate(BaseModel):
    """HTTP request creation schema."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Request name")
    request_url: str = Field(..., description="Request URL")
    method: str = Field("get", description="HTTP method")
    params: Optional[Any] = Field(None, description="Request parameters")
    content: Optional[str] = Field(None, description="Raw request content")
    data: Optional[Any] = Field(None, description="Request payload data")
    json_field: Optional[Any] = Field(None, description="Request JSON field")
    headers: Optional[str] = Field(None, description="Request headers as JSON string")
    url_params: Optional[Any] = Field(None, description="URL parameters")
    attachments: Optional[str] = Field(None, description="Attachments definition")
    proxies: Optional[str] = Field(None, description="Proxy configuration")


class RequestUpdate(BaseModel):
    """HTTP request update schema."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Request name")
    request_url: Optional[str] = Field(None, description="Request URL")
    method: Optional[str] = Field(None, description="HTTP method")
    params: Optional[Any] = Field(None, description="Request parameters")
    content: Optional[str] = Field(None, description="Raw request content")
    data: Optional[Any] = Field(None, description="Request payload data")
    json_field: Optional[Any] = Field(None, description="Request JSON field")
    headers: Optional[str] = Field(None, description="Request headers as JSON string")
    url_params: Optional[Any] = Field(None, description="URL parameters")
    attachments: Optional[str] = Field(None, description="Attachments definition")
    proxies: Optional[str] = Field(None, description="Proxy configuration")
