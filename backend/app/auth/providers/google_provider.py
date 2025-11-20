from __future__ import annotations
import time, asyncio
from typing import Any, Mapping, Optional, List
import httpx
from app.auth.types import AccessToken


class GoogleProvider:
    def __init__(self):
        try:
            from google.oauth2.service_account import Credentials as SACreds  # type: ignore
            from google.auth.transport.requests import Request as GoogleRequest  # type: ignore
            self._sa_available = True
            self._SACreds = SACreds
            self._GoogleRequest = GoogleRequest
        except Exception:
            self._sa_available = False
            self._SACreds = None
            self._GoogleRequest = None

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
        strategy = str(creds_cfg.get("strategy", "service_account"))
        provider = "google"

        scopes_cred = creds_cfg.get("scopes") or []
        scopes_hint = hints.get("scopes") or []

        scopes = list(dict.fromkeys([*scopes_cred, *scopes_hint]))
        if not scopes:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        print(f"[google] using scopes: {scopes}")

        cached = cache.get(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes)
        if cached:
            return cached

        if strategy == "service_account":
            token = await self._from_service_account(creds_cfg["payload"], scopes)
        elif strategy == "oauth":
            token = await self._from_oauth_refresh(creds_cfg["payload"])
        else:
            raise RuntimeError(f"google: unsupported strategy: {strategy}")

        cache.put(bot_id=bot_id, provider=provider, profile=profile, strategy=strategy, scopes=scopes, token=token)
        return token

    def apply_headers(self, headers: dict, token: AccessToken, hints: Mapping[str, Any]) -> None:
        headers["Authorization"] = f"{token.token_type} {token.access_token}"

    async def _from_service_account(self, payload: Mapping[str, Any], scopes: List[str]) -> AccessToken:
        if not self._sa_available:
            raise RuntimeError(
                "google-auth not installed or broken namespace. "
                "Run: pip uninstall -y google && pip install google-auth requests"
            )

        SACreds = self._SACreds
        GoogleRequest = self._GoogleRequest

        creds = SACreds.from_service_account_info(dict(payload), scopes=scopes)

        # refresh() — синхронный; исполняем в thread-пуле, чтобы не блокировать event loop
        def _refresh_sync():
            creds.refresh(GoogleRequest())
            return creds.token, getattr(creds, "expiry", None)

        token_value, expiry_dt = await asyncio.to_thread(_refresh_sync)
        expires_at = expiry_dt.timestamp() if expiry_dt else None

        return AccessToken(token_type="Bearer", access_token=token_value, expires_at=expires_at)

    async def _from_oauth_refresh(self, payload: Mapping[str, Any]) -> AccessToken:
        client_id = payload.get("client_id")
        client_secret = payload.get("client_secret")
        refresh_token = payload.get("refresh_token")
        if not (client_id and client_secret and refresh_token):
            raise RuntimeError("google oauth: missing client_id/client_secret/refresh_token")

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post("https://oauth2.googleapis.com/token", data=data)
            r.raise_for_status()
            j = r.json()

        access_token = j["access_token"]
        expires_in = int(j.get("expires_in", 3600))
        expires_at = time.time() + expires_in - 60
        return AccessToken(token_type="Bearer", access_token=access_token, expires_at=expires_at)
