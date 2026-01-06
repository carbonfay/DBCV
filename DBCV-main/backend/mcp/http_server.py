"""HTTP MCP Server for DBCV."""

import asyncio
import logging
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import config
from server import dbcv_server


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP DBCV Server",
    description="Model Context Protocol server for DBCV bot creation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_incoming_requests(request: Request, call_next):
    """Log incoming request method and path for troubleshooting."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Completed request: {request.method} {request.url.path} -> {response.status_code}")
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize MCP server on startup."""
    try:
        # Initialize without persisting shared auth token
        dbcv_server.initialize(config.auth_token)
        logger.info("✅ MCP DBCV HTTP Server started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start MCP server: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-dbcv-server"}


def _create_call_tool_request(
    tool_name: str,
    arguments: Dict[str, Any],
    rpc_id: Optional[Any] = None,
) -> Any:
    """Create a lightweight object compatible with dbcv_server expectations."""
    if isinstance(arguments, Mapping):
        safe_arguments: Dict[str, Any] = dict(arguments)
    else:
        safe_arguments = {}
        if arguments not in (None, {}):
            logger.debug(
                "Received non-mapping arguments %s for tool %s; defaulting to empty dict",
                type(arguments).__name__,
                tool_name,
            )

    name = tool_name or safe_arguments.get("name")
    if not name:
        name = "unknown_tool"

    return SimpleNamespace(
        name=name,
        arguments=safe_arguments,
        params={"name": name, "arguments": safe_arguments},
        id=rpc_id,
    )


def _build_initialize_response(rpc_id: Any) -> Dict[str, Any]:
    """Build JSON-RPC response for initialize requests."""
    result = {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "logging": {},
            "prompts": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "tools": {"listChanged": True},
        },
        "serverInfo": {
            "name": "DBCV MCP Server",
            "title": "DBCV MCP Server",
            "version": "1.0.0",
        },
        "instructions": "DBCV MCP Server ���?��?�?�?�'���?�>�?��' ��?�?�'�?�?�?��?�'�< �?�>�? �?�?���?���?��? �� �?���?���?�>��?��? �+�?�'���?�� �? DBCV.",
    }
    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


def _build_tools_list_response(rpc_id: Any) -> Dict[str, Any]:
    """Build JSON-RPC response for tools/list requests."""
    result = _serialize_tool_list()
    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


async def _build_tools_call_response(
    body: Dict[str, Any],
    headers: Mapping[str, str],
    token_from_query: Optional[str] = None,
) -> Dict[str, Any]:
    """Build JSON-RPC response for tools/call requests."""
    rpc_id = body.get("id", 1)
    try:
        params = body.get("params") or {}
        tool_name = (
            params.get("name")
            or params.get("tool")
            or params.get("method")
        )
        arguments = params.get("arguments") or params.get("parameters") or {}

        if not tool_name:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32602, "message": "Tool name is required"},
            }

        auth_header = headers.get("Authorization") or headers.get("authorization")
        token = None
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        token = (
            token
            or params.get("token")
            or arguments.get("auth_token")
            or token_from_query
        )

        if token:
            dbcv_server.set_auth_token(token)
            arguments.setdefault("auth_token", token)
        else:
            logger.debug(
                "No auth token in tools/call; headers=%s params=%s token_query=%s",
                dict(headers),
                params,
                token_from_query,
            )

        tool_request = _create_call_tool_request(tool_name, arguments, rpc_id=rpc_id)
        result = await dbcv_server.handle_call_tool(tool_request)

        content = []
        if result.content:
            for item in result.content:
                if hasattr(item, "text"):
                    content.append({"type": "text", "text": item.text})

        response = {
            "content": content,
            "isError": False,
            "structuredContent": None,
            "nextCursor": None,
        }
        return {"jsonrpc": "2.0", "id": rpc_id, "result": response}

    except Exception as exc:  # pragma: no cover - logged for observability
        logger.error(f"Error in tools/call handler: {exc}")
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -1, "message": str(exc)},
        }


@app.api_route("/", methods=["GET", "POST"])
async def root_info(request: Request):
    """Basic root endpoint for health checks and JSON-RPC routing."""
    if request.method == "GET":
        return {
            "status": "ok",
            "service": "mcp-dbcv-server",
            "message": "MCP endpoints are available under /mcp and /tools."
        }

    try:
        body = await request.json()
    except Exception:
        body = None

    logger.warning(f"Received POST / with body: {body}")

    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return {
            "status": "error",
            "message": "Use /mcp endpoints for MCP JSON-RPC calls.",
            "received": body,
        }

    method = body.get("method")
    rpc_id = body.get("id", 1)

    if method == "initialize":
        logger.info("Handling initialize request at root endpoint.")
        return _build_initialize_response(rpc_id)

    if method == "tools/list":
        logger.info("Handling tools/list request at root endpoint.")
        return _build_tools_list_response(rpc_id)

    if method == "tools/call":
        logger.info("Handling tools/call request at root endpoint.")
        return await _build_tools_call_response(body, request.headers, request.query_params.get("auth_token"))

    if method and method.startswith("notifications/"):
        logger.info(f"Received MCP notification: {method}")
        return Response(status_code=200)

    logger.warning(f"Unknown MCP method at root endpoint: {method}")
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    try:
        tools = dbcv_server.all_tools
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ],
            "count": len(tools)
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/call")
async def call_tool(request: Dict[str, Any]):
    """Call an MCP tool."""
    try:
        tool_name = request.get("name")
        arguments = dict(request.get("arguments") or {})
        auth_token = request.get("auth_token")

        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")

        if auth_token:
            dbcv_server.set_auth_token(auth_token)
            logger.info("Set auth token for tool call (arguments)" )
            arguments.setdefault("auth_token", auth_token)

        tool_request = _create_call_tool_request(tool_name, arguments)

        result = await dbcv_server.handle_call_tool(tool_request)

        response_text = ""
        if result.content:
            for content in result.content:
                if hasattr(content, "text"):
                    response_text += content.text

        return {
            "success": True,
            "result": response_text,
            "tool": tool_name,
        }

    except Exception as exc:
        logger.error(f"Error calling tool {request.get('name', 'unknown')}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        dbcv_server.clear_auth_token()

@app.post("/mcp/process")
async def process_prompt(request: Request):
    """Process prompt with autonomous assistant."""
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        body_token = body.get("auth_token")
        session_id = body.get("session_id") or request.query_params.get("session_id")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        auth_header = request.headers.get("Authorization") or ""
        header_token = None
        if auth_header.lower().startswith("bearer "):
            header_token = auth_header.split(" ", 1)[1].strip() or None

        query_token = request.query_params.get("auth_token")
        auth_token = header_token or body_token or query_token
        if not auth_token:
            raise HTTPException(status_code=401, detail="Authentication token required")

        dbcv_server.set_auth_token(auth_token)
        logger.info("Processing MCP prompt with user auth token")

        from autonomous_assistant import AutonomousAssistant

        assistant = AutonomousAssistant(
            api_key=config.openai_api_key,
            mcp_server_url=config.mcp_server_url,
        )

        result = await assistant.create_response_with_tools(
            prompt,
            auth_token,
            session_id=session_id,
        )

        logger.info("MCP prompt processed successfully")
        return result

    except Exception as exc:  # pragma: no cover - surfaced to caller
        logger.error(f"Process prompt error: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "output_text": f"Failed to process prompt: {str(exc)}",
            "tool_calls": [],
        }
    finally:
        dbcv_server.clear_auth_token()

# --- MCP HTTP transport endpoints expected by Responses API ---

@app.post("/mcp/initialize")
async def mcp_initialize(request: Request):
    """MCP initialize endpoint (JSON-RPC 2.0 style response)."""
    try:
        body = await request.json()
        rpc_id = body.get("id", 1)
        return _build_initialize_response(rpc_id)
    except Exception as e:
        logger.error(f"Error in /mcp/initialize: {e}")
        return {"jsonrpc": "2.0", "id": body.get("id", 1) if 'body' in locals() else 1, "error": {"code": -1, "message": str(e)}}



def _serialize_tool_list() -> Dict[str, Any]:
    """Serialize registered tools into MCP JSON-RPC payload."""

    def _tool_to_json(tool_obj):
        obj = {
            "name": getattr(tool_obj, "name", "unknown"),
            "title": getattr(tool_obj, "name", "unknown"),
            "description": getattr(tool_obj, "description", ""),
            "inputSchema": getattr(tool_obj, "inputSchema", None),
        }
        output_schema = getattr(tool_obj, "outputSchema", None)
        if output_schema is not None:
            obj["outputSchema"] = output_schema
        return obj

    return {
        "tools": [_tool_to_json(tool) for tool in dbcv_server.all_tools],
        "nextCursor": None,
    }


@app.api_route("/mcp/tools/list", methods=["GET", "POST"])
async def mcp_tools_list(request: Request):
    """List MCP tools (JSON-RPC 2.0 style response)."""
    try:
        rpc_id = 1
        if request.method == "POST":
            body = await request.json()
            rpc_id = body.get("id", 1)
        else:
            rpc_id = request.query_params.get("id", 1)

        logger.info(
            f"Serving tools list for request id={rpc_id} via {request.method} {request.url.path}"
        )

        return _build_tools_list_response(rpc_id)
    except Exception as e:
        logger.error(f"Error in /mcp/tools/list: {e}")
        rpc_id = request.query_params.get("id", 1)
        if request.method == "POST":
            try:
                body = await request.json()
                rpc_id = body.get("id", rpc_id)
            except Exception:
                pass
        return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -1, "message": str(e)}}


@app.api_route("/mcp/tools", methods=["GET", "POST"])
async def mcp_tools(request: Request):
    """Alias endpoint for listing MCP tools."""
    return await mcp_tools_list(request)


@app.post("/mcp/tools/call")
async def mcp_tools_call(request: Request):
    """Call an MCP tool (JSON-RPC 2.0 style response)."""
    try:
        body = await request.json()
        return await _build_tools_call_response(body, request.headers, request.query_params.get("auth_token"))
    except Exception as e:
        logger.error(f"Error in /mcp/tools/call: {e}")
        return {"jsonrpc": "2.0", "id": body.get("id", 1) if 'body' in locals() else 1, "error": {"code": -1, "message": str(e)}}

@app.post("/auth/set-token")
async def set_auth_token(request: Dict[str, Any]):
    """Deprecated endpoint retained for backward compatibility."""
    auth_token = request.get("auth_token")
    if not auth_token:
        raise HTTPException(status_code=400, detail="Auth token is required")

    logger.warning("/auth/set-token is deprecated; send Authorization header with each request instead")
    return {
        "success": True,
        "message": "Token accepted for validation only; include Authorization header on subsequent requests.",
    }




if __name__ == "__main__":
    # Run HTTP server
    uvicorn.run(
        "http_server:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level=config.log_level.lower()
    )




# DEBUG HEADERS PLACEHOLDER







