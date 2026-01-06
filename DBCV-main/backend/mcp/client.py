"""DBCV API Client for MCP Server."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

import httpx
from httpx import AsyncClient, HTTPError

from config import config
from schemas import (
    BotInfo, BotCreate, BotUpdate,
    StepInfo, StepCreate, StepUpdate,
    RequestInfo, RequestCreate, RequestUpdate,
    ConnectionGroupInfo, ConnectionGroupCreate, ConnectionGroupUpdate
)

logger = logging.getLogger(__name__)


def _mask_token(token: Optional[str]) -> str:
    """Return redacted token for logging."""
    if not token:
        return "<none>"
    if len(token) <= 10:
        return f"{token[:3]}***"
    return f"{token[:6]}...{token[-4:]}"


class DBCVAPIClient:
    """Client for DBCV Backend API."""
    
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.base_url = config.backend_api_url
        self.timeout = 30.0
        
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to DBCV API."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        async with AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                logger.info(
                    "[API] %s %s params=%s payload_keys=%s token=%s",
                    method,
                    endpoint,
                    params or {},
                    list(data.keys()) if isinstance(data, dict) else None,
                    _mask_token(self.auth_token),
                )
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                logger.info(
                    "[API] %s %s -> %s",
                    method,
                    endpoint,
                    response.status_code,
                )
                return response.json()
                
            except HTTPError as e:
                logger.error(f"API request failed: {method} {url} - {e}")
                raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                raise Exception(f"Unexpected error: {str(e)}")
    
    # Bot operations
    async def get_bot(self, bot_id: str) -> BotInfo:
        """Get bot information."""
        data = await self._request("GET", f"/bots/{bot_id}")
        return BotInfo(**data)
    
    async def create_bot(self, bot_data: BotCreate) -> BotInfo:
        """Create a new bot."""
        data = await self._request("POST", "/bots", data=bot_data.model_dump(exclude_none=True))
        return BotInfo(**data)
    
    async def update_bot(self, bot_id: str, bot_data: BotUpdate) -> BotInfo:
        """Update bot."""
        data = await self._request(
            "PATCH",
            f"/bots/{bot_id}",
            data=bot_data.model_dump(exclude_unset=True, exclude_none=True),
        )
        return BotInfo(**data)
    
    async def list_bots(self, skip: int = 0, limit: int = 100) -> List[BotInfo]:
        """List user's bots."""
        data = await self._request("GET", "/bots", params={"skip": skip, "limit": limit})
        return [BotInfo(**bot) for bot in data]
    
    # Step operations
    async def create_step(self, step_data: StepCreate) -> StepInfo:
        """Create a new step."""
        data = await self._request("POST", "/steps", data=step_data.model_dump(exclude_none=True))
        return StepInfo(**data)
    
    async def update_step(self, step_id: str, step_data: StepUpdate) -> StepInfo:
        """Update step."""
        data = await self._request(
            "PATCH",
            f"/steps/{step_id}",
            data=step_data.model_dump(exclude_unset=True, exclude_none=True),
        )
        return StepInfo(**data)
    
    async def get_step(self, step_id: str) -> StepInfo:
        """Get step information."""
        data = await self._request("GET", f"/steps/{step_id}")
        return StepInfo(**data)
    
    async def delete_step(self, step_id: str) -> Dict[str, str]:
        """Delete step."""
        return await self._request("DELETE", f"/steps/{step_id}")
    
    async def create_step_message(self, step_id: str, text: Optional[str]) -> Optional[Dict[str, Any]]:
        """Attach a message to a step if text is provided."""
        if not text:
            return None
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
        }
        form_data = {
            "text": text,
            "step_id": step_id,
        }
        async with AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.post(url, headers=headers, data=form_data)
                response.raise_for_status()
                return response.json()
            except HTTPError as e:
                logger.error("Failed to create message for step %s: %s", step_id, e)
                return None
    
    # Request operations
    async def create_request(self, request_data: RequestCreate) -> RequestInfo:
        """Create a new HTTP request."""
        data = await self._request("POST", "/requests", data=request_data.model_dump(exclude_none=True))
        return RequestInfo(**data)
    
    async def update_request(self, request_id: str, request_data: RequestUpdate) -> RequestInfo:
        """Update HTTP request."""
        data = await self._request(
            "PATCH",
            f"/requests/{request_id}",
            data=request_data.model_dump(exclude_unset=True, exclude_none=True),
        )
        return RequestInfo(**data)
    
    async def get_request(self, request_id: str) -> RequestInfo:
        """Get HTTP request information."""
        data = await self._request("GET", f"/requests/{request_id}")
        return RequestInfo(**data)
    
    async def delete_request(self, request_id: str) -> Dict[str, str]:
        """Delete HTTP request."""
        return await self._request("DELETE", f"/requests/{request_id}")
    
    # Connection group operations
    async def create_connection_group(self, connection_data: ConnectionGroupCreate) -> ConnectionGroupInfo:
        """Create a new connection group."""
        data = await self._request("POST", "/connection_groups/", data=connection_data.model_dump(exclude_none=True))
        return ConnectionGroupInfo(**data)
    
    async def update_connection_group(self, connection_group_id: str, connection_data: ConnectionGroupUpdate) -> ConnectionGroupInfo:
        """Update connection group."""
        data = await self._request(
            "PATCH",
            f"/connection_groups/{connection_group_id}",
            data=connection_data.model_dump(exclude_unset=True, exclude_none=True),
        )
        return ConnectionGroupInfo(**data)
    
    async def get_connection_group(self, connection_group_id: str) -> ConnectionGroupInfo:
        """Get connection group information."""
        data = await self._request("GET", f"/connection_groups/{connection_group_id}")
        return ConnectionGroupInfo(**data)
    
    async def delete_connection_group(self, connection_group_id: str) -> Dict[str, str]:
        """Delete connection group."""
        return await self._request("DELETE", f"/connection_groups/{connection_group_id}")
    
    # Utility methods
    async def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        try:
            return await self._request("GET", "/health")
        except Exception:
            return {"status": "unhealthy"}
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        return await self._request("GET", "/users/me")
