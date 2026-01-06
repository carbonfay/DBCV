#!/usr/bin/env python3
"""Test MCP DBCV Server with authentication token."""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from autonomous_assistant import AutonomousAssistant
from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_with_token():
    """Test the autonomous assistant with authentication token."""
    try:
        # Validate configuration
        config.validate()
        
        # Get configuration
        api_key = config.openai_api_key
        mcp_server_url = config.mcp_server_url
        auth_token = config.auth_token or "test-jwt-token"
        
        logger.info("🚀 Testing Autonomous DBCV Assistant with JWT token...")
        logger.info(f"🔧 MCP Server URL: {mcp_server_url}")
        logger.info(f"🔐 Auth Token: {auth_token[:20]}...")
        
        # Create assistant
        assistant = AutonomousAssistant(api_key, mcp_server_url)
        
        # Test prompt
        test_prompt = "Создай простого бота для приветствия пользователей с шагом 'Приветствие'"
        logger.info(f"🧪 Test prompt: {test_prompt}")
        
        try:
            result = await assistant.create_response_with_tools(test_prompt, auth_token)
            
            logger.info(f"✅ Test completed: {result['response_id']}")
            logger.info(f"📝 Output: {result['output_text'][:200]}...")
            
            if result['tool_calls']:
                logger.info(f"🔧 Tool calls executed: {len(result['tool_calls'])}")
                for j, tool_call in enumerate(result['tool_calls']):
                    logger.info(f"  {j+1}. {tool_call['tool']}: {tool_call['result']}")
            else:
                logger.info("ℹ️ No tool calls executed")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
        
        logger.info("🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return False


async def main():
    """Main entry point."""
    success = await test_with_token()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
