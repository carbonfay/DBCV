"""Configuration for MCP DBCV Server."""

import logging
import os
from typing import Optional





class MCPConfig:
    """Configuration for MCP DBCV Server."""
    
    def __init__(self):
        # DBCV Backend API
        self.backend_url = os.getenv("DBCV_BACKEND_URL", "http://localhost:8003")
        self.api_prefix = "/api/v1"
        
        # MCP Server
        self._mcp_server_url = os.getenv("MCP_SERVER_URL", "https://wondrously-winged-cub.cloudpub.ru")
        self.mcp_scheme = os.getenv("MCP_SCHEME", "http")
        self.mcp_host = os.getenv("MCP_HOST", "localhost")
        self.mcp_port = int(os.getenv("MCP_PORT", "8005"))
        
        # Authentication
        self.auth_token = os.getenv("MCP_AUTH_TOKEN")
        
        # OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
    @property
    def backend_api_url(self) -> str:
        """Get full backend API URL."""
        return f"{self.backend_url}{self.api_prefix}"
    
    @property
    def mcp_server_url(self) -> str:
        """Get MCP server URL."""
        if self._mcp_server_url:
            return self._mcp_server_url.rstrip("/")
        return f"{self.mcp_scheme}://{self.mcp_host}:{self.mcp_port}"
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        if not self.auth_token:
            logging.getLogger(__name__).warning(
                "MCP_AUTH_TOKEN is not configured; relying on per-request Authorization headers."
            )


# Global config instance
config = MCPConfig()


