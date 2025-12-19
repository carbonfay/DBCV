"""PayPal Create Payout интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class PayPalCreatePayoutIntegration(BaseIntegration):
    """Интеграция для создания выплаты в PayPal."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_create_payout",
            version="1.0.0",
            name="PayPal Create Payout",
            description="Создание выплаты в PayPal через Payouts API",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#0070BA",
            config_schema={
                "type": "object",
                "required": ["sender_batch_header", "items"],
                "properties": {
                    "sender_batch_header": {
                        "type": "object",
                        "title": "Sender Batch Header",
                        "description": "Заголовок пакета отправителя",
                        "required": ["sender_batch_id", "email_subject"],
                        "properties": {
                            "sender_batch_id": {
                                "type": "string",
                                "title": "Sender Batch ID",
                                "description": "Уникальный ID для пакета транзакций"
                            },
                            "email_subject": {
                                "type": "string",
                                "title": "Email Subject",
                                "description": "Тема email для получателей"
                            },
                            "email_message": {
                                "type": "string",
                                "title": "Email Message",
                                "description": "Сообщение email для получателей"
                            }
                        }
                    },
                    "items": {
                        "type": "array",
                        "title": "Payout Items",
                        "description": "Элементы выплаты",
                        "items": {
                            "type": "object",
                            "required": ["recipient_type", "amount", "note"],
                            "properties": {
                                "recipient_type": {
                                    "type": "string",
                                    "title": "Recipient Type",
                                    "description": "Тип получателя",
                                    "enum": ["EMAIL", "PHONE", "PAYPAL_ID"],
                                    "default": "EMAIL"
                                },
                                "recipient_wallet": {
                                    "type": "string",
                                    "title": "Recipient Wallet",
                                    "description": "Кошелек получателя (email, телефон или ID)"
                                },
                                "amount": {
                                    "type": "object",
                                    "title": "Amount",
                                    "required": ["value", "currency"],
                                    "properties": {
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Сумма выплаты"
                                        },
                                        "currency": {
                                            "type": "string",
                                            "title": "Currency",
                                            "description": "Валюта",
                                            "default": "USD"
                                        }
                                    }
                                },
                                "note": {
                                    "type": "string",
                                    "title": "Note",
                                    "description": "Примечание к выплате"
                                },
                                "sender_item_id": {
                                    "type": "string",
                                    "title": "Sender Item ID",
                                    "description": "Уникальный ID для элемента выплаты"
                                }
                            }
                        }
                    },
                    "sync_mode": {
                        "type": "boolean",
                        "title": "Sync Mode",
                        "description": "Режим синхронной обработки",
                        "default": False
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="api_key",  # Actually uses OAuth2 client credentials
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать выплату по email",
                    "config": {
                        "sender_batch_header": {
                            "sender_batch_id": "batch_123456",
                            "email_subject": "Выплата от компании"
                        },
                        "items": [
                            {
                                "recipient_type": "EMAIL",
                                "recipient_wallet": "recipient@example.com",
                                "amount": {
                                    "value": "100.00",
                                    "currency": "USD"
                                },
                                "note": "Выплата за выполненные работы"
                            }
                        ]
                    }
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя httpx для прямых вызовов PayPal API.

        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер

        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not available"
                }
            }

        # Получаем OAuth2 данные из credentials
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="paypal",
            strategy="api_key"
        )

        if not creds:
            await logger.error("PayPal credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "PayPal credentials not found in credentials"
                }
            }

        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds

        # Получаем OAuth2 данные (client_id и client_secret или access_token)
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        access_token = payload.get("access_token")

        if not (client_id and client_secret) and not access_token:
            await logger.error(f"PayPal client credentials not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "PayPal client_id and client_secret or access_token are required"
                }
            }

        # Получаем параметры из config
        sender_batch_header = config.get("sender_batch_header")
        items = config.get("items")
        sync_mode = config.get("sync_mode", False)

        if not sender_batch_header or not items:
            await logger.error("sender_batch_header and items are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "sender_batch_header and items are required"
                }
            }

        # Если access_token не предоставлен, нужно получить его через OAuth2
        if not access_token:
            try:
                # Получаем токен доступа
                async with httpx.AsyncClient() as token_client:
                    token_response = await token_client.post(
                        "https://api.sandbox.paypal.com/v1/oauth2/token",
                        auth=(client_id, client_secret),
                        data={"grant_type": "client_credentials"},
                        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
                    )

                    if token_response.status_code != 200:
                        await logger.error(f"PayPal token request failed: {token_response.status_code} - {token_response.text}")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": token_response.status_code,
                                "description": f"Failed to get PayPal access token: {token_response.text}"
                            }
                        }

                    token_data = token_response.json()
                    access_token = token_data.get("access_token")

                    if not access_token:
                        await logger.error("Failed to get PayPal access token")
                        return {
                            "response": {
                                "ok": False,
                                "error_code": 500,
                                "description": "Failed to get PayPal access token"
                            }
                        }
            except Exception as e:
                await logger.error(f"Error getting PayPal access token: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 500,
                        "description": f"Error getting PayPal access token: {str(e)}"
                    }
                }

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Подготовим тело запроса
            payout_data = {
                "sender_batch_header": sender_batch_header,
                "items": items
            }

            # Определяем URL в зависимости от режима
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "PayPal-Request-Id": sender_batch_header.get("sender_batch_id", "default_request_id")
            }

            # Определяем endpoint - для синхронного режима добавляем параметр
            url = "https://api.sandbox.paypal.com/v1/payments/payouts"
            if sync_mode:
                url += "?sync_mode=true"

            # Выполняем POST-запрос
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payout_data, headers=headers)

            # Проверяем статус ответа
            if response.status_code not in [200, 201]:
                await logger.error(f"PayPal Payouts API returned status {response.status_code}: {response.text}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": response.status_code,
                        "description": f"PayPal API returned status {response.status_code}: {response.text}"
                    }
                }

            # Парсим JSON-ответ
            data = response.json()

            # Возвращаем результат в формате системы
            return {
                "response": {
                    "ok": True,
                    "result": data
                }
            }
        except httpx.RequestError as e:
            await logger.error(f"HTTP request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"HTTP request error: {e}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

