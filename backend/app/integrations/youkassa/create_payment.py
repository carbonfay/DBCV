"""YooKassa Create Payment integration (HTTP, no SDK).

Creates a payment via POST https://api.yookassa.ru/v3/payments using Basic Auth
with shop_id/account_id and secret_key. Idempotence-Key is required; defaults
to a new UUID if not provided in config.
"""
from typing import Dict, Any
from uuid import UUID, uuid4
import base64
import http.client
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class YoukassaCreatePaymentIntegration(BaseIntegration):
    """Создание платежа в YooKassa через HTTP API (без SDK)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="youkassa_create_payment",
            version="1.0.0",
            name="YouKassa Create Payment",
            description="Создание платежа через HTTP API YooKassa",
            category="payments",
            icon_s3_key="icons/integrations/youkassa.svg",
            color="#ff6a00",
            config_schema={
                "type": "object",
                "required": ["amount"],
                "properties": {
                    "amount": {
                        "type": "object",
                        "required": ["value", "currency"],
                        "properties": {
                            "value": {"type": ["string", "number"], "title": "Amount", "description": "Сумма платежа (например, 100.00)"},
                            "currency": {"type": "string", "title": "Currency", "description": "Валюта (например, RUB)", "default": "RUB"},
                        },
                    },
                    "description": {"type": "string", "title": "Description", "description": "Описание платежа"},
                    "capture": {"type": "boolean", "title": "Capture", "description": "Автокапча (true=сразу снять, false=авторизация)", "default": True},
                    "payment_method_data": {"type": "object", "title": "Payment Method Data", "description": "Данные способа оплаты"},
                    "confirmation": {"type": "object", "title": "Confirmation", "description": "Способ подтверждения (redirect, code_inline, qr, external)"},
                    "receipt": {"type": "object", "title": "Receipt", "description": "Данные чека (items, customer, settlements)"},
                    "metadata": {"type": "object", "title": "Metadata", "description": "Произвольные метаданные"},
                    "idempotence_key": {"type": "string", "title": "Idempotence Key", "description": "Уникальный ключ запроса (auto-generate если не задан)"},
                },
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name=None,
            examples=[
                {
                    "title": "Создать платеж с редиректом (redirect)",
                    "config": {
                        "amount": {"value": "100.00", "currency": "RUB"},
                        "description": "Test payment",
                        "capture": True,
                        "confirmation": {"type": "redirect", "return_url": "https://example.com/return"},
                        "payment_method_data": {"type": "bank_card"}
                    },
                },
                {
                    "title": "Создать платеж (простой)",
                    "config": {
                        "amount": {"value": "50.00", "currency": "RUB"},
                        "description": "Simple payment",
                    },
                }
            ],
        )

    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger,
    ) -> Dict[str, Any]:
        """Создает платеж через HTTP API YooKassa."""

        amount = config.get("amount")
        if not amount or not isinstance(amount, dict) or not amount.get("value") or not amount.get("currency"):
            await logger.error("amount.value and amount.currency are required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "amount.value and amount.currency are required",
                }
            }

        # Получаем учетные данные
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key",
        )

        if not creds:
            await logger.error("YouKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YouKassa credentials not found",
                }
            }

        payload = creds.get("payload") if isinstance(creds, dict) else None
        if payload is None and isinstance(creds, dict):
            payload = creds

        if not isinstance(payload, dict):
            await logger.error("YouKassa credentials missing 'payload' dict")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Invalid credentials format: 'payload' dict is required",
                }
            }

        shop_id = str(payload.get("shop_id") or payload.get("account_id") or "").strip()
        secret_key = str(payload.get("secret_key") or payload.get("api_key") or "").strip()

        if not shop_id or not secret_key:
            safe_keys = sorted([k for k in payload.keys()])
            await logger.error(f"Missing shop_id/account_id or secret_key in payload; available keys={safe_keys}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YooKassa credentials missing 'shop_id/account_id' or 'secret_key' in payload",
                }
            }

        idempotence_key = str(config.get("idempotence_key") or uuid4())

        body: Dict[str, Any] = {
            "amount": amount,
            "capture": config.get("capture", True),
        }

        for key in ("description", "payment_method_data", "confirmation", "receipt", "metadata"):
            if key in config and config[key] is not None:
                value = config[key]
                # Не добавляем пустые объекты/массивы
                if isinstance(value, (dict, list)) and not value:
                    continue
                body[key] = value

        body_json = json.dumps(body, ensure_ascii=False).encode("utf-8")

        credentials_b64 = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials_b64}",
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence_key,
            "Accept": "application/json",
        }

        # Детальное логирование для диагностики
        await logger.debug(
            f"=== YooKassa Payment Create Request ==="
            f"\nURL: https://api.yookassa.ru/v3/payments"
            f"\nMethod: POST"
            f"\nShop ID: {shop_id}"
            f"\nIdempotence-Key: {idempotence_key}"
            f"\nRequest Body: {json.dumps(body, ensure_ascii=False, indent=2)}"
            f"\nHeaders: Content-Type={headers['Content-Type']}, Accept={headers['Accept']}"
        )

        conn = http.client.HTTPSConnection("api.yookassa.ru", 443, timeout=30)
        try:
            conn.request("POST", "/v3/payments", body=body_json, headers=headers)
            resp = conn.getresponse()
            data_raw = resp.read()
            status = resp.status
            response_headers = dict(resp.getheaders())

            await logger.debug(
                f"=== YooKassa Payment Create Response ==="
                f"\nStatus: {status} {resp.reason}"
                f"\nResponse Headers: {json.dumps(response_headers, ensure_ascii=False)}"
                f"\nRaw Response: {data_raw.decode('utf-8', errors='replace')}"
            )

            try:
                parsed = json.loads(data_raw.decode("utf-8"))
            except Exception as parse_err:
                await logger.error(f"Failed to parse JSON response: {parse_err}")
                parsed = {"error": "invalid_json", "raw": data_raw.decode("utf-8", errors="replace")}

            if 200 <= status < 300:
                payment_id = parsed.get("id")
                await logger.debug(f"✓ Payment created successfully: {payment_id}")
                return {
                    "response": {
                        "ok": True,
                        "result": parsed,
                        "_debug": {
                            "status": status,
                            "headers": response_headers,
                            "request_body": body,
                        }
                    }
                }

            error_code = parsed.get("code", "unknown_error")
            error_desc = parsed.get("description", str(parsed))
            await logger.error(
                f"✗ YooKassa payment create failed"
                f"\nStatus: {status}"
                f"\nError Code: {error_code}"
                f"\nDescription: {error_desc}"
                f"\nFull Response: {json.dumps(parsed, ensure_ascii=False, indent=2)}"
            )
            return {
                "response": {
                    "ok": False,
                    "error_code": status,
                    "description": error_desc,
                    "full_response": parsed,
                    "_debug": {
                        "status": status,
                        "headers": response_headers,
                        "request_body": body,
                    }
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error while creating payment: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e),
                }
            }
        finally:
            try:
                conn.close()
            except Exception:
                pass
