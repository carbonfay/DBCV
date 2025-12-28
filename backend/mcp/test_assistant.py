#!/usr/bin/env python3
"""Test Autonomous Assistant with MCP tools."""

import asyncio
import logging
import sys
from pathlib import Path

import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from autonomous_assistant import AutonomousAssistant
from mcp.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.asyncio, pytest.mark.skip(reason="Manual MCP test")]


async def test_assistant():
    """Test the autonomous assistant."""
    try:
        # Validate configuration
        config.validate()
        
        # Get configuration
        api_key = config.openai_api_key
        mcp_server_url = config.mcp_server_url
        auth_token = config.auth_token or "default-token"
        
        logger.info("🚀 Testing Autonomous DBCV Assistant...")
        logger.info(f"🔧 MCP Server URL: {mcp_server_url}")
        
        # Create assistant
        assistant = AutonomousAssistant(api_key, mcp_server_url)
        
        # Test prompts
        test_prompts = [
            "Создай простого бота для приветствия пользователей с шагом 'Приветствие'",
            "Создай бота для обработки заказов с шагами: получение заказа, проверка товара, отправка подтверждения",
            "Создай бота для получения новостей с HTTP запросом к API новостей"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            logger.info(f"🧪 Test {i}: {prompt}")
            
            try:
                result = await assistant.create_response_with_tools(prompt, auth_token)
                
                logger.info(f"✅ Test {i} completed: {result['response_id']}")
                logger.info(f"📝 Output: {result['output_text'][:200]}...")
                
                if result['tool_calls']:
                    logger.info(f"🔧 Tool calls executed: {len(result['tool_calls'])}")
                    for j, tool_call in enumerate(result['tool_calls']):
                        logger.info(f"  {j+1}. {tool_call['tool']}: {tool_call['result']}")
                else:
                    logger.info("ℹ️ No tool calls executed")
                
                logger.info("-" * 50)
                
            except Exception as e:
                logger.error(f"❌ Test {i} failed: {e}")
                continue
        
        logger.info("🎉 All tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)


async def main():
    """Main entry point."""
    await test_assistant()


if __name__ == "__main__":
    asyncio.run(main())
