#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Тестовый скрипт для проверки регистрации Moodle интеграции."""
import sys
import os

# Устанавливаем UTF-8 для вывода
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.integrations.registry import registry
    
    # Проверяем регистрацию
    integration = registry.get('moodle_create_course')
    
    if integration:
        print("[OK] Integration found!")
        print(f"   Name: {integration.metadata.name}")
        print(f"   ID: {integration.metadata.id}")
        print(f"   Version: {integration.metadata.version}")
        print(f"   Category: {integration.metadata.category}")
        print(f"   Credentials Provider: {integration.metadata.credentials_provider}")
        print(f"   Credentials Strategy: {integration.metadata.credentials_strategy}")
        print(f"   Library: {integration.metadata.library_name}")
        print(f"   Has examples: {len(integration.metadata.examples) if integration.metadata.examples else 0} examples")
        sys.exit(0)
    else:
        print("[ERROR] Integration NOT found in registry")
        print(f"   Available integrations: {list(registry._latest_versions.keys())}")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

