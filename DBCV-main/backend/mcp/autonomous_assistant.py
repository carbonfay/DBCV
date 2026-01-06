"""Autonomous GPT Assistant using Responses API with MCP tools."""

from pathlib import Path

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from openai import AsyncOpenAI

from config import config

logger = logging.getLogger(__name__)


class AutonomousAssistant:
    """Autonomous GPT assistant using Responses API with MCP tools."""

    def __init__(self, api_key: str, mcp_server_url: str):
        proxy = os.getenv("PROXY")
        if proxy and "://" not in proxy:
            proxy = f"http://{proxy}"
        http_client = (
            httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(proxy=proxy))
            if proxy
            else None
        )

        self.client = AsyncOpenAI(api_key=api_key, http_client=http_client)
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self._tracking_header = {"X-Internal-Token": config.auth_token or ""}

    def _build_server_url(self, auth_token: str) -> str:
        if not auth_token:
            return self.mcp_server_url
        encoded_token = quote(auth_token, safe="")
        joiner = "&" if "?" in self.mcp_server_url else "?"
        return f"{self.mcp_server_url}{joiner}auth_token={encoded_token}"

    async def _send_tracking_event(
        self,
        session_id: Optional[str],
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not session_id or not config.backend_api_url:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{config.backend_api_url}/tracking/sessions/{session_id}/events",
                    json={"type": event_type, "data": payload or {}},
                    headers=self._tracking_header,
                )
        except Exception as exc:
            logger.debug(
                "Tracking event '%s' for session %s failed: %s",
                event_type,
                session_id,
                exc,
            )

    async def create_response_with_tools(
        self,
        prompt: str,
        auth_token: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a response using Responses API with MCP tools."""
        output_chunks: List[str] = []
        final_response_data: Dict[str, Any] = {}

        try:
            async with self.client.responses.stream(
                model="gpt-4o",
                instructions=self._get_assistant_instructions(),
                tools=[
                    {
                        "type": "mcp",
                        "server_label": "dbcv-mcp-server",
                        "server_url": self._build_server_url(auth_token),
                        "allowed_tools": [
                            "create_bot",
                            "get_bot",
                            "list_bot",
                            "update_bot",
                            "create_step",
                            "update_step",
                            "get_step",
                            "delete_step",
                            "create_request",
                            "update_request",
                            "get_request",
                            "delete_request",
                            "create_connection_group",
                            "update_connection_group",
                            "get_connection_group_info",
                            "delete_connection_group",
                        ],
                        "require_approval": "never",
                    }
                ],
                tool_choice="auto",
                parallel_tool_calls=False,
                input=prompt,
            ) as stream:
                async for event in stream:
                    event_type = getattr(event, "type", "")

                    if event_type == "response.output_text.delta":
                        chunk = getattr(event, "delta", None)
                        if chunk:
                            output_chunks.append(chunk)
                            await self._send_tracking_event(
                                session_id,
                                "ai_thought",
                                {
                                    "chunk": chunk,
                                    "timestamp": getattr(event, "created_at", None),
                                },
                            )
                    elif event_type == "response.tool_call.delta":
                        payload = (
                            event.model_dump()
                            if hasattr(event, "model_dump")
                            else getattr(event, "__dict__", {})
                        )
                        await self._send_tracking_event(session_id, "ai_tool_update", payload)
                    elif event_type == "response.error":
                        await self._send_tracking_event(
                            session_id,
                            "ai_error",
                            {"message": getattr(event, "error", None)},
                        )

                final_response = await stream.get_final_response()
                final_response_data = (
                    final_response.model_dump()
                    if hasattr(final_response, "model_dump")
                    else getattr(final_response, "__dict__", {})
                )

        except Exception as exc:
            logger.error("Failed to create response: %s", exc)
            await self._send_tracking_event(session_id, "ai_error", {"message": str(exc)})
            raise

        output_text = final_response_data.get("output_text") or "".join(output_chunks)
        tool_calls = final_response_data.get("tool_calls") or []

        if session_id:
            await self._send_tracking_event(
                session_id,
                "ai_completed",
                {"output_text": output_text, "tool_calls": tool_calls},
            )

        return {
            "success": True,
            "status": final_response_data.get("status", "completed"),
            "response_id": final_response_data.get("id"),
            "output_text": output_text,
            "tool_calls": tool_calls,
            "error": None,
        }

    def _get_assistant_instructions(self) -> str:
        """Get assistant instructions for autonomous operation."""
        instructions_path = Path(__file__).resolve().parent / "init_files" / "assistant_instructions.md"
        try:
            return instructions_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Assistant instructions file not found at %s. Using fallback text.", instructions_path)
            return (
                "Assistant instructions are missing. Respond with JSON containing reasoning, tools_to_use, and actions. "
                "Rely on MCP tools (create_step, create_request, create_connection_group, etc.), always include required "
                "identifiers such as bot_id, step_id, and request_id, and represent headers/params/variables as structured JSON."
            )
