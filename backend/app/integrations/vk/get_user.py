import httpx

from app.integrations.base import BaseIntegration
from app.integrations.types import (
    IntegrationMetadata,
    IntegrationContext,
    IntegrationResult,
)
from app.services.credentials_resolver import CredentialsResolver


class VkGetUserIntegration(BaseIntegration):

    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="vk_get_user",
            name="VK Get User",
            description="Get VK user info via VK API users.get",
            category="social",
            provider="vk",
            credentials_strategy="api_key",
            version="1.0.0",
            config_schema={
                "type": "object",
                "properties": {
                    "user_ids": {
                        "type": "string",
                        "description": "Comma-separated user IDs or screen names (e.g. '1,durov')"
                    },
                    "fields": {
                        "type": "string",
                        "description": "Optional fields to return (comma-separated, e.g. 'photo_200,city')",
                        "default": ""
                    }
                },
                "required": ["user_ids"]
            },
            outputs_schema={
                "type": "object"
            },
            examples=[
                {
                    "user_ids": "1",
                    "fields": "photo_200,city"
                }
            ]
        )

    async def execute(self, context: IntegrationContext) -> IntegrationResult:
        # Получаем credentials через CredentialsResolver
        credentials = CredentialsResolver.get_default_for(
            provider="vk",
            strategy="api_key",
            credentials=context.credentials
        )
        token = credentials.payload.get("access_token")
        if not token:
            return IntegrationResult(success=False, error="Missing access_token in credentials")

        user_ids = context.config.get("user_ids")
        fields = context.config.get("fields", "")

        url = "https://api.vk.com/method/users.get"
        params = {
            "access_token": token,
            "v": "5.199",
            "user_ids": user_ids,
        }
        if fields:
            params["fields"] = fields

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)

        try:
            data = resp.json()
        except Exception:
            return IntegrationResult(success=False, error="Invalid JSON response from VK", data={"status_code": resp.status_code, "text": resp.text})

        # Простая проверка на ошибки VK
        if "error" in data:
            return IntegrationResult(success=False, error=f"VK API error: {data['error']}", data=data)

        return IntegrationResult(success=True, data=data)
