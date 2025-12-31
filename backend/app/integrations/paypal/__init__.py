"""PayPal integrations package: register available PayPal integrations."""
from app.integrations.registry import registry
import sys, traceback

try:
    from .create_order import PaypalCreateOrderIntegration
    registry.register(PaypalCreateOrderIntegration())
    print("[paypal] PaypalCreateOrderIntegration registered")
except Exception as e:
    print("[paypal] Failed to register PaypalCreateOrderIntegration:", e, file=sys.stderr)
    traceback.print_exc()

try:
    from .get_order import PaypalGetOrderIntegration
    registry.register(PaypalGetOrderIntegration())
    print("[paypal] PaypalGetOrderIntegration registered")
except Exception as e:
    print("[paypal] Failed to register PaypalGetOrderIntegration:", e, file=sys.stderr)
    traceback.print_exc()
