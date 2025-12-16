#!/usr/bin/env python3
"""Test imports for MCP DBCV Server."""

import sys
from pathlib import Path

import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

pytestmark = pytest.mark.skip(reason="Manual MCP test")

def test_imports():
    """Test all imports."""
    try:
        print("🧪 Testing imports...")
        
        # Test config
        print("  - Testing config...")
        from mcp.config import config
        print(f"    ✅ Config loaded: {config.backend_api_url}")
        
        # Test client
        print("  - Testing client...")
        from mcp.client import DBCVAPIClient
        print("    ✅ Client imported")
        
        # Test schemas
        print("  - Testing schemas...")
        from mcp.schemas import BotCreate, StepCreate, RequestCreate, ConnectionGroupCreate
        print("    ✅ Schemas imported")
        
        # Test tools
        print("  - Testing tools...")
        from mcp.tools import BotTools, StepTools, RequestTools, ConnectionTools
        print("    ✅ Tools imported")
        
        # Test server
        print("  - Testing server...")
        from mcp.server import dbcv_server
        print("    ✅ Server imported")
        
        # Test HTTP server
        print("  - Testing HTTP server...")
        from mcp.http_server import app
        print("    ✅ HTTP server imported")
        
        # Test autonomous assistant
        print("  - Testing autonomous assistant...")
        from mcp.autonomous_assistant import AutonomousAssistant
        print("    ✅ Autonomous assistant imported")
        
        print("🎉 All imports successful!")
        assert True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_imports()
