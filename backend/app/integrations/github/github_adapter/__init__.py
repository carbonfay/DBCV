from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent / "github_openapi_client"

top = sys.modules.get("github_openapi_client")
if top is None:
    top = types.ModuleType("github_openapi_client")
    top.__path__ = [str(_pkg_dir)]
    top.__package__ = "github_openapi_client"
    sys.modules["github_openapi_client"] = top

importlib.import_module("github_openapi_client.exceptions")
importlib.import_module("github_openapi_client.api_client")
importlib.import_module("github_openapi_client.configuration")
importlib.import_module("github_openapi_client.api.repos_api")

nested_root = __name__ + ".github_openapi_client"
sys.modules[nested_root] = sys.modules["github_openapi_client"]

for name, module in list(sys.modules.items()):
    if name == "github_openapi_client" or name.startswith("github_openapi_client."):
        nested_name = nested_root + name[len("github_openapi_client"):]
        sys.modules[nested_name] = module
