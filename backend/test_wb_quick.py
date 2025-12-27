#!/usr/bin/env python3
"""Простой тест интеграции Wildberries."""

import sys

print("Testing Wildberries integration...")

# Добавляем путь к app в PYTHONPATH
sys.path.insert(0, '.')

try:
    from app.integrations.registry import registry
    print("✅ Registry imported successfully")
    
    wb = registry.get("wildberries_update_stock")
    if wb:
        print(f"✅ Wildberries integration found: {wb.metadata.id}")
        print(f"   Version: {wb.metadata.version}")
        print(f"   Name: {wb.metadata.name}")
        print(f"   Description: {wb.metadata.description}")
        
        # List all integrations
        print("\n📊 All registered integrations:")
        for meta in registry.list_all():
            print(f"   - {meta.id} v{meta.version} ({meta.category})")
    else:
        print("❌ Wildberries integration NOT found")
        print("\nAvailable integrations:")
        for meta in registry.list_all():
            print(f"   - {meta.id} v{meta.version}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Test completed successfully!")


