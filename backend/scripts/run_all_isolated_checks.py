"""Оркестратор изолированных проверок интеграций.
Запускает существующие скрипты check_get_updates_isolated.py, check_send_video_isolated.py,
check_integrations_catalog_isolated.py и выводит сводку.
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPTS = [
    BASE / "scripts" / "check_get_updates_isolated.py",
    BASE / "scripts" / "check_send_video_isolated.py",
    BASE / "scripts" / "check_integrations_catalog_isolated.py",
]

results = {}
for s in SCRIPTS:
    if not s.exists():
        results[str(s.name)] = (False, "missing")
        continue
    print(f"Running {s.name}...")
    try:
        proc = subprocess.run([sys.executable, str(s)], capture_output=True, text=True, check=False)
        ok = proc.returncode == 0
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        results[str(s.name)] = (ok, out or err)
    except Exception as e:
        results[str(s.name)] = (False, str(e))

print("\nSummary:")
for name, (ok, msg) in results.items():
    status = "OK" if ok else "FAIL"
    print(f"- {name}: {status}")
    if msg:
        print(f"  -> {msg.splitlines()[0]}")

if all(r[0] for r in results.values()):
    sys.exit(0)
else:
    sys.exit(1)
