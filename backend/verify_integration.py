#!/usr/bin/env python3
"""Verification script for OpenWeatherMap Daily Forecast Integration."""

import sys
import inspect
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def check_import():
    """Check if the integration can be imported."""
    print("✓ Checking imports...")
    try:
        from app.integrations.weather.openweathermap_daily_forecast import (
            OpenWeatherMapDailyForecastIntegration
        )
        print("  ✓ Successfully imported OpenWeatherMapDailyForecastIntegration")
        return OpenWeatherMapDailyForecastIntegration
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        return None

def check_class_structure(integration_class):
    """Check if the class structure is correct."""
    print("\n✓ Checking class structure...")
    
    # Check inheritance
    from app.integrations.base import BaseIntegration
    if not issubclass(integration_class, BaseIntegration):
        print(f"  ✗ Class does not inherit from BaseIntegration")
        return False
    print("  ✓ Class inherits from BaseIntegration")
    
    # Check metadata property
    instance = integration_class()
    if not hasattr(instance, 'metadata'):
        print("  ✗ Missing 'metadata' property")
        return False
    print("  ✓ Has 'metadata' property")
    
    # Check execute method
    if not hasattr(instance, 'execute'):
        print("  ✗ Missing 'execute' method")
        return False
    if not inspect.iscoroutinefunction(instance.execute):
        print("  ✗ 'execute' method is not async")
        return False
    print("  ✓ Has async 'execute' method")
    
    return True

def check_metadata(integration_class):
    """Check if metadata is properly configured."""
    print("\n✓ Checking metadata...")
    
    instance = integration_class()
    metadata = instance.metadata
    
    checks = [
        ("id", "openweathermap_daily_forecast"),
        ("version", "1.0.0"),
        ("name", "OpenWeatherMap Get Daily Forecast"),
        ("category", "weather"),
        ("credentials_provider", "openweathermap"),
        ("credentials_strategy", "api_key"),
    ]
    
    all_passed = True
    for attr, expected in checks:
        actual = getattr(metadata, attr, None)
        if actual == expected:
            print(f"  ✓ {attr}: {actual}")
        else:
            print(f"  ✗ {attr}: expected '{expected}', got '{actual}'")
            all_passed = False
    
    # Check config_schema
    if metadata.config_schema:
        print("  ✓ Has config_schema")
        schema = metadata.config_schema
        
        if "required" in schema and "latitude" in schema["required"] and "longitude" in schema["required"]:
            print("    ✓ Required fields: latitude, longitude")
        else:
            print("    ✗ Missing required fields")
            all_passed = False
        
        if "properties" in schema:
            print("    ✓ Has properties")
            props = schema["properties"]
            if "latitude" in props and "longitude" in props and "units" in props:
                print("      ✓ Has latitude, longitude, units properties")
            else:
                print("      ✗ Missing expected properties")
                all_passed = False
        else:
            print("    ✗ Missing properties")
            all_passed = False
    else:
        print("  ✗ Missing config_schema")
        all_passed = False
    
    # Check examples
    if metadata.examples:
        print(f"  ✓ Has {len(metadata.examples)} examples")
    else:
        print("  ✗ Missing examples")
        all_passed = False
    
    return all_passed

def check_library_usage(integration_class):
    """Check that the integration uses httpx."""
    print("\n✓ Checking library usage...")
    
    instance = integration_class()
    
    # Read the source code
    import inspect
    source = inspect.getsource(integration_class)
    
    checks = [
        ("httpx", "Uses httpx library"),
        ("credentials_resolver.get_default_for", "Gets credentials via resolver"),
        ("try:", "Has error handling"),
        ("except", "Has exception handling"),
        ('error_code":', "Returns error codes in response"),
        ('{"response":', "Returns correct response format"),
    ]
    
    all_passed = True
    for check_str, description in checks:
        if check_str in source:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ Missing: {description}")
            all_passed = False
    
    return all_passed

def check_error_handling(integration_class):
    """Check error handling implementation."""
    print("\n✓ Checking error handling...")
    
    import inspect
    source = inspect.getsource(integration_class.execute)
    
    # Check for different error cases
    error_checks = [
        ("httpx.HTTPError", "Handles httpx HTTP errors"),
        ("error_code", "Sets error codes"),
        ("description", "Sets error descriptions"),
        ("await logger.error", "Logs errors"),
        ("400,", "Handles 400 Bad Request"),
        ("401,", "Handles 401 Unauthorized"),
        ("500,", "Handles 500 Server Error"),
    ]
    
    all_passed = True
    for check_str, description in error_checks:
        if check_str in source:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ Missing: {description}")
            all_passed = False
    
    return all_passed

def main():
    """Run all checks."""
    print("=" * 60)
    print("OpenWeatherMap Daily Forecast Integration Verification")
    print("=" * 60)
    
    # Check 1: Import
    integration_class = check_import()
    if not integration_class:
        print("\n✗ Failed: Cannot import integration")
        return False
    
    # Check 2: Class structure
    if not check_class_structure(integration_class):
        print("\n✗ Failed: Class structure is incorrect")
        return False
    
    # Check 3: Metadata
    if not check_metadata(integration_class):
        print("\n✗ Failed: Metadata is incomplete or incorrect")
        return False
    
    # Check 4: Library usage
    if not check_library_usage(integration_class):
        print("\n✗ Failed: Library usage is incorrect")
        return False
    
    # Check 5: Error handling
    if not check_error_handling(integration_class):
        print("\n✗ Failed: Error handling is incomplete")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All checks passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
