"""Bitrix24: GetDeal integration (crm.deal.get).

Использует внешнюю библиотеку `bitrix24` если она установлена. Возвращает
сделку по её ID.
"""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

import httpx




class Bitrix24GetDealIntegration(BaseIntegration):
    """Интеграция Bitrix24: получение сделки (crm.deal.get).

    Эта реализация пытается использовать библиотеку `bitrix24` напрямую.
    Если библиотека отсутствует, возвращается ошибка с подсказкой установить
    соответствующий пакет.
    """

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="bitrix24_getdeal",
            version="1.0.0",
            name="Bitrix24 Get Deal",
            description="Получение сделки из Bitrix24 (crm.deal.get)",
            category="crm",
            icon_s3_key="icons/integrations/bitrix24.svg",
            color="#2b7bb9",
            config_schema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {
                        "type": "integer",
                        "title": "Deal ID",
                        "description": "Идентификатор сделки (ID)"
                    }
                }
            },
            credentials_provider="other",
            # Bitrix24 может работать через OAuth или Webhook/API key —
            # указываем наиболее частую стратегию OAuth (внешний токен).
            credentials_strategy="oauth",
            library_name=None,
            examples=[
                {
                    "title": "Получить сделку по ID",
                    "config": {"id": 123}
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
        """Выполнить вызов crm.deal.get используя библиотеку bitrix24.

        Ожидается, что credentials содержат расшифрованный payload с полями,
        например: {
            "domain": "your-domain.bitrix24.ru",
            "access_token": "...",
            # либо
            "webhook_url": "https://.../rest/USER_ID/WEBHOOK_KEY/"
        }
        """
        # Получаем credentials: пробуем сначала strategy из метаданных, затем fallback
        strategy = self.metadata.credentials_strategy or "oauth"
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="other",
            strategy=strategy
        )

        if not creds:
            # Попытка fallback на api_key
            creds = await credentials_resolver.get_default_for(
                bot_id=bot_id,
                provider="other",
                strategy="oauth"
            )

        if not creds:
            await logger.error("Bitrix24 credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "Bitrix24 credentials not found"
                }
            }

        payload = creds.get("payload", {}) if isinstance(creds, dict) else {}
        if not payload:
            # backward compatibility: если payload нет — использовать корень
            payload = creds

        deal_id = config.get("id")
        if deal_id is None:
            await logger.error("config.id (deal id) is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "config.id (deal id) is required"
                }
            }

        # Попытки выполнить вызов через webhook_url или через domain+access_token
        webhook_url = payload.get("webhook_url") or payload.get("webhook")
        domain = payload.get("domain") or payload.get("base_url") or payload.get("url")
        access_token = payload.get("access_token") or payload.get("token") or payload.get("accessToken")

        async def _try_webhook(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
            """Попытка вызвать webhook-путь: POST {webhook}/crm.deal.get с json {'ID': id} """
            try:
                url = url.rstrip('/') + '/crm.deal.get'
                resp = await client.post(url, json={"ID": int(deal_id)})
                resp.raise_for_status()
                try:
                    return {"ok": True, "result": resp.json()}
                except Exception:
                    return {"ok": True, "result": resp.text}
            except Exception as e:
                await logger.error(f"Bitrix24 webhook call failed: {e}")
                return {"ok": False, "error": str(e)}

        async def _try_domain_token(client: httpx.AsyncClient, domain: str, token: str) -> Dict[str, Any]:
            """Попытка вызвать REST API через domain + auth token.

            Пробуем GET {domain}/rest/crm.deal.get.json?auth=token&ID=... затем POST fallback.
            """
            try:
                base = domain.rstrip('/')
                if not base.startswith('http'):
                    base = 'https://' + base

                # 1) GET to .json endpoint
                url = f"{base}/rest/crm.deal.get.json"
                params = {"auth": token, "ID": int(deal_id)}
                resp = await client.get(url, params=params)
                if resp.status_code >= 200 and resp.status_code < 300:
                    try:
                        return {"ok": True, "result": resp.json()}
                    except Exception:
                        return {"ok": True, "result": resp.text}

                # 2) POST fallback
                url2 = f"{base}/rest/crm.deal.get"
                resp2 = await client.post(url2, json={"auth": token, "ID": int(deal_id)})
                resp2.raise_for_status()
                try:
                    return {"ok": True, "result": resp2.json()}
                except Exception:
                    return {"ok": True, "result": resp2.text}

            except Exception as e:
                await logger.error(f"Bitrix24 domain/token call failed: {e}")
                return {"ok": False, "error": str(e)}

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1) Try webhook if provided
            if webhook_url:
                res = await _try_webhook(client, webhook_url)
                if res.get("ok"):
                    return {"response": {"ok": True, "result": res.get("result")}}

            # 2) Try domain + token
            if domain and access_token:
                res = await _try_domain_token(client, domain, access_token)
                if res.get("ok"):
                    return {"response": {"ok": True, "result": res.get("result")}}

        # Если ничего не сработало — вернуть ошибку
        await logger.error("Unable to call Bitrix24: no working endpoint or token")
        return {
            "response": {
                "ok": False,
                "error_code": 500,
                "description": "Unable to call Bitrix24: no working endpoint or token"
            }
        }
