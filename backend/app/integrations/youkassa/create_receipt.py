"""YooKassa Create Receipt integration (HTTP-only, no SDK).

Отправляет HTTP POST на https://api.yookassa.ru/v3/receipts с basic-auth
по shop_id/account_id и secret_key. Требуется idempotence-key (используем
payment_id, если не передан idempotence_key в конфиге).
"""
from typing import Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal, InvalidOperation
import base64
import http.client
import json

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger


class YoukassaCreateReceiptIntegration(BaseIntegration):
    """Создание чека (receipt) в YooKassa через HTTP API (без SDK)."""

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="youkassa_create_receipt",
            version="1.0.0",
            name="YouKassa Create Receipt",
            description="Создание фискального чека через YooKassa SDK",
            category="payments",
            icon_s3_key="icons/integrations/youkassa.svg",
            color="#ff6a00",
            config_schema={
                "type": "object",
                "required": ["payment_id", "items"],
                "properties": {
                    "payment_id": {"type": "string", "title": "Payment ID", "description": "ID платежа, для которого формируется чек"},
                    "type": {"type": "string", "title": "Type", "description": "Тип чека: payment/refund"},
                    "send": {"type": "boolean", "title": "Send to customer", "description": "Отправить чек клиенту"},
                    "customer": {"type": "object", "title": "Customer", "description": "Данные покупателя"},
                    "items": {
                        "type": "array",
                        "items": {"type": "object"},
                        "title": "Items",
                        "description": "Список позиций"
                    },
                    "settlements": {
                        "type": "array",
                        "items": {"type": "object"},
                        "title": "Settlements",
                        "description": "Данные расчётов (например, наличные/безналичные)"
                    }
                }
            },
            credentials_provider="other",
            credentials_strategy="api_key",
            library_name=None,
            examples=[
                {
                    "title": "Создать чек для платежа",
                    "config": {
                        "payment_id": "21b23b5b-000f-5061-a000-0674e49a8c10",
                        "type": "payment",
                        "send": True,
                        "items": [
                            {
                                "description": "Product 1",
                                "quantity": 1,
                                "amount": {"value": "100.00", "currency": "RUB"},
                                "vat_code": "2",
                                "payment_mode": "full_payment",
                                "payment_subject": "commodity"
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
        """Создает чек через HTTP API YooKassa.

        Args:
            config: Параметры для создания чека
            credentials_resolver: Резолвер учетных данных
            bot_id: ID бота
            logger: Логгер

        Returns:
            Результат выполнения: успех или ошибка
        """

        payment_id = config.get("payment_id")
        items = config.get("items")
        if not payment_id:
            await logger.error("payment_id is required to create a receipt")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payment_id is required"
                }
            }
        if not items:
            await logger.error("items are required to create a receipt")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "items are required"
                }
            }

        await logger.debug(
            f"Receipt create request: payment_id={payment_id}, "
            f"items_type={type(items)}, has_items={bool(items)}, config_keys={list(config.keys())}"
        )

        # Получаем учетные данные
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy="api_key"
        )

        if not creds:
            await logger.error("YouKassa credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "YouKassa credentials not found"
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
                    "description": "Invalid credentials format: 'payload' dict is required"
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
                    "description": "YooKassa credentials missing 'shop_id/account_id' or 'secret_key' in payload"
                }
            }

        # Формируем HTTP запрос
        idempotence_key = str(config.get("idempotence_key") or uuid4())

        # Если settlements не переданы, вычислим сумму по items и подставим по умолчанию
        settlements = config.get("settlements")
        if not settlements:
            total_value: Decimal | None = None
            currency: str | None = None
            try:
                for i in items:
                    amt = i.get("amount") if isinstance(i, dict) else None
                    if isinstance(amt, dict):
                        val = amt.get("value")
                        cur = amt.get("currency")
                        if val is not None:
                            dval = Decimal(str(val))
                            total_value = dval if total_value is None else (total_value + dval)
                        if currency is None and cur:
                            currency = str(cur)
            except (InvalidOperation, Exception) as e:
                await logger.error(f"Failed to compute settlements total from items: {e}")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "Invalid item amounts: unable to compute settlements total",
                    }
                }

            if total_value is None or currency is None:
                await logger.error("settlements are missing and cannot be auto-computed: items lack amount/currency")
                return {
                    "response": {
                        "ok": False,
                        "error_code": 400,
                        "description": "Missing settlements and items.amount/currency to compute default",
                    }
                }

            settlements = [
                {
                    "type": "cashless",
                    "amount": {"value": f"{total_value:.2f}", "currency": currency},
                }
            ]

            await logger.debug(
                f"Auto-applied settlements: total={total_value} {currency}, type=cashless"
            )

        body = {
            "payment_id": payment_id,
            "type": config.get("type") or "payment",
            "send": config.get("send", True),
            "items": items,
        }

        # Пробрасываем опциональные поля, если заданы
        for optional_key in ("customer", "tax_system_code", "receipt_industry_details", "receipt_operating_details"):
            if optional_key in config and config[optional_key] is not None:
                body[optional_key] = config[optional_key]

        # Всегда добавляем рассчитанные или переданные settlements
        body["settlements"] = settlements

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
            f"=== YooKassa Receipt Create Request ==="
            f"\nURL: https://api.yookassa.ru/v3/receipts"
            f"\nMethod: POST"
            f"\nShop ID: {shop_id}"
            f"\nIdempotence-Key: {idempotence_key}"
            f"\nRequest Body: {json.dumps(body, ensure_ascii=False, indent=2)}"
            f"\nHeaders: Content-Type={headers['Content-Type']}, Accept={headers['Accept']}"
        )

        conn = http.client.HTTPSConnection("api.yookassa.ru", 443, timeout=30)
        try:
            conn.request("POST", "/v3/receipts", body=body_json, headers=headers)
            resp = conn.getresponse()
            data_raw = resp.read()
            status = resp.status
            response_headers = dict(resp.getheaders())

            await logger.debug(
                f"=== YooKassa Receipt Create Response ==="
                f"\nStatus: {status} {resp.reason}"
                f"\nResponse Headers: {json.dumps(response_headers, ensure_ascii=False)}"
                f"\nRaw Response: {data_raw.decode('utf-8', errors='replace')}"
            )

            # Пытаемся распарсить JSON
            parsed = None
            try:
                parsed = json.loads(data_raw.decode("utf-8"))
            except Exception as parse_err:
                await logger.error(f"Failed to parse JSON response: {parse_err}")
                parsed = {"error": "invalid_json", "raw": data_raw.decode("utf-8", errors="replace")}

            if 200 <= status < 300:
                await logger.debug(f"✓ Receipt created successfully")
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

            error_code = parsed.get("code") if isinstance(parsed, dict) else "unknown_error"
            error_desc = parsed.get("description") if isinstance(parsed, dict) else str(parsed)
            await logger.error(
                f"✗ YooKassa receipt create failed"
                f"\nStatus: {status}"
                f"\nError Code: {error_code}"
                f"\nDescription: {error_desc}"
                f"\nFull Response: {json.dumps(parsed, ensure_ascii=False, indent=2) if isinstance(parsed, dict) else parsed}"
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
            await logger.error(f"Unexpected error while creating receipt: {e}")
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
