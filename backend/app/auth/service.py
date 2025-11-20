import uuid
from urllib.parse import urlparse
from typing import Mapping, Any, Optional

from app.auth.cache import TokenCache
from app.auth.providers.google_provider import GoogleProvider
from app.auth.providers.amocrm_provider import AmoCrmProvider
from app.auth.providers.yandex_provider import YandexCloudProvider, YandexIdOAuthProvider


class AuthService:
    def __init__(self, resolver):
        self._resolver = resolver
        self._cache = TokenCache()
        self._providers = {
            "google": GoogleProvider(),
            "amocrm": AmoCrmProvider(),
            "yandex_cloud": YandexCloudProvider(),
            "yandex_id": YandexIdOAuthProvider(),
        }

    async def apply(
        self,
        *,
        bot_id: str,
        headers: dict,
        request_url: str,
        credentials_id: Optional[str] = None,   # явный override (не обязательно)
        strategy_hint: Optional[str] = None,    # "service_account" | "oauth"
        provider_hint: Optional[str] = None,
        profile: str = "default",
        hints: Mapping[str, Any] = {},
    ) -> None:
        provider_key, prov_hints = self._detect_provider(request_url, provider_hint, hints)
        if not provider_key:
            return

        # 1) если передан явный ID — берём его
        if credentials_id:
            secret = await self._resolver.get_by_id(uuid.UUID(credentials_id))
        else:
            # 2) иначе дефолт / единственная учётка
            secret = await self._resolver.get_default_for(
                bot_id=uuid.UUID(bot_id), provider=provider_key, strategy=strategy_hint
            ) or await self._resolver.get_single_for(
                bot_id=uuid.UUID(bot_id), provider=provider_key, strategy=strategy_hint
            )

        if not secret:
            raise RuntimeError(
                f"No credentials for bot={bot_id}, provider={provider_key}. "
                f"Set default or pass credentials_id."
            )
        if secret["provider"] != provider_key:
            raise RuntimeError("provider mismatch for resolved credentials")

        provider = self._providers[provider_key]
        token = await provider.ensure(
            bot_id=bot_id,
            profile=profile,
            creds_cfg=secret,  # содержит: provider, strategy, scopes, payload
            profile_state=None,
            hints=prov_hints,
            cache=self._cache,
        )
        provider.apply_headers(headers, token, prov_hints)

    def _detect_provider(self, url: str, explicit: Optional[str], hints):
        if explicit:
            return explicit, hints
        host = (urlparse(url).hostname or "").lower()
        if "googleapis.com" in host:
            # hints = {**hints, "scopes": ["https://www.googleapis.com/auth/cloud-platform"]}
            return "google", hints
        if host.endswith(".amocrm.ru"):
            return "amocrm", hints
        if "yandexcloud.net" in host or "cloud.yandex" in host:
            return "yandex_cloud", hints
        if host.startswith("api-metrika.yandex."):
            return "yandex_id", hints
        return None, hints
