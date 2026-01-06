"""MCP DBCV Server - Main server implementation."""

import asyncio
import json
import logging
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
)

from config import config
from client import DBCVAPIClient
from tools import BotTools, StepTools, RequestTools, ConnectionTools

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("dbcv-mcp-server")

_current_token: ContextVar[Optional[str]] = ContextVar("dbcv_mcp_token", default=None)
_current_client: ContextVar[Optional[DBCVAPIClient]] = ContextVar("dbcv_mcp_client", default=None)


def _mask_token(token: Optional[str]) -> str:
    """Return a redacted representation of a token for logging."""
    if not token:
        return "<none>"
    if len(token) <= 10:
        return f"{token[:3]}***"
    return f"{token[:6]}...{token[-4:]}"


class DBCVMCPServer:
    """Main MCP DBCV Server class."""

    def __init__(self):
        self.default_client: Optional[DBCVAPIClient] = None
        self.bot_tools: Optional[BotTools] = None
        self.step_tools: Optional[StepTools] = None
        self.request_tools: Optional[RequestTools] = None
        self.connection_tools: Optional[ConnectionTools] = None
        self.all_tools: List[Tool] = []
        self.client: Optional[DBCVAPIClient] = None

    def initialize(self, default_auth_token: Optional[str] = None):
        """Initialize the server with default authentication token."""
        try:
            config.validate()

            if default_auth_token:
                self.default_client = DBCVAPIClient(default_auth_token)
            else:
                self.default_client = None
            self.client = self.default_client

            self.bot_tools = BotTools(None)
            self.step_tools = StepTools(None)
            self.request_tools = RequestTools(None)
            self.connection_tools = ConnectionTools(None)

            self.all_tools = []
            self.all_tools.extend(self.bot_tools.get_tools())
            self.all_tools.extend(self.step_tools.get_tools())
            self.all_tools.extend(self.request_tools.get_tools())
            self.all_tools.extend(self.connection_tools.get_tools())

            logger.info("MCP DBCV Server initialized with %d tools", len(self.all_tools))
            logger.info("Backend URL: %s", config.backend_api_url)
            logger.info("MCP Server URL: %s", config.mcp_server_url)

        except Exception as exc:  # pragma: no cover
            logger.error("Failed to initialize MCP server: %s", exc)
            raise

    def set_auth_token(self, auth_token: str):
        """Set authentication token for current request."""
        client = DBCVAPIClient(auth_token)
        _current_token.set(auth_token)
        _current_client.set(client)

        logger.info("Authentication token set for MCP request: %s", _mask_token(auth_token))

    def clear_auth_token(self) -> None:
        """Reset authentication state after handling a request."""
        _current_token.set(None)
        _current_client.set(None)

    def _get_request_client(self) -> Optional[DBCVAPIClient]:
        client = _current_client.get()
        if client:
            return client
        return self.default_client

    async def handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list tools request."""
        return ListToolsResult(tools=self.all_tools)

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call request."""
        client = self._get_request_client()
        token = _current_token.get()
        try:
            if not client:
                possible_token = None
                try:
                    possible_token = (request.arguments or {}).get("auth_token")  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover
                    possible_token = None
                if possible_token:
                    self.set_auth_token(possible_token)
                    client = self._get_request_client()
                    token = possible_token

            if not client:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: No authentication token set")]
                )

            try:
                arg_keys = list((request.arguments or {}).keys())  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                arg_keys = ["<unavailable>"]

            logger.info(
                "Executing tool '%s' with args=%s (token=%s)",
                getattr(request, "name", "<unknown>"),
                arg_keys,
                _mask_token(token),
            )

            if request.name.startswith(("get_bot", "list_bot", "create_bot", "update_bot")):
                result = await BotTools(client).call_tool(request)
            elif request.name.startswith(("create_step", "update_step", "get_step", "delete_step")):
                result = await StepTools(client).call_tool(request)
            elif request.name.startswith(("create_request", "update_request", "get_request", "delete_request")):
                result = await RequestTools(client).call_tool(request)
            elif request.name.startswith(("create_connection", "update_connection", "get_connection", "delete_connection")):
                result = await ConnectionTools(client).call_tool(request)
            else:
                result = CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )

            content_len = len(result.content) if getattr(result, "content", None) else 0
            logger.info(
                "Tool '%s' completed with %d content chunk(s)",
                getattr(request, "name", "<unknown>"),
                content_len,
            )
            return result

        except Exception as exc:  # pragma: no cover
            logger.error("Error handling tool call %s: %s", request.name, exc)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {exc}")]
            )
        finally:
            self.clear_auth_token()


# Global server instance
dbcv_server = DBCVMCPServer()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return dbcv_server.all_tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    auth_token = None

    if "auth_token" in arguments:
        auth_token = arguments.pop("auth_token")

    if auth_token:
        dbcv_server.set_auth_token(auth_token)
        logger.info("Auth token received directly in tool call: %s", _mask_token(auth_token))
    else:
        logger.warning("No auth token provided in tool call")

    request = CallToolRequest(name=name, arguments=arguments)
    result = await dbcv_server.handle_call_tool(request)
    return result.content


async def run_server(auth_token: Optional[str]):
    """Run the MCP server."""
    try:
        dbcv_server.initialize(auth_token)

        if dbcv_server.client:
            health = await dbcv_server.client.health_check()
            logger.info("Backend health check: %s", health)
        else:
            logger.info("Skipping backend health check (no default auth token configured)")

        logger.info("Starting MCP DBCV Server...")
        async with server.run_stdio():
            await asyncio.Future()  # Run forever

    except Exception as exc:  # pragma: no cover
        logger.error("Server failed: %s", exc)
        raise


async def main():
    """Main entry point."""
    auth_token = config.auth_token
    await run_server(auth_token)


if __name__ == "__main__":
    asyncio.run(main())
