"""Helper to run integration tests programmatically using pytest.
"""
import sys
import pytest

if __name__ == "__main__":
    # Run only integration tests folder
    rc = pytest.main(["-q", "backend/app/tests/integrations"]) 
    sys.exit(rc)
