import json
import sys
from app.integrations import registry


def main():
    integration = registry.get("vk_send_photo")
    if not integration:
        print(json.dumps({"ok": False, "reason": "vk_send_photo not registered"}))
        sys.exit(2)

    m = integration.metadata
    out = {
        "ok": True,
        "id": m.id,
        "version": m.version,
        "name": m.name,
        "category": m.category,
        "library_name": getattr(m, "library_name", None),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
