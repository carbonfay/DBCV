"""Bot tools for MCP DBCV Server."""

import logging
from typing import Dict, Any, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult
)

from client import DBCVAPIClient
from schemas import BotInfo, BotCreate, BotUpdate
from .common import DEFAULT_ALLOWED_ROLES, ensure_authorized_roles

logger = logging.getLogger(__name__)


class BotTools:
    """Bot management tools for MCP DBCV Server."""
    
    def __init__(self, client: DBCVAPIClient):
        self.client = client
    
    def get_tools(self) -> List[Tool]:
        """Get list of bot tools."""
        return [
            Tool(
                name="get_bot_info",
                description="Get information about a specific bot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "bot_id": {
                            "type": "string",
                            "description": "Bot ID to get information for"
                        }
                    },
                    "required": ["bot_id"]
                }
            ),
            Tool(
                name="list_bots",
                description="List all bots accessible to the user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "skip": {
                            "type": "integer",
                            "description": "Number of bots to skip",
                            "default": 0
                        },
                        "limit": {
                            "type": "integer", 
                            "description": "Maximum number of bots to return",
                            "default": 100
                        }
                    }
                }
            ),
            Tool(
                name="create_bot",
                description="Create a new bot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Bot name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Bot description"
                        },
                        "config": {
                            "type": "object",
                            "description": "Bot configuration (JSON object)"
                        },
                        "variables": {
                            "type": "object",
                            "description": "Legacy field for configuration (JSON object)"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="update_bot",
                description="Update an existing bot",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "bot_id": {
                            "type": "string",
                            "description": "Bot ID to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New bot name"
                        },
                        "description": {
                            "type": "string",
                            "description": "New bot description"
                        },
                        "config": {
                            "type": "object",
                            "description": "New bot configuration (JSON object)"
                        },
                        "variables": {
                            "type": "object",
                            "description": "Legacy field for configuration (JSON object)"
                        },
                        "is_active": {
                            "type": "boolean",
                            "description": "Bot active status"
                        }
                    },
                    "required": ["bot_id"]
                }
            )
        ]
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle bot tool calls."""
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
            
            if request.name == "get_bot_info":
                return await self._get_bot_info(request.arguments)
            elif request.name == "list_bots":
                return await self._list_bots(request.arguments)
            elif request.name == "create_bot":
                return await self._create_bot(request.arguments)
            elif request.name == "update_bot":
                return await self._update_bot(request.arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )
                
        except Exception as e:
            logger.error(f"Error in bot tool {request.name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    async def _get_bot_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get bot information."""
        bot_id = arguments["bot_id"]
        bot = await self.client.get_bot(bot_id)
        
        result = {
            "success": True,
            "bot": {
                "id": bot.id,
                "name": bot.name,
                "description": bot.description,
                "config": bot.config,
                "owner_id": bot.owner_id,
                "first_step_id": bot.first_step_id,
                "is_active": bot.is_active,
                "created_at": bot.created_at,
                "updated_at": bot.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Bot information retrieved successfully: {result}")]
        )
    
    async def _list_bots(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List user's bots."""
        skip = arguments.get("skip", 0)
        limit = arguments.get("limit", 100)
        
        bots = await self.client.list_bots(skip=skip, limit=limit)
        
        result = {
            "success": True,
            "bots": [
                {
                    "id": bot.id,
                    "name": bot.name,
                    "description": bot.description,
                    "config": bot.config,
                    "first_step_id": bot.first_step_id,
                    "is_active": bot.is_active,
                    "created_at": bot.created_at,
                    "updated_at": bot.updated_at,
                }
                for bot in bots
            ],
            "total": len(bots)
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Bots listed successfully: {result}")]
        )
    
    async def _create_bot(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Create a new bot."""
        config = arguments.get("config")
        if config is None:
            config = arguments.get("variables")
        bot_data = BotCreate(
            name=arguments["name"],
            description=arguments.get("description"),
            config=config,
        )
        
        bot = await self.client.create_bot(bot_data)
        
        result = {
            "success": True,
            "bot": {
                "id": bot.id,
                "name": bot.name,
                "description": bot.description,
                "config": bot.config,
                "is_active": bot.is_active,
                "created_at": bot.created_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Bot created successfully: {result}")]
        )
    
    async def _update_bot(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Update an existing bot."""
        bot_id = arguments["bot_id"]
        config = arguments.get("config")
        if config is None and "variables" in arguments:
            config = arguments.get("variables")
        bot_data = BotUpdate(
            name=arguments.get("name"),
            description=arguments.get("description"),
            config=config,
            is_active=arguments.get("is_active")
        )
        
        bot = await self.client.update_bot(bot_id, bot_data)
        
        result = {
            "success": True,
            "bot": {
                "id": bot.id,
                "name": bot.name,
                "description": bot.description,
                "config": bot.config,
                "is_active": bot.is_active,
                "updated_at": bot.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Bot updated successfully: {result}")]
        )
