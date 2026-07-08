import psutil
import ctypes
import subprocess
import os
from core.whitelist import is_whitelisted

# Procesos a cerrar cuando se detecta un juego
PROCESSES_TO_KILL = [
    "Discord.exe",
    "chrome.exe",
    "msedge.exe",
    "OneDrive.exe",
    "Teams.exe",
    "Spotify.exe",
    "EpicWebHelper.exe",
]

# Servicios de telemetria a pausar
SERVICES_TO_STOP = [
    "DiagTrack",       # Connected User Experiences and Telemetry
    "SysMain",         # Superfetch
]

_killed_processes = []
_stopped_services = []
_original_priorities = {}


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def apply_game_mode(game_name: str):
    _kill_background_processes()
    _stop_services()
    _set_game_priority(game_name)
    _clean_ram()


def restore_normal_mode():
    _restore_services()


def _kill_background_processes():
    _killed_processes.clear()
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name in PROCESSES_TO_KILL and not is_whitelisted(name):
                proc.kill()
                _killed_processes.append(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def _stop_services():
    _stopped_services.clear()
    if not is_admin():
        return
    for service in SERVICES_TO_STOP:
        try:
            subprocess.run(
                ["sc", "stop", service],
                capture_output=True,
                timeout=5
            )
            _stopped_services.append(service)
        except Exception:
            continue


def _restore_services():
    if not is_admin():
        return
    for service in _stopped_services:
        try:
            subprocess.run(
                ["sc", "start", service],
                capture_output=True,
                timeout=5
            )
        except Exception:
            continue
    _stopped_services.clear()


def _set_game_priority(game_name: str):
    GAME_EXE_MAP = {
        "Fortnite": "FortniteClient-Win64-Shipping.exe",
        "Valorant": "VALORANT-Win64-Shipping.exe",
        "CS2": "cs2.exe",
        "Warzone": "ModernWarfare4.exe",
        "Apex Legends": "r5apex.exe",
    }
    exe = GAME_EXE_MAP.get(game_name)
    if not exe:
        return

    HIGH_PRIORITY = 0x00000080

    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"] == exe:
                handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info["pid"])
                if handle:
                    ctypes.windll.kernel32.SetPriorityClass(handle, HIGH_PRIORITY)
                    ctypes.windll.kernel32.CloseHandle(handle)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def _clean_ram():
    # Fuerza al SO a liberar memoria de procesos inactivos
    if not is_admin():
        return
    try:
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
        for proc in psutil.process_iter(["pid"]):
            try:
                handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info["pid"])
                if handle:
                    ctypes.windll.psapi.EmptyWorkingSet(handle)
                    ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                continue
    except Exception:
        pass
