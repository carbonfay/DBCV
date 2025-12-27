from __future__ import annotations

import time
from typing import Any, Mapping, Optional

import httpx
import jwt
from datetime import datetime, timedelta, timezone
from app.auth.types import AccessToken


class YandexCloudProvider:
    """
    IAM-токен для Yandex Cloud.
    Два варианта payload:
      A) OAuth-поток:
         { "oauth_token": "<user_oauth_token>" }
         -> обмен на IAM-токен через IAM API.
      B) Service Account key:
         {
           "service_account_id": "...",
           "key_id": "...",
           "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
         }
         -> формирую JWT и меняю на IAM-токен.
    """

    IAM_URL = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

    async def ensure(
        self,
        *,
        bot_id: str,
        profile: str,
        creds_cfg: Mapping[str, Any],
        profile_state: Optional[Mapping[str, Any]],
        hints: Mapping[str, Any],
        cache,
    ) -> AccessToken:
        provider = "yandex_cloud"
        strategy = str(creds_cfg.get("strategy", "service_account"))
        scopes = None  # Yandex Cloud IAM не требует scopes

        cached = cache.get(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes)
        if cached:
            return cached

        payload = creds_cfg["payload"]
        if "oauth_token" in payload:
            token = await self._from_oauth(payload["oauth_token"])
        else:
            token = await self._from_service_account(payload)

        cache.put(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes, token=token)
        return token

    def apply_headers(self, headers: dict, token: AccessToken, hints: Mapping[str, Any]) -> None:
        headers["Authorization"] = f"Bearer {token.access_token}"

    async def _from_oauth(self, oauth_token: str) -> AccessToken:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(self.IAM_URL, json={"yandexPassportOauthToken": oauth_token})
            r.raise_for_status()
            j = r.json()
        iam = j["iamToken"]
        expires_at = _parse_rfc3339_to_unix(j.get("expiresAt"))
        return AccessToken(token_type="Bearer", access_token=iam, expires_at=expires_at)

    async def _from_service_account(self, sa: Mapping[str, Any]) -> AccessToken:
        service_account_id = sa.get("service_account_id")
        key_id = sa.get("key_id")
        private_key = sa.get("private_key")

        if not (service_account_id and key_id and private_key):
            raise RuntimeError("yandex_cloud SA: missing service_account_id/key_id/private_key")

        now = datetime.now(timezone.utc)
        payload = {
            "aud": self.IAM_URL,
            "iss": service_account_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=1)).timestamp()),  # короткий TTL JWT
        }
        headers = {"kid": key_id, "typ": "JWT", "alg": "PS256"}

        assertion = jwt.encode(
            payload,
            private_key,
            algorithm="PS256",
            headers=headers,
        )

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(self.IAM_URL, json={"jwt": assertion})
            r.raise_for_status()
            j = r.json()
        iam = j["iamToken"]
        expires_at = _parse_rfc3339_to_unix(j.get("expiresAt"))
        return AccessToken(token_type="Bearer", access_token=iam, expires_at=expires_at)


class YandexIdOAuthProvider:
    """
    OAuth для Яндекс.ID (Метрика и похожие API).
    В payload ожидаю:
      - access_token (долгоживущий) ИЛИ client_id/client_secret/refresh_token для обновления.
    Заголовок — 'Authorization: OAuth <token>'.
    """

    TOKEN_URL = "https://oauth.yandex.ru/token"

    async def ensure(
        self,
        *,
        bot_id: str,
        profile: str,
        creds_cfg: Mapping[str, Any],
        profile_state: Optional[Mapping[str, Any]],
        hints: Mapping[str, Any],
        cache,
    ) -> AccessToken:
        provider = "yandex_id"
        strategy = str(creds_cfg.get("strategy", "oauth"))
        scopes = None

        cached = cache.get(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes)
        if cached:
            return cached

        payload = creds_cfg["payload"]
        if "access_token" in payload and not payload.get("expires_at"):
            token = AccessToken(token_type="OAuth", access_token=payload["access_token"], expires_at=None)
        elif "refresh_token" in payload:
            token = await self._refresh(payload)
        else:
            raise RuntimeError("yandex_id: provide access_token or refresh_token with client credentials")

        cache.put(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes, token=token)
        return token

    def apply_headers(self, headers: dict, token: AccessToken, hints: Mapping[str, Any]) -> None:
        headers["Authorization"] = f"OAuth {token.access_token}"

    async def _refresh(self, payload: Mapping[str, Any]) -> AccessToken:
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        refresh_token = payload.get("refresh_token")
        if not (client_id and client_secret and refresh_token):
            raise RuntimeError("yandex_id: missing client_id/client_secret/refresh_token")

        form = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(self.TOKEN_URL, data=form)
            r.raise_for_status()
            j = r.json()
        access_token = j["access_token"]
        expires_in = int(j.get("expires_in", 3600))
        expires_at = time.time() + expires_in - 60
        return AccessToken(token_type="OAuth", access_token=access_token, expires_at=expires_at)


class YandexMapsApiKeyProvider:
    """
    Провайдер для API-ключа Яндекс Карт.
    В payload ожидает:
      - api_key (строка)
    Используется как простой API-ключ, без обновления.
    """

    # Нет необходимости в TOKEN_URL или других URL, так как ключ не обновляется

    async def ensure(
        self,
        *,
        bot_id: str,
        profile: str,
        creds_cfg: Mapping[str, Any],
        profile_state: Optional[Mapping[str, Any]],
        hints: Mapping[str, Any],
        cache,
    ) -> AccessToken:
        provider = "yandex_maps"
        strategy = str(creds_cfg.get("strategy", "api_key"))  # по умолчанию 'api_key'
        scopes = None  # API-ключи не используют scopes

        # Проверяем кэш (хотя API-ключ не меняется, кэширование всё равно полезно)
        cached = cache.get(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes)
        if cached:
            return cached

        payload = creds_cfg["payload"]
        api_key = payload.get("api_key") or payload.get("key")  # Поддерживаем оба варианта

        if not api_key:
            raise RuntimeError("yandex_maps: missing api_key in payload")

        # Важно: API-ключ - это не токен, но мы используем AccessToken для совместимости
        # с текущей архитектурой. expires_at = None, так как API-ключи не истекают.
        token = AccessToken(token_type="ApiKey", access_token=api_key, expires_at=None)

        # Сохраняем в кэш
        cache.put(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes, token=token)
        return token

    def apply_headers(self, headers: dict, token: AccessToken, hints: Mapping[str, Any]) -> None:
        # API-ключ передается в заголовке или параметрах запроса, НЕ в Authorization
        # Но этот метод может не использоваться для API-ключа, если он передается как параметр
        # Оставляем как есть, но в интеграции мы его передаем как параметр geocode запроса
        # headers["Authorization"] = f"Api-Key {token.access_token}" # НЕТ для Yandex Maps API
        pass  # Для Yandex Maps API ключ передается как параметр, не заголовок


def _parse_rfc3339_to_unix(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        from datetime import datetime
        from dateutil import parser
        dt = parser.isoparse(s)
    except Exception:
        try:
            s2 = s.rstrip("Z")
            if "." in s2:
                s2 = s2.split(".", 1)[0]
            dt = datetime.fromisoformat(s2)
        except Exception:
            return None
    return dt.timestamp() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).timestamp()
