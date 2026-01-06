from typing import Dict, Any
from uuid import UUID
from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger
import requests  # Для выполнения HTTP-запросов

class YookassaRefundIntegration(BaseIntegration):
    """Интеграция для возврата средств через YooKassa."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa_refund",
            version="1.0.0",
            name="YooKassa Refund",
            description="Выполнение возврата средств через API YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#4CAF50",
            config_schema={
                "type": "object",
                "required": ["shop_id", "secret_key", "payment_id", "amount"],
                "properties": {
                    "shop_id": {
                        "type": "string",
                        "title": "YooKassa Shop ID"
                    },
                    "secret_key": {
                        "type": "string",
                        "title": "YooKassa Secret Key"
                    },
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID"
                    },
                    "amount": {
                        "type": "number",
                        "title": "Amount"
                    }
                }
            },
            credentials_provider="yookassa",
            credentials_strategy="api_key",
            examples=[{
                "title": "Простой возврат",
                "config": {
                    "shop_id": "your_shop_id",
                    "secret_key": "your_secret_key",
                    "payment_id": "payment_id_to_refund",
                    "amount": 1000
                }
            }]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет возврат средств через API YooKassa.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """

        # Получаем креды
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="yookassa",
            strategy="api_key"
        )

        if not creds:
            await logger.error("YooKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials not found"
                }
            }

        shop_id = creds.get("payload", {}).get("shop_id")
        secret_key = creds.get("payload", {}).get("secret_key")

        # Получаем параметры из конфигурации
        payment_id = config.get("payment_id")
        amount = config.get("amount")

        if not shop_id or not secret_key:
            await logger.error("Invalid credentials")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Invalid YooKassa credentials"
                }
            }

        if not payment_id or not amount:
            await logger.error("payment_id and amount are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id and amount are required"
                }
            }

        # Формируем запрос к API YooKassa для возврата средств
        url = f"https://api.yookassa.ru/v3/payments/{payment_id}/refunds"
        headers = {
            "Authorization": f"Basic {secret_key}"
        }
        payload = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                return {
                    "response": {
                        "ok": True,
                        "result": response_data
                    }
                }
            else:
                await logger.error(f"Error in YooKassa refund: {response_data}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": response_data.get("description", "Unknown error")
                    }
                }
        except Exception as e:
            await logger.error(f"Unexpected error: {str(e)}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }
