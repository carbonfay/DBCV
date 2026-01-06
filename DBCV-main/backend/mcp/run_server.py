#!/usr/bin/env python3
"""Run MCP DBCV Server."""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from server import server
from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point."""
    try:
        # Validate configuration
        config.validate()
        
        # Get auth token
        auth_token = config.auth_token
        
        logger.info("🚀 Starting MCP DBCV Server...")
        logger.info(f"🔧 Backend URL: {config.backend_api_url}")
        logger.info(f"🌐 MCP Server URL: {config.mcp_server_url}")
        
        # Import and initialize server
        from server import dbcv_server
        dbcv_server.initialize(auth_token)
        
        # Health check
        if dbcv_server.client:
            health = await dbcv_server.client.health_check()
            logger.info("Backend health check: %s", health)
        else:
            logger.info("Skipping backend health check (no default auth token configured)")

        # Start server
        async with server.run_stdio():
            await asyncio.Future()  # Run forever
            
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
