import json
import urllib.request
import os
import sys
import threading

CURRENT_VERSION = "1.1.0"
VERSION_URL     = "https://raw.githubusercontent.com/drxopti/drxopti/main/version.json"
# Fallback local para cuando no haya release publicado aún
_FALLBACK = {"version": CURRENT_VERSION, "url": "", "changelog": "Sin actualizaciones disponibles."}


def check_for_update(timeout: float = 5.0) -> dict:
    """
    Retorna:
      { "has_update": bool, "latest": str, "current": str,
        "url": str, "changelog": str }
    """
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except Exception:
        data = _FALLBACK

    latest    = data.get("version", CURRENT_VERSION)
    has_update = _version_gt(latest, CURRENT_VERSION)
    return {
        "has_update": has_update,
        "latest":     latest,
        "current":    CURRENT_VERSION,
        "url":        data.get("url", ""),
        "changelog":  data.get("changelog", ""),
    }


def check_async(callback):
    """Llama callback(result) en un hilo separado."""
    def run():
        result = check_for_update()
        callback(result)
    threading.Thread(target=run, daemon=True).start()


def download_and_install(url: str, progress_cb=None):
    """Descarga el nuevo .exe y lo abre (reemplaza el proceso actual)."""
    import urllib.request
    tmp = os.path.join(os.environ.get("TEMP", "."), "DrxOpti_update.exe")
    try:
        def reporthook(count, block, total):
            if progress_cb and total > 0:
                progress_cb(int(count * block * 100 / total))
        urllib.request.urlretrieve(url, tmp, reporthook)
        os.startfile(tmp)
        sys.exit(0)
    except Exception as e:
        raise RuntimeError(f"Descarga fallida: {e}")


def _version_gt(a: str, b: str) -> bool:
    """True si a > b (ej: '1.2.0' > '1.1.0')."""
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except Exception:
        return False
