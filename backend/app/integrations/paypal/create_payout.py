# backend/app/integrations/paypal/create_payout.py

from backend.app.integrations.base import BaseIntegration
from backend.app.integrations.credentials_resolver import get_default_for
import requests
import logging

class PayPalCreatePayout(BaseIntegration):
    """
    Интеграция PayPal Create Payout
    """

    # Метаданные интеграции
    name = "paypal_create_payout"
    description = "Создаёт массовые выплаты через PayPal API"
    version = "1.0"

    def execute(self, payout_data: dict) -> dict:
        """
        Выполнить выплату через PayPal API POST /v1/payments/payouts
        """
        # Получение credentials через стандартный resolver
        credentials = get_default_for(provider="paypal", strategy="oauth2")
        access_token = credentials.access_token  # пример получения токена

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.post(
                "https://api.sandbox.paypal.com/v1/payments/payouts",
                json=payout_data,
                headers=headers
            )
            response.raise_for_status()  # исключение при ошибках HTTP
            return response.json()

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP ошибка PayPal: {http_err} - {response.text}")
            return {"error": str(http_err), "details": response.text}

        except requests.exceptions.RequestException as req_err:
            logging.error(f"Ошибка запроса PayPal: {req_err}")
            return {"error": str(req_err)}

        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            return {"error": str(e)}
