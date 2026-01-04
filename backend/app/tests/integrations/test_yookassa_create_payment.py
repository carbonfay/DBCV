#!/usr/bin/env python3
"""
Простой тест для интеграции YooKassa Create Payment.
Этот тест демонстрирует использование интеграции без реального API вызова.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


# Мокируем библиотеку yookassa для тестирования
class MockPayment:
    def __init__(self):
        self.id = "24b94598-000f-5000-9000-1b68e7b15f3f"
        self.status = "pending"
        self.amount = MagicMock()
        self.amount.value = "100.00"
        self.amount.currency = "RUB"
        self.description = "Test payment"
        self.confirmation = MagicMock()
        self.confirmation.type = "redirect"
        self.confirmation.confirmation_url = (
            "https://yoomoney.ru/checkout/payments/v2/contract?orderId=test"
        )
        self.created_at = "2023-01-01T00:00:00.000Z"
        self.paid = False
        self.refundable = False
        self.metadata = {"test": "true"}
        self.test = True

    @classmethod
    def create(cls, payment_data):
        return cls()


class MockConfiguration:
    account_id = None
    secret_key = None


# Мокируем модуль yookassa
import sys
from unittest.mock import MagicMock

mock_yookassa = MagicMock()
mock_yookassa.Configuration = MockConfiguration
mock_yookassa.Payment = MockPayment
mock_yookassa.domain.exceptions.ApiError = Exception
sys.modules["yookassa"] = mock_yookassa
sys.modules["yookassa.domain"] = MagicMock()
sys.modules["yookassa.domain.exceptions"] = MagicMock()

# Теперь импортируем нашу интеграцию
from app.integrations.yookassa.create_payment import YookassaCreatePaymentIntegration


async def test_yookassa_create_payment():
    """Тест создания платежа YooKassa."""
    print("🧪 Тестирование YooKassa Create Payment Integration")

    # Создаем интеграцию
    integration = YookassaCreatePaymentIntegration()

    # Проверяем метаданные
    metadata = integration.metadata
    print(f"✅ ID интеграции: {metadata.id}")
    print(f"✅ Версия: {metadata.version}")
    print(f"✅ Название: {metadata.name}")
    print(f"✅ Категория: {metadata.category}")
    print(f"✅ Провайдер credentials: {metadata.credentials_provider}")
    print(f"✅ Стратегия: {metadata.credentials_strategy}")

    # Мокируем credentials resolver
    mock_credentials_resolver = AsyncMock()
    mock_credentials_resolver.get_default_for.return_value = {
        "payload": {"account_id": "test_account_id", "secret_key": "test_secret_key"}
    }

    # Мокируем logger
    mock_logger = AsyncMock()

    # Тестовые данные для создания платежа
    config = {
        "amount": "100.00",
        "currency": "RUB",
        "description": "Test payment from DBCV",
        "return_url": "https://example.com/success",
        "capture": True,
        "metadata": {"order_id": "12345", "user_id": "67890"},
    }

    # Выполняем интеграцию
    print("\n🚀 Выполнение интеграции...")
    result = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger,
    )

    # Проверяем результат
    print(f"\n📊 Результат выполнения:")
    print(f"Status: {'✅ SUCCESS' if result['response']['ok'] else '❌ FAILED'}")

    if result["response"]["ok"]:
        payment_result = result["response"]["result"]
        print(f"Payment ID: {payment_result['id']}")
        print(f"Status: {payment_result['status']}")
        print(
            f"Amount: {payment_result['amount']['value']} {payment_result['amount']['currency']}"
        )
        print(f"Description: {payment_result['description']}")
        print(f"Confirmation URL: {payment_result['confirmation']['confirmation_url']}")
        print(f"Created at: {payment_result['created_at']}")
        print(f"Test mode: {payment_result['test']}")
    else:
        print(f"Error: {result['response']['description']}")

    # Тест с отсутствующими credentials
    print("\n🧪 Тестирование с отсутствующими credentials...")
    mock_credentials_resolver.get_default_for.return_value = None

    result_no_creds = await integration.execute(
        config=config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger,
    )

    print(
        f"Result without credentials: {'✅ EXPECTED ERROR' if not result_no_creds['response']['ok'] else '❌ UNEXPECTED SUCCESS'}"
    )
    print(f"Error message: {result_no_creds['response']['description']}")

    # Тест с неполными данными
    print("\n🧪 Тестирование с неполными данными...")
    mock_credentials_resolver.get_default_for.return_value = {
        "payload": {"account_id": "test_account_id", "secret_key": "test_secret_key"}
    }

    incomplete_config = {
        "amount": "50.00"
        # отсутствуют currency и return_url
    }

    result_incomplete = await integration.execute(
        config=incomplete_config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger,
    )

    print(
        f"Result with incomplete data: {'✅ EXPECTED ERROR' if not result_incomplete['response']['ok'] else '❌ UNEXPECTED SUCCESS'}"
    )
    print(f"Error message: {result_incomplete['response']['description']}")

    print("\n🎉 Все тесты завершены!")


if __name__ == "__main__":
    asyncio.run(test_yookassa_create_payment())
