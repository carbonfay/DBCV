"""Schemas for MCP DBCV Server."""

from .bot import BotInfo, BotCreate, BotUpdate
from .step import StepInfo, StepCreate, StepUpdate
from .request import RequestInfo, RequestCreate, RequestUpdate
from .connection import (
    ConnectionInfo, ConnectionCreate, ConnectionUpdate,
    ConnectionGroupInfo, ConnectionGroupCreate, ConnectionGroupUpdate
)

__all__ = [
    "BotInfo",
    "BotCreate",
    "BotUpdate",
    "StepInfo",
    "StepCreate",
    "StepUpdate",
    "RequestInfo",
    "RequestCreate",
    "RequestUpdate",
    "ConnectionInfo",
    "ConnectionCreate",
    "ConnectionUpdate",
    "ConnectionGroupInfo",
    "ConnectionGroupCreate",
    "ConnectionGroupUpdate",
]
