import os
import json
from datetime import datetime

BACKUP_DIR = "/mnt/bot_backups"


async def store_bot_version(bot_id, data: dict):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    filename = f"{BACKUP_DIR}/{bot_id}_{datetime.now().isoformat()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename