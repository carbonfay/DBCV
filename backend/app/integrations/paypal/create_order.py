"""PayPal Create Order интеграция используя httpx для прямых API вызовов."""
from typing import Dict, Any
from uuid import UUID
import httpx
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# httpx уже в requirements.txt, поэтому проверяем доступность
HTTPX_AVAILABLE = True


class PayPalCreateOrderIntegration(BaseIntegration):
    """Интеграция для создания заказа в PayPal."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_create_order",
            version="1.0.0",
            name="PayPal Create Order",
            description="Создание заказа в PayPal через Orders API",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#0070BA",
            config_schema={
                "type": "object",
                "required": ["purchase_units"],
                "properties": {
                    "intent": {
                        "type": "string",
                        "title": "Intent",
                        "description": "Намерение платежа",
                        "enum": ["CAPTURE", "AUTHORIZE"],
                        "default": "CAPTURE"
                    },
                    "purchase_units": {
                        "type": "array",
                        "title": "Purchase Units",
                        "description": "Единицы покупки (товары/услуги)",
                        "items": {
                            "type": "object",
                            "required": ["amount"],
                            "properties": {
                                "reference_id": {
                                    "type": "string",
                                    "title": "Reference ID",
                                    "description": "Ссылочный ID для идентификации этой единицы покупки"
                                },
                                "amount": {
                                    "type": "object",
                                    "title": "Amount",
                                    "description": "Сумма заказа",
                                    "required": ["currency_code", "value"],
                                    "properties": {
                                        "currency_code": {
                                            "type": "string",
                                            "title": "Currency Code",
                                            "description": "Код валюты",
                                            "default": "USD"
                                        },
                                        "value": {
                                            "type": "string",
                                            "title": "Value",
                                            "description": "Сумма в виде строки с двумя знаками после запятой"
                                        },
                                        "breakdown": {
                                            "type": "object",
                                            "title": "Breakdown",
                                            "description": "Разбивка суммы",
                                            "properties": {
                                                "item_total": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                },
                                                "tax_total": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                },
                                                "shipping": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                },
                                                "handling": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                },
                                                "insurance": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                },
                                                "shipping_discount": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                },
                                                "discount": {
                                                    "type": "object",
                                                    "properties": {
                                                        "currency_code": {
                                                            "type": "string"
                                                        },
                                                        "value": {
                                                            "type": "string"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "items": {
                                    "type": "array",
                                    "title": "Items",
                                    "description": "Список товаров",
                                    "items": {
                                        "type": "object",
                                        "required": ["name", "quantity", "unit_amount"],
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "title": "Name",
                                                "description": "Название товара"
                                            },
                                            "quantity": {
                                                "type": "string",
                                                "title": "Quantity",
                                                "description": "Количество в виде строки"
                                            },
                                            "unit_amount": {
                                                "type": "object",
                                                "title": "Unit Amount",
                                                "properties": {
                                                    "currency_code": {
                                                        "type": "string"
                                                    },
                                                    "value": {
                                                        "type": "string"
                                                    }
                                                }
                                            },
                                            "tax": {
                                                "type": "object",
                                                "title": "Tax",
                                                "properties": {
                                                    "currency_code": {
                                                        "type": "string"
                                                    },
                                                    "value": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "description": {
                                    "type": "string",
                                    "title": "Description",
                                    "description": "Описание единицы покупки"
                                },
                                "custom_id": {
                                    "type": "string",
                                    "title": "Custom ID",
                                    "description": "Пользовательский ID"
                                }
                            }
                        }
                    },
                    "application_context": {
                        "type": "object",
                        "title": "Application Context",
                        "description": "Контекст приложения для настройки UX",
                        "properties": {
                            "brand_name": {
                                "type": "string",
                                "title": "Brand Name",
                                "description": "Название бренда"
                            },
                            "locale": {
                                "type": "string",
                                "title": "Locale",
                                "description": "Языковой стандарт",
                                "default": "en-US"
                            },
                            "landing_page": {
                                "type": "string",
                                "title": "Landing Page",
                                "description": "Страница входа в PayPal",
                                "enum": ["LOGIN", "BILLING"]
                            },
                            "shipping_preference": {
                                "type": "string",
                                "title": "Shipping Preference",
                                "description": "Предпочтения доставки",
                                "enum": ["GET_FROM_FILE", "NO_SHIPPING", "SET_PROVIDED_ADDRESS"]
                            },
                            "user_action": {
                                "type": "string",
                                "title": "User Action",
                                "description": "Действие пользователя",
                                "enum": ["CONTINUE", "PAY_NOW"]
                            },
                            "return_url": {
                                "type": "string",
                                "title": "Return URL",
                                "description": "URL для возврата после оплаты"
                            },
                            "cancel_url": {
                                "type": "string",
                                "title": "Cancel URL",
                                "description": "URL для отмены"
                            }
                        }
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="api_key",
            library_name="httpx" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Создать заказ на 100 USD",
                    "config": {
                        "purchase_units": [
                            {
                                "amount": {
                                    "currency_code": "USD",
                                    "value": "100.00"
                                }
                            }
                        ],
                        "application_context": {
                            "user_action": "PAY_NOW",
                            "return_url": "{$bot.return_url$}",
                            "cancel_url": "{$bot.cancel_url$}"
                        }
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

        # Получаем параметры из config
        intent = config.get("intent", "CAPTURE")
        purchase_units = config.get("purchase_units", [])
        application_context = config.get("application_context", {})

        if not purchase_units:
            await logger.error("purchase_units is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "purchase_units is required"
                }
            }

        # ИСПОЛЬЗУЕМ httpx НАПРЯМУЮ
        try:
            # Подготовим тело запроса
            order_data = {
                "intent": intent,
                "purchase_units": purchase_units
            }

            if application_context:
                order_data["application_context"] = application_context

            # Определяем URL и headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            url = "https://api.sandbox.paypal.com/v2/checkout/orders"

            # Выполняем POST-запрос
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=order_data, headers=headers)

            # Проверяем статус ответа
            if response.status_code not in [200, 201]:
                await logger.error(f"PayPal Orders API returned status {response.status_code}: {response.text}")
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

