"""Request tools for MCP DBCV Server."""

import json
import logging
from typing import Dict, Any, List

from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

from client import DBCVAPIClient
from schemas import RequestCreate, RequestUpdate
from .common import DEFAULT_ALLOWED_ROLES, ensure_authorized_roles

logger = logging.getLogger(__name__)


def _stringify_payload(value: Any) -> Any:
    """Ensure complex payload values are stored as strings to match UI expectations."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return str(value)


class RequestTools:
    """HTTP request management tools for MCP DBCV Server."""
    
    def __init__(self, client: DBCVAPIClient):
        self.client = client
    
    def get_tools(self) -> List[Tool]:
        """Get list of request tools."""
        return [
            Tool(
                name="create_request",
                description="Create a new HTTP request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Request name"
                        },
                        "url": {
                            "type": "string",
                            "description": "Request URL"
                        },
                        "request_url": {
                            "type": "string",
                            "description": "Alias for request URL"
                        },
                        "method": {
                            "type": "string",
                            "description": "HTTP method (GET, POST, PUT, DELETE, etc.)",
                            "default": "GET"
                        },
                        "headers": {
                            "type": "string",
                            "description": "Request headers as JSON string (e.g., '{\"Content-Type\": \"application/json\"}')"
                        },
                        "params": {
                            "type": "string",
                            "description": "Request parameters as JSON string (e.g., '{\"param1\": \"value1\"}')"
                        },
                        "content": {
                            "type": "string",
                            "description": "Raw request content (will be stored as text)"
                        },
                        "data": {
                            "type": "string",
                            "description": "Request payload data as JSON string"
                        },
                        "json_field": {
                            "type": "string",
                            "description": "Request JSON field as JSON string"
                        },
                        "url_params": {
                            "type": "string",
                            "description": "URL parameters as JSON string"
                        },
                        "attachments": {
                            "type": "string",
                            "description": "Attachments definition"
                        },
                        "proxies": {
                            "type": "string",
                            "description": "Proxy configuration"
                        }
                    },
                    "required": ["name", "url"]
                }
            ),
            Tool(
                name="update_request",
                description="Update an existing HTTP request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "Request ID to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New request name"
                        },
                        "url": {
                            "type": "string",
                            "description": "New request URL"
                        },
                        "request_url": {
                            "type": "string",
                            "description": "Alias for new request URL"
                        },
                        "method": {
                            "type": "string",
                            "description": "New HTTP method"
                        },
                        "headers": {
                            "type": "string",
                            "description": "New request headers as JSON string"
                        },
                        "params": {
                            "type": "string",
                            "description": "New request parameters as JSON string"
                        },
                        "content": {
                            "type": "string",
                            "description": "New raw request content"
                        },
                        "data": {
                            "type": "string",
                            "description": "New request payload data as JSON string"
                        },
                        "json_field": {
                            "type": "string",
                            "description": "New request JSON field as JSON string"
                        },
                        "url_params": {
                            "type": "string",
                            "description": "New URL parameters as JSON string"
                        },
                        "attachments": {
                            "type": "string",
                            "description": "New attachments definition"
                        },
                        "proxies": {
                            "type": "string",
                            "description": "New proxy configuration"
                        }
                    },
                    "required": ["request_id"]
                }
            ),
            Tool(
                name="get_request_info",
                description="Get information about a specific HTTP request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "Request ID to get information for"
                        }
                    },
                    "required": ["request_id"]
                }
            ),
            Tool(
                name="delete_request",
                description="Delete an HTTP request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "Request ID to delete"
                        }
                    },
                    "required": ["request_id"]
                }
            )
        ]
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle request tool calls."""
        try:
            # Check if client is available
            if not self.client:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: No authentication token set")]
                )
            
            # Check user permissions
            auth_result = await ensure_authorized_roles(
                self.client,
                DEFAULT_ALLOWED_ROLES,
                logger,
                request.name,
            )
            if auth_result:
                return auth_result
            
            if request.name == "create_request":
                return await self._create_request(request.arguments)
            elif request.name == "update_request":
                return await self._update_request(request.arguments)
            elif request.name == "get_request_info":
                return await self._get_request_info(request.arguments)
            elif request.name == "delete_request":
                return await self._delete_request(request.arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )
                
        except Exception as e:
            logger.error(f"Error in request tool {request.name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    async def _create_request(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Create a new HTTP request."""
        request_url = arguments.get("request_url") or arguments.get("url")
        if not request_url:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Either 'url' or 'request_url' must be provided to create a request.")]
            )
        request_data = RequestCreate(
            name=arguments["name"],
            request_url=request_url,
            method=(arguments.get("method") or "get").lower(),
            headers=_stringify_payload(arguments.get("headers")),
            params=_stringify_payload(arguments.get("params")),
            content=arguments.get("content") or arguments.get("body"),
            data=_stringify_payload(arguments.get("data")),
            json_field=_stringify_payload(arguments.get("json_field")),
            url_params=_stringify_payload(arguments.get("url_params")),
            attachments=_stringify_payload(arguments.get("attachments")),
            proxies=_stringify_payload(arguments.get("proxies")),
        )
        
        request = await self.client.create_request(request_data)
        
        result = {
            "success": True,
            "request": {
                "id": request.id,
                "name": request.name,
                "request_url": request.request_url,
                "method": request.method,
                "headers": request.headers,
                "params": request.params,
                "content": request.content,
                "data": request.data,
                "json_field": request.json_field,
                "url_params": request.url_params,
                "attachments": request.attachments,
                "proxies": request.proxies,
                "created_at": request.created_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP request created successfully: {result}")]
        )
    
    async def _update_request(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Update an existing HTTP request."""
        request_id = arguments["request_id"]
        request_url = arguments.get("request_url") or arguments.get("url")
        request_data = RequestUpdate(
            name=arguments.get("name"),
            request_url=request_url,
            method=(arguments.get("method").lower() if arguments.get("method") else None),
            headers=_stringify_payload(arguments.get("headers")),
            params=_stringify_payload(arguments.get("params")),
            content=arguments.get("content") or arguments.get("body"),
            data=_stringify_payload(arguments.get("data")),
            json_field=_stringify_payload(arguments.get("json_field")),
            url_params=_stringify_payload(arguments.get("url_params")),
            attachments=_stringify_payload(arguments.get("attachments")),
            proxies=_stringify_payload(arguments.get("proxies")),
        )
        
        request = await self.client.update_request(request_id, request_data)
        
        result = {
            "success": True,
            "request": {
                "id": request.id,
                "name": request.name,
                "request_url": request.request_url,
                "method": request.method,
                "headers": request.headers,
                "params": request.params,
                "content": request.content,
                "data": request.data,
                "json_field": request.json_field,
                "url_params": request.url_params,
                "attachments": request.attachments,
                "proxies": request.proxies,
                "updated_at": request.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP request updated successfully: {result}")]
        )
    
    async def _get_request_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get HTTP request information."""
        request_id = arguments["request_id"]
        request = await self.client.get_request(request_id)
        
        result = {
            "success": True,
            "request": {
                "id": request.id,
                "name": request.name,
                "request_url": request.request_url,
                "method": request.method,
                "headers": request.headers,
                "params": request.params,
                "content": request.content,
                "data": request.data,
                "json_field": request.json_field,
                "url_params": request.url_params,
                "attachments": request.attachments,
                "proxies": request.proxies,
                "created_at": request.created_at,
                "updated_at": request.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP request information retrieved successfully: {result}")]
        )
    
    async def _delete_request(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Delete an HTTP request."""
        request_id = arguments["request_id"]
        result = await self.client.delete_request(request_id)
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"HTTP request deleted successfully: {result}")]
        )
