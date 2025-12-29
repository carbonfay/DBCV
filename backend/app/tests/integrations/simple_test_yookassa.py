#!/usr/bin/env python3
"""Простой тест для YooKassa интеграции без сложных зависимостей."""

import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

# Добавляем путь к модулям
sys.path.insert(0, '/home/arseniy/Practise/DBCV/backend')

try:
    from app.integrations.yookassa.get_payment import YookassaGetPaymentIntegration
    print("✅ Импорт YookassaGetPaymentIntegration успешен")
except ImportError as e:
    print(f"❌ Ошибка импорта YookassaGetPaymentIntegration: {e}")
    sys.exit(1)

async def test_metadata():
    """Тест метаданных."""
    print("\n🧪 Тестируем метаданные...")
    integration = YookassaGetPaymentIntegration()
    metadata = integration.metadata
    
    assert metadata.id == "yookassa_get_payment", f"Expected 'yookassa_get_payment', got '{metadata.id}'"
    assert metadata.version == "1.0.0", f"Expected '1.0.0', got '{metadata.version}'"
    assert metadata.category == "payments", f"Expected 'payments', got '{metadata.category}'"
    assert metadata.credentials_provider == "other", f"Expected 'other', got '{metadata.credentials_provider}'"
    assert metadata.credentials_strategy == "api_key", f"Expected 'api_key', got '{metadata.credentials_strategy}'"
    
    print("✅ Метаданные корректны")

async def test_execute_success():
    """Тест успешного выполнения."""
    print("\n🧪 Тестируем успешное выполнение...")
    
    integration = YookassaGetPaymentIntegration()
    
    # Создаем mock объекты
    credentials_resolver = MagicMock()
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "account_id": "501156",
            "secret_key": "test_Fh8hUAVVBGUGbjmlzba6TB0iyUbos_lueTHE-axOwM4"
        }
    })
    
    logger = MagicMock()
    logger.error = AsyncMock()
    logger.info = AsyncMock()
    
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    # Mock для Payment объекта
    mock_payment = MagicMock()
    mock_payment.id = "24b94598-000f-5000-9000-1b68e7b15f3f"
    mock_payment.status = "succeeded"
    mock_payment.paid = True
    mock_payment.refundable = True
    mock_payment.description = "Тестовый платеж"
    mock_payment.created_at = None
    mock_payment.test = True
    mock_payment.metadata = {"order_id": "12345"}
    
    # Mock для amount
    mock_payment.amount = MagicMock()
    mock_payment.amount.value = "100.00"
    mock_payment.amount.currency = "RUB"
    
    # Mock для payment_method
    mock_payment.payment_method = MagicMock()
    mock_payment.payment_method.type = "bank_card"
    mock_payment.payment_method.id = "pm_test_123"
    mock_payment.payment_method.saved = False
    
    # Mock для recipient
    mock_payment.recipient = MagicMock()
    mock_payment.recipient.account_id = "501156"
    mock_payment.recipient.gateway_id = "test_gateway"
    
    # Mock для refunded_amount
    mock_payment.refunded_amount = MagicMock()
    mock_payment.refunded_amount.value = "0.00"
    mock_payment.refunded_amount.currency = "RUB"
    
    with patch('app.integrations.yookassa.get_payment.YOOKASSA_AVAILABLE', True), \
         patch('app.integrations.yookassa.get_payment.Configuration') as mock_config, \
         patch('app.integrations.yookassa.get_payment.Payment') as mock_payment_class:
        
        mock_payment_class.find_one.return_value = mock_payment
        
        result = await integration.execute(
            config={"payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        # Проверяем результат
        assert result["response"]["ok"] is True, f"Expected True, got {result['response']['ok']}"
        assert result["response"]["result"]["id"] == "24b94598-000f-5000-9000-1b68e7b15f3f"
        assert result["response"]["result"]["status"] == "succeeded"
        assert result["response"]["result"]["amount"]["value"] == "100.00"
        assert result["response"]["result"]["amount"]["currency"] == "RUB"
        
        print("✅ Успешное выполнение работает корректно")

async def test_missing_credentials():
    """Тест отсутствующих credentials."""
    print("\n🧪 Тестируем отсутствующие credentials...")
    
    integration = YookassaGetPaymentIntegration()
    
    credentials_resolver = MagicMock()
    credentials_resolver.get_default_for = AsyncMock(return_value=None)
    
    logger = MagicMock()
    logger.error = AsyncMock()
    
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    result = await integration.execute(
        config={"payment_id": "test-payment-id"},
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 401
    assert "credentials not found" in result["response"]["description"]
    
    print("✅ Обработка отсутствующих credentials работает корректно")

async def test_missing_payment_id():
    """Тест отсутствующего payment_id."""
    print("\n🧪 Тестируем отсутствующий payment_id...")
    
    integration = YookassaGetPaymentIntegration()
    
    credentials_resolver = MagicMock()
    credentials_resolver.get_default_for = AsyncMock(return_value={
        "payload": {
            "account_id": "501156",
            "secret_key": "test_key"
        }
    })
    
    logger = MagicMock()
    logger.error = AsyncMock()
    
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    result = await integration.execute(
        config={},  # Отсутствует payment_id
        credentials_resolver=credentials_resolver,
        bot_id=bot_id,
        logger=logger
    )
    
    assert result["response"]["ok"] is False
    assert result["response"]["error_code"] == 400
    assert "payment_id is required" in result["response"]["description"]
    
    print("✅ Обработка отсутствующего payment_id работает корректно")

async def test_library_not_available():
    """Тест недоступности библиотеки."""
    print("\n🧪 Тестируем недоступность библиотеки...")
    
    integration = YookassaGetPaymentIntegration()
    
    credentials_resolver = MagicMock()
    logger = MagicMock()
    logger.error = AsyncMock()
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    
    with patch('app.integrations.yookassa.get_payment.YOOKASSA_AVAILABLE', False):
        result = await integration.execute(
            config={"payment_id": "test-payment-id"},
            credentials_resolver=credentials_resolver,
            bot_id=bot_id,
            logger=logger
        )
        
        assert result["response"]["ok"] is False
        assert result["response"]["error_code"] == 500
        assert "library is not installed" in result["response"]["description"]
    
    print("✅ Обработка недоступности библиотеки работает корректно")

async def main():
    """Запуск всех тестов."""
    print("🚀 Запуск тестов YooKassa интеграции...")
    
    try:
        await test_metadata()
        await test_execute_success()
        await test_missing_credentials()
        await test_missing_payment_id()
        await test_library_not_available()
        
        print("\n🎉 Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"\n❌ Тест провален: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
