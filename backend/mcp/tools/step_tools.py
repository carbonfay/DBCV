"""Step tools for MCP DBCV Server."""

import logging
from typing import Dict, Any, List

from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

from client import DBCVAPIClient
from schemas import StepCreate, StepUpdate
from .common import DEFAULT_ALLOWED_ROLES, ensure_authorized_roles

logger = logging.getLogger(__name__)


class StepTools:
    """Step management tools for MCP DBCV Server."""
    
    def __init__(self, client: DBCVAPIClient):
        self.client = client
    
    def get_tools(self) -> List[Tool]:
        """Get list of step tools."""
        return [
            Tool(
                name="create_step",
                description="Create a new step for a bot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "bot_id": {
                            "type": "string",
                            "description": "Bot ID to create step for"
                        },
                        "name": {
                            "type": "string",
                            "description": "Step name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Step description"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message to send to user"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Step timeout in seconds",
                            "default": 30
                        },
                        "timeout_after": {
                            "type": "integer",
                            "description": "Alias for timeout (seconds)"
                        },
                        "is_proxy": {
                            "type": "boolean",
                            "description": "Whether step continues automatically (true) or waits for user input (false)",
                            "default": False
                        },
                        "pos_x": {
                            "type": "number",
                            "description": "Canvas X position",
                            "default": 0
                        },
                        "pos_y": {
                            "type": "number",
                            "description": "Canvas Y position",
                            "default": 0
                        }
                    },
                    "required": ["bot_id", "name"]
                }
            ),
            Tool(
                name="update_step",
                description="Update an existing step",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "step_id": {
                            "type": "string",
                            "description": "Step ID to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New step name"
                        },
                        "description": {
                            "type": "string",
                            "description": "New step description"
                        },
                        "message": {
                            "type": "string",
                            "description": "New message to send to user"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "New step timeout in seconds"
                        },
                        "timeout_after": {
                            "type": "integer",
                            "description": "Alias for timeout in seconds"
                        },
                        "is_proxy": {
                            "type": "boolean",
                            "description": "New is_proxy value"
                        },
                        "pos_x": {
                            "type": "number",
                            "description": "New canvas X position"
                        },
                        "pos_y": {
                            "type": "number",
                            "description": "New canvas Y position"
                        }
                    },
                    "required": ["step_id"]
                }
            ),
            Tool(
                name="get_step_info",
                description="Get information about a specific step",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "step_id": {
                            "type": "string",
                            "description": "Step ID to get information for"
                        }
                    },
                    "required": ["step_id"]
                }
            ),
            Tool(
                name="delete_step",
                description="Delete a step",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "step_id": {
                            "type": "string",
                            "description": "Step ID to delete"
                        }
                    },
                    "required": ["step_id"]
                }
            )
        ]
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle step tool calls."""
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
            
            if request.name == "create_step":
                return await self._create_step(request.arguments)
            elif request.name == "update_step":
                return await self._update_step(request.arguments)
            elif request.name == "get_step_info":
                return await self._get_step_info(request.arguments)
            elif request.name == "delete_step":
                return await self._delete_step(request.arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )
                
        except Exception as e:
            logger.error(f"Error in step tool {request.name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    async def _create_step(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Create a new step."""
        timeout_after = arguments.get("timeout_after", arguments.get("timeout"))
        step_data = StepCreate(
            bot_id=arguments["bot_id"],
            name=arguments["name"],
            is_proxy=arguments.get("is_proxy", False),
            description=arguments.get("description"),
            timeout_after=timeout_after,
            pos_x=arguments.get("pos_x", 0.0),
            pos_y=arguments.get("pos_y", 0.0)        )
        
        step = await self.client.create_step(step_data)
        message_response = await self.client.create_step_message(step.id, arguments.get("message"))
        
        result = {
            "success": True,
            "step": {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "bot_id": step.bot_id,
                "is_proxy": step.is_proxy,
                "timeout_after": step.timeout_after,
                "pos_x": step.pos_x,
                "pos_y": step.pos_y,
                "created_at": step.created_at,
                "message_created": bool(message_response),
            }
        }
        
        if message_response:
            result["message"] = {
                "id": message_response.get("id"),
                "text": message_response.get("text"),
            }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Step created successfully: {result}")]
        )
    
    async def _update_step(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Update an existing step."""
        step_id = arguments["step_id"]
        timeout_after = arguments.get("timeout_after", arguments.get("timeout"))
        step_data = StepUpdate(
            name=arguments.get("name"),
            description=arguments.get("description"),
            is_proxy=arguments.get("is_proxy"),
            timeout_after=timeout_after,
            pos_x=arguments.get("pos_x"),
            pos_y=arguments.get("pos_y")        )
        
        step = await self.client.update_step(step_id, step_data)
        message_response = None
        if "message" in arguments:
            message_response = await self.client.create_step_message(step.id, arguments.get("message"))
        
        result = {
            "success": True,
            "step": {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "bot_id": step.bot_id,
                "is_proxy": step.is_proxy,
                "timeout_after": step.timeout_after,
                "pos_x": step.pos_x,
                "pos_y": step.pos_y,
                "updated_at": step.updated_at
            }
        }
        
        if message_response:
            result["message"] = {
                "id": message_response.get("id"),
                "text": message_response.get("text"),
            }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Step updated successfully: {result}")]
        )
    
    async def _get_step_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get step information."""
        step_id = arguments["step_id"]
        step = await self.client.get_step(step_id)
        
        result = {
            "success": True,
            "step": {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "bot_id": step.bot_id,
                "is_proxy": step.is_proxy,
                "timeout_after": step.timeout_after,
                "pos_x": step.pos_x,
                "pos_y": step.pos_y,
                "created_at": step.created_at,
                "updated_at": step.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Step information retrieved successfully: {result}")]
        )
    
    async def _delete_step(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Delete a step."""
        step_id = arguments["step_id"]
        result = await self.client.delete_step(step_id)
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Step deleted successfully: {result}")]
        )
