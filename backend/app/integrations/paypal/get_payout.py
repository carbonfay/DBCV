"""PayPal Get Payout интеграция используя httpx для прямых запросов к PayPal REST API."""
from typing import Dict, Any
from uuid import UUID

from app.integrations.base import BaseIntegration, IntegrationMetadata
from app.auth.credentials_resolver import CredentialsResolver
from app.loggers.bot import BotLogger

# Импортируем httpx для прямых запросов к PayPal REST API
# Сохраняем оригинальные классы исключений до возможного monkeypatch в тестах
try:
    import httpx
    HTTPX_AVAILABLE = True
    _HTTPX_HTTP_STATUS_ERROR = getattr(httpx, "HTTPStatusError", Exception)
    _HTTPX_TIMEOUT_ERROR = getattr(httpx, "TimeoutException", TimeoutError)
    _HTTPX_REQUEST_ERROR = getattr(httpx, "RequestError", Exception)
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None
    _HTTPX_HTTP_STATUS_ERROR = Exception
    _HTTPX_TIMEOUT_ERROR = TimeoutError
    _HTTPX_REQUEST_ERROR = Exception


class PayPalGetPayoutIntegration(BaseIntegration):
    """Интеграция для получения информации о выплате PayPal через REST API."""
    
    @property
    def metadata(self) -> IntegrationMetadata:
        return IntegrationMetadata(
            id="paypal_get_payout",
            version="1.0.0",
            name="PayPal Get Payout",
            description="Получение информации о выплате PayPal по ID пакета выплат",
            category="payments",
            icon_s3_key="icons/integrations/paypal.svg",
            color="#003087",
            config_schema={
                "type": "object",
                "required": ["payout_batch_id"],
                "properties": {
                    "payout_batch_id": {
                        "type": "string",
                        "title": "Payout Batch ID",
                        "description": "ID пакета выплат PayPal (например: PAYOUT_BATCH_ID)"
                    },
                    "environment": {
                        "type": "string",
                        "title": "Environment",
                        "enum": ["sandbox", "production"],
                        "default": "sandbox",
                        "description": "Окружение PayPal: sandbox для тестирования, production для продакшена"
                    }
                }
            },
            credentials_provider="paypal",
            credentials_strategy="oauth",
            library_name="httpx>=0.27.0" if HTTPX_AVAILABLE else None,
            examples=[
                {
                    "title": "Получить информацию о выплате",
                    "config": {
                        "payout_batch_id": "PAYOUT_BATCH_ID",
                        "environment": "sandbox"
                    }
                }
            ]
        )
    
    async def _get_access_token(
        self,
        client_id: str,
        client_secret: str,
        environment: str,
        logger: BotLogger
    ) -> str:
        """
        Получает OAuth2 access token от PayPal.
        
        Args:
            client_id: PayPal Client ID
            client_secret: PayPal Client Secret
            environment: sandbox или production
            logger: Логгер
        
        Returns:
            Access token или None при ошибке
        """
        base_url = "https://api.sandbox.paypal.com" if environment == "sandbox" else "https://api.paypal.com"
        token_url = f"{base_url}/v1/oauth2/token"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    auth=(client_id, client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"Accept": "application/json", "Accept-Language": "en_US"}
                )
                response.raise_for_status()
                token_data = response.json()
                return token_data.get("access_token")
        except _HTTPX_HTTP_STATUS_ERROR as e:
            await logger.error(f"PayPal OAuth error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            await logger.error(f"Error getting PayPal access token: {e}")
            return None
    
    async def execute(
        self,
        config: Dict[str, Any],
        credentials_resolver: CredentialsResolver,
        bot_id: UUID,
        logger: BotLogger
    ) -> Dict[str, Any]:
        """
        Выполняет интеграцию используя httpx для прямых запросов к PayPal REST API.
        
        Args:
            config: Параметры интеграции
            credentials_resolver: Резолвер для получения credentials
            bot_id: ID бота для получения credentials
            logger: Логгер
        
        Returns:
            Результат выполнения в формате системы
        """
        if not HTTPX_AVAILABLE:
            await logger.error("httpx library is not available")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": "httpx library is not installed"
                }
            }
        
        # Получаем credentials из PayPal
        creds = await credentials_resolver.get_default_for(
            bot_id=bot_id,
            provider="paypal",
            strategy="oauth"
        )
        
        if not creds:
            await logger.error("PayPal credentials not found")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "PayPal credentials not found"
                }
            }
        
        # Credentials возвращаются с ключом "payload", который содержит расшифрованные данные
        payload = creds.get("payload", {})
        if not payload:
            # Если payload нет, возможно данные в корне (для обратной совместимости)
            payload = creds
        
        client_id = payload.get("client_id") or payload.get("clientId")
        client_secret = payload.get("client_secret") or payload.get("clientSecret")
        
        if not client_id or not client_secret:
            await logger.error(f"client_id or client_secret not found in credentials. Available keys: {list(payload.keys())}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 401,
                    "description": "client_id and client_secret are required in PayPal credentials"
                }
            }
        
        # Получаем параметры из config
        payout_batch_id = config.get("payout_batch_id")
        environment = config.get("environment", "sandbox")
        
        if not payout_batch_id:
            await logger.error("payout_batch_id is required")
            return {
                "response": {
                    "ok": False,
                    "error_code": 400,
                    "description": "payout_batch_id is required"
                }
            }
        
        # ИСПОЛЬЗУЕМ httpx ДЛЯ ПРЯМЫХ ЗАПРОСОВ К PAYPAL REST API
        try:
            # Получаем access token
            access_token = await self._get_access_token(
                client_id=client_id,
                client_secret=client_secret,
                environment=environment,
                logger=logger
            )
            
            if not access_token:
                return {
                    "response": {
                        "ok": False,
                        "error_code": 401,
                        "description": "Failed to get PayPal access token"
                    }
                }
            
            # Формируем URL для запроса
            base_url = "https://api.sandbox.paypal.com" if environment == "sandbox" else "https://api.paypal.com"
            payout_url = f"{base_url}/v1/payments/payouts/{payout_batch_id}"
            
            # Выполняем запрос к PayPal API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    payout_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    timeout=30.0
                )
                
                # Обрабатываем ответ
                if response.status_code == 200:
                    payout_data = response.json()
                    await logger.info(f"Successfully retrieved payout {payout_batch_id}")
                    
                    return {
                        "response": {
                            "ok": True,
                            "result": {
                                "batch_header": payout_data.get("batch_header", {}),
                                "items": payout_data.get("items", []),
                                "links": payout_data.get("links", [])
                            }
                        }
                    }
                elif response.status_code == 404:
                    await logger.error(f"Payout {payout_batch_id} not found")
                    return {
                        "response": {
                            "ok": False,
                            "error_code": 404,
                            "description": f"Payout batch {payout_batch_id} not found"
                        }
                    }
                else:
                    error_text = response.text
                    await logger.error(f"PayPal API error: {response.status_code} - {error_text}")
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", error_text)
                    except:
                        error_message = error_text
                    
                    return {
                        "response": {
                            "ok": False,
                            "error_code": response.status_code,
                            "description": error_message
                        }
                    }
                    
        except _HTTPX_TIMEOUT_ERROR:
            await logger.error("PayPal API request timeout")
            return {
                "response": {
                    "ok": False,
                    "error_code": 504,
                    "description": "PayPal API request timeout"
                }
            }
        except _HTTPX_REQUEST_ERROR as e:
            await logger.error(f"PayPal API request error: {e}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": f"PayPal API request error: {str(e)}"
                }
            }
        except Exception as e:
            await logger.error(f"Unexpected error: {e}")
            import traceback
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            await logger.error(f"Traceback: {traceback_str}")
            return {
                "response": {
                    "ok": False,
                    "error_code": 500,
                    "description": str(e)
                }
            }

