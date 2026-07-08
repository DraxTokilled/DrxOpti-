import json
import os
from core.paths import data_dir

WHITELIST_FILE = os.path.join(data_dir(), "whitelist.json")

# Procesos que NUNCA se cierran por defecto
DEFAULT_WHITELIST = [
    "Discord.exe",       # llamadas de voz
    "obs64.exe",         # streaming
    "obs32.exe",
    "StreamlabsOBS.exe",
    "XSplit.exe",
    "Streamlabs.exe",
    "voicemeeter.exe",   # audio virtual
    "voicemeeterpro.exe",
    "vbcable",
    "nvcontainer.exe",   # NVIDIA overlay
    "audiodg.exe",       # motor de audio de Windows
]


def load() -> list:
    if not os.path.exists(WHITELIST_FILE):
        _save(DEFAULT_WHITELIST)
        return list(DEFAULT_WHITELIST)
    try:
        with open(WHITELIST_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return list(DEFAULT_WHITELIST)


def add(exe: str):
    wl = load()
    if exe not in wl:
        wl.append(exe)
        _save(wl)


def remove(exe: str):
    wl = load()
    if exe in wl:
        wl.remove(exe)
        _save(wl)


def is_whitelisted(exe: str) -> bool:
    wl = [e.lower() for e in load()]
    return exe.lower() in wl


def _save(wl: list):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(wl, f, indent=2)
