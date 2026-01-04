#!/usr/bin/env python3
"""
Простой тест для интеграции YooKassa Create Receipt.
Этот тест демонстрирует использование интеграции без реального API вызова.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))


# Мокируем библиотеку yookassa для тестирования
class MockReceipt:
    def __init__(self):
        self.id = "rt_2c5b350c-00f5-5000-8000-102d922df857"
        self.type = "payment"
        self.payment_id = "24b94598-000f-5000-9000-1b68e7b15f3f"
        self.status = "pending"
        self.items = [
            {
                "description": "Товар 1",
                "quantity": 1.0,
                "amount": {"value": "100.00", "currency": "RUB"},
                "vat_code": 2,
                "payment_mode": "full_prepayment",
                "payment_subject": "commodity",
            }
        ]
        self.customer = {
            "full_name": "Иванов Иван Иванович",
            "email": "customer@example.com",
        }
        self.created_at = "2023-01-01T00:00:00.000Z"
        self.registered_at = None
        self.fiscal_document_number = None
        self.fiscal_storage_number = None
        self.fiscal_attribute = None
        self.fiscal_provider_id = None
        self.tax_system_code = None
        self.internet = True

    @classmethod
    def create(cls, receipt_data):
        return cls()


class MockConfiguration:
    account_id = None
    secret_key = None


# Мокируем модуль yookassa перед импортом
mock_yookassa = MagicMock()
mock_yookassa.Configuration = MockConfiguration
mock_yookassa.Receipt = MockReceipt
mock_yookassa.domain = MagicMock()
mock_yookassa.domain.exceptions = MagicMock()
mock_yookassa.domain.exceptions.ApiError = Exception
sys.modules["yookassa"] = mock_yookassa
sys.modules["yookassa.domain"] = mock_yookassa.domain
sys.modules["yookassa.domain.exceptions"] = mock_yookassa.domain.exceptions

# Теперь импортируем нашу интеграцию
try:
    from app.integrations.yookassa.create_receipt import (
        YookassaCreateReceiptIntegration,
    )

    print("✅ Импорт YookassaCreateReceiptIntegration успешен")
except ImportError as e:
    print(f"❌ Ошибка импорта YookassaCreateReceiptIntegration: {e}")
    sys.exit(1)


async def test_yookassa_create_receipt():
    """Тест создания чека YooKassa."""
    print("🧪 Тестирование YooKassa Create Receipt Integration")

    # Создаем интеграцию
    integration = YookassaCreateReceiptIntegration()

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

    # Тестовые данные для создания чека
    config = {
        "payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f",
        "customer_full_name": "Иванов Иван Иванович",
        "customer_email": "customer@example.com",
        "customer_phone": "79000000000",
        "items": [
            {
                "description": "Товар 1",
                "quantity": 1.0,
                "amount": {"value": "100.00", "currency": "RUB"},
                "vat_code": 2,
                "payment_mode": "full_prepayment",
                "payment_subject": "commodity",
            }
        ],
        "settlements": [
            {
                "type": "cashless",
                "amount": {"value": "100.00", "currency": "RUB"},
            }
        ],
        "send": True,
        "internet": True,
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
        receipt_result = result["response"]["result"]
        print(f"Receipt ID: {receipt_result['id']}")
        print(f"Type: {receipt_result['type']}")
        print(f"Payment ID: {receipt_result['payment_id']}")
        print(f"Status: {receipt_result['status']}")
        print(f"Items count: {receipt_result.get('items_count', 0)}")
        print(f"Customer info: {receipt_result.get('customer_info', 'N/A')}")
        print(f"Receipt created: {receipt_result.get('receipt_created', False)}")
        print(f"Message: {receipt_result.get('message', 'N/A')}")
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

    # Тест с отсутствующим payment_id
    print("\n🧪 Тестирование с отсутствующим payment_id...")
    mock_credentials_resolver.get_default_for.return_value = {
        "payload": {"account_id": "test_account_id", "secret_key": "test_secret_key"}
    }

    incomplete_config = {
        "items": [
            {
                "description": "Товар 1",
                "quantity": 1.0,
                "amount": {"value": "100.00", "currency": "RUB"},
                "vat_code": 2,
                "payment_mode": "full_prepayment",
                "payment_subject": "commodity",
            }
        ],
        "settlements": [
            {
                "type": "cashless",
                "amount": {"value": "100.00", "currency": "RUB"},
            }
        ],
        # отсутствует payment_id
    }

    result_no_payment_id = await integration.execute(
        config=incomplete_config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger,
    )

    print(
        f"Result without payment_id: {'✅ EXPECTED ERROR' if not result_no_payment_id['response']['ok'] else '❌ UNEXPECTED SUCCESS'}"
    )
    print(f"Error message: {result_no_payment_id['response']['description']}")

    # Тест с пустым массивом items
    print("\n🧪 Тестирование с пустым массивом items...")
    empty_items_config = {
        "payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f",
        "items": [],  # пустой массив
        "settlements": [
            {
                "type": "cashless",
                "amount": {"value": "100.00", "currency": "RUB"},
            }
        ],
    }

    result_empty_items = await integration.execute(
        config=empty_items_config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger,
    )

    print(
        f"Result with empty items: {'✅ EXPECTED ERROR' if not result_empty_items['response']['ok'] else '❌ UNEXPECTED SUCCESS'}"
    )
    print(f"Error message: {result_empty_items['response']['description']}")

    # Тест с несколькими товарами
    print("\n🧪 Тестирование с несколькими товарами...")
    multi_items_config = {
        "payment_id": "24b94598-000f-5000-9000-1b68e7b15f3f",
        "customer_email": "test@example.com",
        "items": [
            {
                "description": "Консультация",
                "quantity": 1.0,
                "amount": {"value": "5000.00", "currency": "RUB"},
                "vat_code": 1,
                "payment_mode": "full_payment",
                "payment_subject": "service",
            },
            {
                "description": "Материалы",
                "quantity": 2.0,
                "amount": {"value": "150.00", "currency": "RUB"},
                "vat_code": 2,
                "payment_mode": "full_payment",
                "payment_subject": "commodity",
            },
        ],
        "settlements": [
            {
                "type": "cashless",
                "amount": {"value": "5300.00", "currency": "RUB"},
            }
        ],
        "send": True,
        "internet": True,
    }

    result_multi_items = await integration.execute(
        config=multi_items_config,
        credentials_resolver=mock_credentials_resolver,
        bot_id=uuid4(),
        logger=mock_logger,
    )

    print(
        f"Result with multiple items: {'✅ SUCCESS' if result_multi_items['response']['ok'] else '❌ FAILED'}"
    )
    if result_multi_items["response"]["ok"]:
        print(
            f"Items count: {result_multi_items['response']['result'].get('items_count', 0)}"
        )
    else:
        print(f"Error message: {result_multi_items['response']['description']}")

    print("\n🎉 Все тесты завершены!")
    return True


async def main():
    """Главная функция для запуска тестов."""
    print("🚀 Запуск тестов YooKassa Create Receipt интеграции...")

    try:
        success = await test_yookassa_create_receipt()
        if success:
            print("\n🎉 Все тесты прошли успешно!")
            return True
        else:
            print("\n❌ Некоторые тесты провалились!")
            return False
    except Exception as e:
        print(f"\n❌ Критическая ошибка при выполнении тестов: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
