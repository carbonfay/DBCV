import json, base64, secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

_KEY = settings.secret_box_key_bytes


def encrypt_dict_to_blob(payload: dict) -> str:
    aes = AESGCM(_KEY)
    iv = secrets.token_bytes(12)
    pt = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ct = aes.encrypt(iv, pt, None)
    return json.dumps({
        "v": 1, "alg": "AES-GCM",
        "iv": base64.b64encode(iv).decode(),
        "ct": base64.b64encode(ct).decode()
    }, separators=(",", ":"))


def decrypt_blob_to_dict(blob: str) -> dict:
    obj = json.loads(blob)
    iv = base64.b64decode(obj["iv"]);
    ct = base64.b64decode(obj["ct"])
    pt = AESGCM(_KEY).decrypt(iv, ct, None)
    return json.loads(pt.decode("utf-8"))
