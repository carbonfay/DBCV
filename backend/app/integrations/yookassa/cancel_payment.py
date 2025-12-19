from typing import Dict, Any
from uuid import UUID

import json
import base64
import httpx

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class YooKassaCancelPaymentIntegration(BaseIntegration):

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="yookassa.cancel_payment",
            version="1.0.0",
            name="YooKassa: Cancel payment",
            description="Отменяет платёж в YooKassa по идентификатору платежа.",
            category="payments",
            icon_s3_key="icons/integrations/yookassa.svg",
            color="#00A3E0",
            config_schema={
                "type": "object",
                "required": ["payment_id"],
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "title": "Payment ID",
                        "description": "Идентификатор платежа в YooKassa.",
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
        secret_key = payload.get("secret_key") or payload.get("api_key")

        if not shop_id or not secret_key:
            await logger.error(
                f"YooKassa credentials invalid, expected shop_id and secret_key/api_key, "
                f"got keys: {list(payload.keys())}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": (
                        "Invalid YooKassa credentials: shop_id and secret_key/api_key are required"
                    ),
                }
            }

        # 2. Разбираем конфиг
        payment_id = config.get("payment_id")
        reason = config.get("reason")
        idempotence_key = config.get("idempotence_key")

        if not payment_id:
            await logger.error("YooKassa payment_id is required in config")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required",
                }
            }

        if not idempotence_key:
            from uuid import uuid4

            idempotence_key = str(uuid4())

        # 3. Формируем запрос к YooKassa
        auth_bytes = f"{shop_id}:{secret_key}".encode("utf-8")
        auth_header = base64.b64encode(auth_bytes).decode("ascii")

        url = f"https://api.yookassa.ru/v3/payments/{payment_id}/cancel"

        body: Dict[str, Any] = {}
        if reason:
            body["description"] = reason

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Idempotence-Key": idempotence_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=body, headers=headers)

            try:
                data = response.json()
            except json.JSONDecodeError:
                data = {"raw": response.text}

            if response.status_code in (200, 201):
                return {
                    "response": {
                        "ok": True,
                        "status": data.get("status"),
                        "id": data.get("id"),
                        "payment_id": payment_id,
                        "raw": data,
                    }
                }

            await logger.error(
                f"YooKassa cancel_payment error: {response.status_code} {data}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": response.status_code,
                    "description": (
                        data.get("description")
                        or data.get("message")
                        or "YooKassa cancel payment error"
                    ),
                    "details": data,
                }
            }

        except httpx.RequestError as exc:
            await logger.error(f"YooKassa HTTP error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"YooKassa request error: {exc}",
                }
            }
        except Exception as exc:
            await logger.error(f"Unexpected YooKassa cancel_payment error: {exc}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(exc),
                }
            }
