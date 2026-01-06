#!/usr/bin/env python3
"""Run MCP DBCV HTTP Server."""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for local imports
current_path = Path(__file__).parent
sys.path.insert(0, str(current_path))

from http_server import app
from config import config
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    try:
        # Validate configuration
        config.validate()
        
        logger.info("🚀 Starting MCP DBCV HTTP Server...")
        logger.info(f"🔧 Backend URL: {config.backend_api_url}")
        logger.info(f"🌐 MCP Server URL: {config.mcp_server_url}")
        logger.info(f"📊 Log Level: {config.log_level}")
        
        # Run HTTP server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8005,
            log_level=config.log_level.lower(),
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
