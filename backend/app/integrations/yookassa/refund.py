from typing import Dict, Any
from uuid import UUID, uuid4

import json
import base64
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class YooKassaRefundIntegration(BaseIntegration):

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa.refund",
            version="1.0.0",
            name="YooKassa: Refund payment",
            description="Создает возврат по платежу в YooKassa.",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#00A3E0",
            config_schema={
                "type": "object",
                "required": ["payment_id", "amount"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "Идентификатор платежа в YooKassa.",
                    },
                    "amount": {
                        "type": "number",
                        "title": "Amount",
                        "description": "Сумма возврата (дробное число, например 10.50).",
                    },
                    "currency": {
                        "type": "string",
                        "title": "Currency",
                        "description": "Код валюты в формате ISO 4217 (по умолчанию RUB).",
                        "default": "RUB",
                    },
                    "description": {
                        "type": "string",
                        "title": "Description",
                        "description": "Комментарий к возврату.",
                    },
                    "idempotence_key": {
                        "type": "string",
                        "title": "Idempotence key",
                        "description": "Ключ идемпотентности запроса. Если не указан, будет сгенерирован автоматически.",
                    },
                },
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name="httpx>=0.24.0",
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """
        Ожидаем, что credentials.payload содержит:
        {
            "shop_id": "...",
            "secret_key": "..."
        }
        и хранятся как provider=other, strategy=api_key.
        """
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key",
        )

        if not creds:
            await logger.error("YooKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials not found",
                }
            }

        payload = creds.get("payload") or creds
        shop_id = payload.get("shop_id")
        secret_key = payload.get("secret_key")

        if not shop_id or not secret_key:
            await logger.error(
                f"YooKassa credentials are invalid. "
                f"Expected shop_id and secret_key, got keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials must contain shop_id and secret_key",
                }
            }

        payment_id = config.get("payment_id")
        amount_value = config.get("amount")
        currency = config.get("currency") or "RUB"
        description = config.get("description")
        idempotence_key = config.get("idempotence_key") or str(uuid4())

        if not payment_id:
            await logger.error("payment_id is required for refund")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required",
                }
            }

        if amount_value is None:
            await logger.error("amount is required for refund")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount is required",
                }
            }

        api_url = "https://api.yookassa.ru/v3/refunds"

        body: Dict[str, Any] = {
            "payment_id": payment_id,
            "amount": {
                "value": f"{amount_value:.2f}",
                "currency": currency,
            },
        }
        if description:
            body["description"] = description

        basic_auth_bytes = f"{shop_id}:{secret_key}".encode("utf-8")
        basic_auth = base64.b64encode(basic_auth_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Idempotence-Key": idempotence_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(api_url, json=body, headers=headers)

            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "response": {
                        "ok": True,
                        "result": data,
                    }
                }

            try:
                error_data = response.json()
            except json.JSONDecodeError:
                error_data = {"message": response.text}

            await logger.error(
                f"YooKassa refund API error: {response.status_code} {error_data}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": response.status_code,
                    "description": error_data.get("message")
                    or "YooKassa refund API error",
                    "details": error_data,
                }
            }

        except httpx.RequestError as exc:
            await logger.error(f"YooKassa refund request error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"YooKassa refund request error: {exc}",
                }
            }
        except Exception as exc:  # noqa: BLE001
            await logger.error(f"Unexpected YooKassa refund integration error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(exc),
                }
            }
