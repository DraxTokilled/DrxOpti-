import base64
import hashlib
import json
import os
import uuid
import time
from core.paths import data_dir

LICENSE_FILE = os.path.join(data_dir(), "license.dat")

# Claves de prueba locales — SOLO para desarrollo, bórralas antes de publicar
DEV_KEYS = {
    "DRXO-PRO1-2024-BETA": "pro",
}


def get_machine_id() -> str:
    raw = str(uuid.getnode())
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def activate(key: str) -> dict:
    key = key.strip()

    # Claves de desarrollo (quitar en producción)
    if key.upper() in DEV_KEYS:
        _save({
            "key": key.upper(), "tier": DEV_KEYS[key.upper()],
            "machine": get_machine_id(), "activated_at": time.time(),
        })
        return {"success": True, "tier": "pro"}

    # Verificación de firma offline
    result = _verify_signature(key)
    if result["valid"]:
        _save({
            "key": key, "tier": "pro",
            "cliente": result.get("cliente", ""),
            "machine": get_machine_id(), "activated_at": time.time(),
        })
        return {"success": True, "tier": "pro"}

    return {"success": False, "reason": result.get("reason", "Clave inválida.")}


def get_license() -> dict:
    data = _load()
    if not data:
        return {"tier": "free", "activated": False}
    if data.get("machine") != get_machine_id():
        return {"tier": "free", "activated": False, "reason": "Máquina no autorizada"}
    return {"tier": data.get("tier", "free"), "activated": True, "key": data.get("key", "")}


def is_pro() -> bool:
    return get_license().get("tier") == "pro"


def _verify_signature(key: str) -> dict:
    """
    Verifica la firma Ed25519 de una clave DRXO-<payload>.<firma>.
    La llave pública viaja con la app; la privada solo la tiene el vendedor.
    """
    try:
        from core.public_key import PUBLIC_KEY_B64
    except ImportError:
        return {"valid": False, "reason": "App sin llave pública. Reinstala DrxOpti."}

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        return {"valid": False, "reason": "Falta módulo de verificación. Reinstala DrxOpti."}

    if not key.startswith("DRXO-"):
        return {"valid": False, "reason": "Formato de clave incorrecto."}

    try:
        body = key[5:]
        payload_b64, sig_b64 = body.split(".")

        def _pad(s):  # restaurar padding base64
            return s + "=" * (-len(s) % 4)

        payload   = base64.urlsafe_b64decode(_pad(payload_b64))
        signature = base64.urlsafe_b64decode(_pad(sig_b64))

        public_key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(PUBLIC_KEY_B64)
        )
        public_key.verify(signature, payload)  # lanza excepción si es falsa

        cliente = payload.decode().split("|")[0]
        return {"valid": True, "cliente": cliente}

    except Exception:
        return {"valid": False, "reason": "Clave inválida o alterada."}


def _save(data: dict):
    encoded = json.dumps(data)
    obfuscated = "".join(chr(ord(c) ^ 0x5A) for c in encoded)
    with open(LICENSE_FILE, "w") as f:
        f.write(obfuscated)


def _load() -> dict | None:
    if not os.path.exists(LICENSE_FILE):
        return None
    try:
        with open(LICENSE_FILE, "r") as f:
            obfuscated = f.read()
        decoded = "".join(chr(ord(c) ^ 0x5A) for c in obfuscated)
        return json.loads(decoded)
    except Exception:
        return None
