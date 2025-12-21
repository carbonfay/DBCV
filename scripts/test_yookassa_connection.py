"""Local demo script to test YooKassa integrations without real credentials.

This script mocks the SDK classes using fixture JSON files and runs
`YoukassaGetPaymentsIntegration`, `YoukassaGetPaymentIntegration`, and
`YoukassaCreateReceiptIntegration` showing sample outputs.

Run: python scripts/test_yookassa_connection.py
"""
import sys
import json
from pathlib import Path
from uuid import UUID

# Ensure backend is on path so `app` package can be imported when running script from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Create a lightweight stub for app.loggers.bot to avoid importing heavy dependencies
import types
bot_mod = types.ModuleType("app.loggers.bot")

class _BotLoggerStub:
    async def info(self, *args, **kwargs):
        print("BOT-INFO:", *args)

    async def error(self, *args, **kwargs):
        print("BOT-ERROR:", *args)

bot_mod.BotLogger = _BotLoggerStub
sys.modules["app.loggers.bot"] = bot_mod

# Stub minimal package and base integration module to prevent executing package-level __init__ files
pkg_mod = types.ModuleType("app.integrations")
base_mod = types.ModuleType("app.integrations.base")

# Minimal IntegrationMetadata and BaseIntegration stubs
from dataclasses import dataclass

@dataclass
class IntegrationMetadataStub:
    id: str = "stub"
    version: str = "0.0.0"
    name: str = "stub"
    description: str = "stub"
    category: str = "payments"
    icon_s3_key: str = ""
    color: str = "#000000"
    config_schema: dict = None
    credentials_provider: str = ""
    credentials_strategy: str = "api_key"
    library_name: str = None
    examples: list = None

class BaseIntegrationStub:
    @property
    def metadata(self):
        return IntegrationMetadataStub()

    async def execute(self, *args, **kwargs):
        return {"response": {"ok": False, "error_code": 501, "description": "not implemented"}}

base_mod.IntegrationMetadata = IntegrationMetadataStub
base_mod.BaseIntegration = BaseIntegrationStub
sys.modules["app.integrations"] = pkg_mod
sys.modules["app.integrations.base"] = base_mod

# Also stub credentials_resolver type to avoid heavy backend imports
cred_mod = types.ModuleType("app.auth.credentials_resolver")
class CredentialsResolverStub:
    async def get_default_for(self, *args, **kwargs):
        return None
cred_mod.CredentialsResolver = CredentialsResolverStub
sys.modules["app.auth.credentials_resolver"] = cred_mod

# Load integration modules directly from file to avoid importing whole package and its side-effects
import importlib.util

def load_module_from_file(name: str, rel_path: str):
    file_path = Path(__file__).parent.parent / "backend" / "app" / rel_path
    spec = importlib.util.spec_from_file_location(name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module

get_payments_mod = load_module_from_file("youkassa.get_payments", "integrations/youkassa/get_payments.py")
get_payment_mod = load_module_from_file("youkassa.get_payment", "integrations/youkassa/get_payment.py")
create_receipt_mod = load_module_from_file("youkassa.create_receipt", "integrations/youkassa/create_receipt.py")

YoukassaGetPaymentsIntegration = get_payments_mod.YoukassaGetPaymentsIntegration
YoukassaGetPaymentIntegration = get_payment_mod.YoukassaGetPaymentIntegration
YoukassaCreateReceiptIntegration = create_receipt_mod.YoukassaCreateReceiptIntegration


def load_fixture(name: str):
    p = Path(__file__).parent.parent / "backend" / "app" / "tests" / "fixtures" / "youkassa" / name
    return json.loads(p.read_text())


class FakeCredentialsResolver:
    def __init__(self, payload):
        self._payload = payload

    async def get_default_for(self, bot_id, provider, strategy):
        return {"payload": self._payload}


class DummyLogger:
    async def info(self, *args, **kwargs):
        print("INFO:", *args)

    async def error(self, *args, **kwargs):
        print("ERROR:", *args)


class FakePaymentAPI:
    def __init__(self, data):
        self._data = data

    def list(self, params):
        class R:
            def __init__(self, items, cursor):
                self.items = items
                self.next_cursor = cursor

        items = [type("X", (), {"to_dict": (lambda self, payload=i: payload)})() for i in self._data["items"]]
        return R(items, self._data.get("next_cursor"))

    def find_one(self, payment_id):
        return type("Y", (), {"to_dict": (lambda self, payload=self._data: payload)})()


class FakeReceiptAPI:
    def __init__(self, data):
        self._data = data

    def create(self, cfg):
        return type("R", (), {"to_dict": (lambda self, payload=self._data: payload)})()


async def run():
    bot_id = UUID("12345678-1234-5678-1234-567812345678")
    creds = {"account_id": "acct_demo", "secret_key": "sk_demo"}
    resolver = FakeCredentialsResolver(creds)
    logger = DummyLogger()

    # Load fixtures
    payments_fixture = load_fixture("payments_list.json")
    payment_detail = load_fixture("payment_detail.json")
    receipt_fixture = load_fixture("receipt_create.json")

    # Use loaded module objects and assign fake SDK implementations
    gp = get_payments_mod
    g = get_payment_mod
    cr = create_receipt_mod

    # Replace SDK classes with our fakes and mark library available
    gp.YOOKASSA_AVAILABLE = True
    g.YOOKASSA_AVAILABLE = True
    cr.YOOKASSA_AVAILABLE = True

    # Provide a fake Configuration object so integrations accept provided credentials
    class FakeConfiguration:
        @staticmethod
        def configure(account_id, secret_key):
            print(f"FakeConfiguration.configure called with: {account_id}, {secret_key}")

        @staticmethod
        def configure_auth_token(token):
            print(f"FakeConfiguration.configure_auth_token called with: {token}")

    gp.Configuration = FakeConfiguration
    g.Configuration = FakeConfiguration
    cr.Configuration = FakeConfiguration

    gp.Payment = FakePaymentAPI(payments_fixture)
    g.Payment = FakePaymentAPI({"items": [payment_detail]})
    cr.Receipt = FakeReceiptAPI(receipt_fixture)

    # Run Get Payments
    print("\n--- Get Payments ---")
    gp_integration = YoukassaGetPaymentsIntegration()
    res = await gp_integration.execute({"limit": 2}, resolver, bot_id, logger)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))

    # Run Get Payment
    print("\n--- Get Payment ---")
    g_integration = YoukassaGetPaymentIntegration()
    res = await g_integration.execute({"payment_id": "pay_1"}, resolver, bot_id, logger)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))

    # Run Create Receipt
    print("\n--- Create Receipt ---")
    cr_integration = YoukassaCreateReceiptIntegration()
    cfg = {"payment_id": "pay_1", "items": [{"description": "x", "amount": {"value": "100.00", "currency": "RUB"}}]}
    res = await cr_integration.execute(cfg, resolver, bot_id, logger)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
