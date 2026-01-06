#!/usr/bin/env python3
"""Test MCP DBCV HTTP Server."""

import asyncio
import logging
import sys
import httpx
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from .config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_http_server():
    """Test the HTTP MCP server."""
    try:
        # Validate configuration
        config.validate()
        
        base_url = "http://localhost:8005"
        auth_token = config.auth_token or "test-jwt-token"
        
        logger.info("🚀 Testing MCP DBCV HTTP Server...")
        logger.info(f"🔧 Base URL: {base_url}")
        logger.info(f"🔐 Auth Token: {auth_token[:20]}...")
        
        async with httpx.AsyncClient() as client:
            # Test health check
            logger.info("🧪 Testing health check...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.info(f"✅ Health check passed: {response.json()}")
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
            
            # Test list tools
            logger.info("🧪 Testing list tools...")
            response = await client.get(f"{base_url}/tools")
            if response.status_code == 200:
                tools_data = response.json()
                logger.info(f"✅ List tools passed: {tools_data['count']} tools available")
                for tool in tools_data['tools'][:3]:  # Show first 3 tools
                    logger.info(f"  - {tool['name']}: {tool['description']}")
            else:
                logger.error(f"❌ List tools failed: {response.status_code}")
                return False
            
            # Test set auth token
            logger.info("🧪 Testing set auth token...")
            response = await client.post(
                f"{base_url}/auth/set-token",
                json={"auth_token": auth_token}
            )
            if response.status_code == 200:
                logger.info(f"✅ Set auth token passed: {response.json()}")
            else:
                logger.error(f"❌ Set auth token failed: {response.status_code}")
                return False
            
            # Test tool call (list bots)
            logger.info("🧪 Testing tool call (list_bots)...")
            response = await client.post(
                f"{base_url}/tools/call",
                json={
                    "name": "list_bots",
                    "arguments": {"skip": 0, "limit": 5},
                    "auth_token": auth_token
                }
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Tool call passed: {result['success']}")
                logger.info(f"📝 Result: {result['result'][:200]}...")
            else:
                logger.error(f"❌ Tool call failed: {response.status_code}")
                logger.error(f"📝 Error: {response.text}")
                return False
        
        logger.info("🎉 All HTTP server tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def main():
    """Main entry point."""
    success = await test_http_server()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
