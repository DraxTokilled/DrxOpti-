import os
import sys

def data_dir() -> str:
    """
    Carpeta persistente para datos del usuario (licencia, whitelist, juegos).
    En .exe congelado usa %APPDATA%/DrxOpti; en desarrollo usa la raíz del proyecto.
    """
    if getattr(sys, "frozen", False):
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DrxOpti")
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(base, exist_ok=True)
    return base

def exports_dir() -> str:
    """Carpeta para las tarjetas de resultados generadas."""
    if getattr(sys, "frozen", False):
        base = os.path.join(os.path.expanduser("~"), "Pictures", "DrxOpti")
    else:
        base = os.path.join(data_dir(), "exports")
    os.makedirs(base, exist_ok=True)
    return base
