"""Shared helpers for MCP tool authorization."""

from __future__ import annotations

import logging
from typing import Iterable, Optional, Set

from mcp.types import CallToolResult, TextContent

from client import DBCVAPIClient

# Roles that are allowed to execute privileged MCP tools by default.
DEFAULT_ALLOWED_ROLES: Set[str] = {"DEVELOPER", "ADMIN"}


async def ensure_authorized_roles(
    client: DBCVAPIClient,
    allowed_roles: Iterable[str],
    logger: logging.Logger,
    action_name: str,
) -> Optional[CallToolResult]:
    """
    Ensure authenticated user has one of the allowed roles.

    Returns a CallToolResult with an error message when authorization fails,
    otherwise None to indicate the caller may proceed.
    """
    try:
        user_info = await client.get_user_info()
    except Exception as exc:  # pragma: no cover - network errors are logged
        logger.error("Failed to check user permissions for %s: %s", action_name, exc)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: Authentication failed - {exc}")]
        )

    role = (user_info.get("role") or "").upper()
    normalized_allowed = {role_name.upper() for role_name in allowed_roles}

    if role not in normalized_allowed:
        readable_roles = ", ".join(sorted(normalized_allowed))
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: Access denied. Allowed roles: {readable_roles}.",
                )
            ]
        )

    return None

