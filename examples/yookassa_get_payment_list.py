from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow running from repository root: `python examples/yookassa_get_payment_list.py`
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(dotenv_path=REPO_ROOT / ".env", override=False)

from app.integrations.yookassa.get_payment_list import (  # type: ignore[import-not-found]  # noqa: E402
    YooKassaGetPaymentListIntegration,
)


def main() -> None:
    """
    Example usage:

    PowerShell:
      $env:YOOKASSA_SHOP_ID="your-shop-id"
      $env:YOOKASSA_SECRET_KEY="test_********"
      python examples/yookassa_get_payment_list.py
    """

    integration = YooKassaGetPaymentListIntegration()
    # Для учебной демонстрации можно запустить dry_run без ключей/аккаунта:
    res = integration.execute({"limit": 5, "dry_run": True})
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


