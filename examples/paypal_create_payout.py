from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running from repository root: `python examples/paypal_create_payout.py`
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(dotenv_path=REPO_ROOT / ".env", override=False)

from app.integrations.paypal.create_payout import (  # type: ignore[import-not-found]  # noqa: E402
    PayPalCreatePayoutIntegration,
)


def main() -> None:
    """
    Example usage:

    PowerShell:
      $env:PAYPAL_CLIENT_ID="your-client-id"
      $env:PAYPAL_CLIENT_SECRET="your-client-secret"
      $env:PAYPAL_MODE="sandbox"
      python examples/paypal_create_payout.py
    """

    integration = PayPalCreatePayoutIntegration()

    # Для учебной демонстрации можно запустить dry_run без PayPal аккаунта/ключей:
    res = integration.execute(
        {
            "dry_run": True,
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "receiver": "recipient@example.com",
                    "amount": {"value": "10.00", "currency": "USD"},
                    "note": "Thanks!",
                    "sender_item_id": "item_1",
                }
            ],
        }
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


