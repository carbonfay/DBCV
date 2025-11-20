"""Connection tools for MCP DBCV Server."""

import logging
from typing import Dict, Any, List

from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

from client import DBCVAPIClient
from schemas import ConnectionGroupCreate, ConnectionGroupUpdate, ConnectionCreate, ConnectionUpdate
from .common import DEFAULT_ALLOWED_ROLES, ensure_authorized_roles

logger = logging.getLogger(__name__)


def _maybe_parse_json(value: Any) -> Any:
    """Parse JSON strings into Python objects when possible."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            import json
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _stringify_json(value: Any) -> Any:
    """Ensure value is serialized as JSON string when backend expects a string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        import json
        return json.dumps(value)
    except Exception:
        return str(value)


def _normalize_identifier(value: Any) -> Any:
    """Convert blank identifiers to None and strip whitespace."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def _stringify_optional_json(value: Any) -> Any:
    """Return JSON string representation for optional inputs, keeping raw strings."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        import json
        return json.dumps(value)
    except Exception:
        return str(value)


class ConnectionTools:
    """Connection management tools for MCP DBCV Server."""
    
    def __init__(self, client: DBCVAPIClient):
        self.client = client
    
    def get_tools(self) -> List[Tool]:
        """Get list of connection tools."""
        return [
            Tool(
                name="create_connection_group",
                description="Create a new connection group to link steps, requests, or bot routing",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "bot_id": {
                            "type": "string",
                            "description": "Bot ID (for master connections - bot-level routing)"
                        },
                        "step_id": {
                            "type": "string",
                            "description": "Step ID (for step connections - step-level routing)"
                        },
                        "request_id": {
                            "type": "string",
                            "description": "Request ID (for HTTP connections - request response handling)"
                        },
                        "search_type": {
                            "type": "string",
                            "description": "Connection group type: 'message', 'response', or 'code'",
                            "enum": ["message", "response", "code"],
                            "default": "message"
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Connection group priority",
                            "default": 0
                        },
                        "code": {
                            "type": "string",
                            "description": "Connection group code executed during evaluation"
                        },
                        "variables": {
                            "type": "string",
                            "description": "Variables mapping as JSON string (e.g., '{\"response.data\": \"session.data\"}')"
                        },
                        "connections": {
                            "type": "array",
                            "description": "List of connections in this group",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "next_step_id": {
                                        "type": "string",
                                        "description": "Target step ID to connect to"
                                    },
                                    "priority": {
                                        "type": "integer",
                                        "description": "Connection priority",
                                        "default": 0
                                    },
                                    "rules": {
                                        "type": "string",
                                        "description": "Connection rules as JSON"
                                    },
                                    "filters": {
                                        "type": "string",
                                        "description": "Connection filters as JSON"
                                    }
                                },
                                "required": ["next_step_id"]
                            }
                        }
                    },
                    "note": "Specify either bot_id OR step_id OR request_id, but not multiple at once"
                }
            ),
            Tool(
                name="update_connection_group",
                description="Update an existing connection group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection_group_id": {
                            "type": "string",
                            "description": "Connection group ID to update"
                        },
                        "bot_id": {
                            "type": "string",
                            "description": "New bot ID"
                        },
                        "step_id": {
                            "type": "string",
                            "description": "New step ID"
                        },
                        "request_id": {
                            "type": "string",
                            "description": "New request ID"
                        },
                        "search_type": {
                            "type": "string",
                            "description": "New connection group type",
                            "enum": ["message", "response", "code"]
                        },
                        "priority": {
                            "type": "integer",
                            "description": "New connection group priority"
                        },
                        "code": {
                            "type": "string",
                            "description": "New connection group code"
                        },
                        "variables": {
                            "type": "string",
                            "description": "New variables mapping as JSON string"
                        },
                        "connections": {
                            "type": "array",
                            "description": "New list of connections",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "next_step_id": {
                                        "type": "string",
                                        "description": "Target step ID"
                                    },
                                    "priority": {
                                        "type": "integer",
                                        "description": "Connection priority"
                                    },
                                    "rules": {
                                        "type": "string",
                                        "description": "Connection rules as JSON"
                                    },
                                    "filters": {
                                        "type": "string",
                                        "description": "Connection filters as JSON"
                                    },
                                    "id": {
                                        "type": "string",
                                        "description": "Existing connection ID (for updates)"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["connection_group_id"]
                }
            ),
            Tool(
                name="get_connection_group_info",
                description="Get information about a specific connection group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection_group_id": {
                            "type": "string",
                            "description": "Connection group ID to get information for"
                        }
                    },
                    "required": ["connection_group_id"]
                }
            ),
            Tool(
                name="delete_connection_group",
                description="Delete a connection group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection_group_id": {
                            "type": "string",
                            "description": "Connection group ID to delete"
                        }
                    },
                    "required": ["connection_group_id"]
                }
            )
        ]
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle connection tool calls."""
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
            
            if request.name == "create_connection_group":
                return await self._create_connection_group(request.arguments)
            elif request.name == "update_connection_group":
                return await self._update_connection_group(request.arguments)
            elif request.name == "get_connection_group_info":
                return await self._get_connection_group_info(request.arguments)
            elif request.name == "delete_connection_group":
                return await self._delete_connection_group(request.arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )
                
        except Exception as e:
            logger.error(f"Error in connection tool {request.name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    async def _create_connection_group(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Create a new connection group."""
        # Validate identifier constraints
        bot_id = _normalize_identifier(arguments.get("bot_id"))
        step_id = _normalize_identifier(arguments.get("step_id"))
        request_id = _normalize_identifier(arguments.get("request_id"))
        search_type = (arguments.get("search_type") or "message").lower()

        if not step_id and not bot_id:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Provide either step_id or bot_id.")]
            )
        if step_id and bot_id:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: step_id and bot_id are mutually exclusive.")]
            )

        if search_type == "response" and not request_id:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: request_id is required when search_type is 'response'.")]
            )
        
        # Parse connections
        connections_data = []
        for conn in arguments.get("connections", []):
            next_step_id = _normalize_identifier(conn.get("next_step_id"))
            if not next_step_id:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: Each connection requires 'next_step_id'.")]
                )
            connections_data.append(ConnectionCreate(
                next_step_id=next_step_id,
                priority=conn.get("priority", 0),
                rules=_stringify_optional_json(conn.get("rules")),
                filters=_stringify_optional_json(conn.get("filters")),
            ))
        
        connection_data = ConnectionGroupCreate(
            bot_id=bot_id,
            step_id=step_id,
            request_id=request_id,
            search_type=search_type,
            priority=arguments.get("priority", 0),
            code=arguments.get("code"),
            variables=_stringify_json(arguments.get("variables")),
            connections=connections_data
        )
        
        connection_group = await self.client.create_connection_group(connection_data)
        
        result = {
            "success": True,
            "connection_group": {
                "id": connection_group.id,
                "search_type": connection_group.search_type,
                "priority": connection_group.priority,
                "code": connection_group.code,
                "variables": connection_group.variables,
                "bot_id": connection_group.bot_id or bot_id,
                "step_id": connection_group.step_id or step_id,
                "request_id": connection_group.request_id or request_id,
                "connections": [
                    {
                        "id": conn.id,
                        "next_step_id": conn.next_step_id,
                        "priority": conn.priority,
                        "rules": conn.rules,
                        "filters": conn.filters,
                    }
                    for conn in connection_group.connections
                ],
                "created_at": connection_group.created_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Connection group created successfully: {result}")]
        )
    
    async def _update_connection_group(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Update an existing connection group."""
        connection_group_id = arguments["connection_group_id"]
        
        # Parse connections if provided
        connections_data = None
        if "connections" in arguments:
            connections_data = []
            for conn in arguments["connections"]:
                update_payload = ConnectionUpdate(
                    id=conn.get("id"),
                    next_step_id=_normalize_identifier(conn.get("next_step_id")),
                    priority=conn.get("priority"),
                    rules=_stringify_optional_json(conn.get("rules")),
                    filters=_stringify_optional_json(conn.get("filters")),
                )
                connections_data.append(update_payload)
        
        bot_id = _normalize_identifier(arguments.get("bot_id"))
        step_id = _normalize_identifier(arguments.get("step_id"))
        request_id = _normalize_identifier(arguments.get("request_id"))

        connection_data = ConnectionGroupUpdate(
            bot_id=bot_id,
            step_id=step_id,
            request_id=request_id,
            search_type=arguments.get("search_type"),
            priority=arguments.get("priority"),
            code=arguments.get("code"),
            variables=_stringify_json(arguments.get("variables")),
            connections=connections_data
        )
        
        connection_group = await self.client.update_connection_group(connection_group_id, connection_data)
        
        result = {
            "success": True,
            "connection_group": {
                "id": connection_group.id,
                "search_type": connection_group.search_type,
                "priority": connection_group.priority,
                "code": connection_group.code,
                "variables": connection_group.variables,
                "bot_id": connection_group.bot_id or bot_id,
                "step_id": connection_group.step_id or step_id,
                "request_id": connection_group.request_id or request_id,
                "connections": [
                    {
                        "id": conn.id,
                        "next_step_id": conn.next_step_id,
                        "priority": conn.priority,
                        "rules": conn.rules,
                        "filters": conn.filters,
                    }
                    for conn in connection_group.connections
                ],
                "updated_at": connection_group.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Connection group updated successfully: {result}")]
        )
    
    async def _get_connection_group_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get connection group information."""
        connection_group_id = arguments["connection_group_id"]
        connection_group = await self.client.get_connection_group(connection_group_id)
        
        result = {
            "success": True,
            "connection_group": {
                "id": connection_group.id,
                "search_type": connection_group.search_type,
                "priority": connection_group.priority,
                "code": connection_group.code,
                "variables": connection_group.variables,
                "bot_id": connection_group.bot_id,
                "step_id": connection_group.step_id,
                "request_id": connection_group.request_id,
                "connections": [
                    {
                        "id": conn.id,
                        "next_step_id": conn.next_step_id,
                        "priority": conn.priority,
                        "rules": conn.rules,
                        "filters": conn.filters,
                        "created_at": conn.created_at,
                        "updated_at": conn.updated_at
                    }
                    for conn in connection_group.connections
                ],
                "created_at": connection_group.created_at,
                "updated_at": connection_group.updated_at
            }
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Connection group information retrieved successfully: {result}")]
        )
    
    async def _delete_connection_group(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Delete a connection group."""
        connection_group_id = arguments["connection_group_id"]
        result = await self.client.delete_connection_group(connection_group_id)
        
        return CallToolResult(
            content=[TextContent(type="text", text=f"Connection group deleted successfully: {result}")]
        )
