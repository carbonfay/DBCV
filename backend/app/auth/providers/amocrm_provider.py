from __future__ import annotations

import time
from typing import Any, Mapping, Optional

import httpx
from app.auth.types import AccessToken


class AmoCrmProvider:
    """
    OAuth для AmoCRM.
    В payload ожидаю:
      - base_domain: "mycompany.amocrm.ru"
      - client_id, client_secret, redirect_uri
      - refresh_token
      (опционально) access_token, expires_at — если уже есть.
    """

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
        provider = "amocrm"
        strategy = str(creds_cfg.get("strategy", "oauth"))
        scopes = None  # у AmoCRM скоупы не участвуют в Bearer

        cached = cache.get(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes)
        if cached:
            return cached

        payload = creds_cfg["payload"]
        base_domain = payload.get("base_domain")
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        redirect_uri = payload.get("redirect_uri")
        refresh_token = payload.get("refresh_token")

        if not (base_domain and client_id and client_secret and redirect_uri and refresh_token):
            raise RuntimeError("amocrm: missing base_domain/client_id/client_secret/redirect_uri/refresh_token")

        token = await self._refresh(base_domain, client_id, client_secret, redirect_uri, refresh_token)
        cache.put(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes, token=token)
        return token

    def apply_headers(self, headers: dict, token: AccessToken, hints: Mapping[str, Any]) -> None:
        headers["Authorization"] = f"{token.token_type} {token.access_token}"

    async def _refresh(self, base_domain: str, client_id: str, client_secret: str, redirect_uri: str, refresh_token: str) -> AccessToken:
        url = f"https://{base_domain}/oauth2/access_token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": redirect_uri,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            j = r.json()
        access_token = j["access_token"]
        expires_in = int(j.get("expires_in", 7200))
        # Amo обычно даёт 2 часа — беру минутный буфер
        expires_at = time.time() + expires_in - 60
        return AccessToken(token_type="Bearer", access_token=access_token, expires_at=expires_at)
