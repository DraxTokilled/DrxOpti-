import ctypes
import subprocess
import winreg

# Windows default: 15600 microseconds (15.6ms)
# Gaming target:    5000 microseconds (0.5ms)
DEFAULT_TIMER = 156000   # en unidades de 100ns
GAMING_TIMER  =   5000

_ntdll = ctypes.windll.ntdll

def get_current_resolution() -> float:
    minimum = ctypes.c_ulong()
    maximum = ctypes.c_ulong()
    current = ctypes.c_ulong()
    _ntdll.NtQueryTimerResolution(
        ctypes.byref(maximum),
        ctypes.byref(minimum),
        ctypes.byref(current),
    )
    return current.value / 10000  # convertir a ms

def set_gaming_resolution() -> bool:
    try:
        result = _ntdll.NtSetTimerResolution(GAMING_TIMER, True, ctypes.byref(ctypes.c_ulong()))
        return result == 0
    except Exception:
        return False

def restore_default_resolution() -> bool:
    try:
        result = _ntdll.NtSetTimerResolution(DEFAULT_TIMER, True, ctypes.byref(ctypes.c_ulong()))
        return result == 0
    except Exception:
        return False

def apply_bcdedit_timer():
    # Persiste el timer reducido entre reinicios (requiere admin)
    try:
        subprocess.run(
            ["bcdedit", "/set", "useplatformclock", "true"],
            capture_output=True, timeout=8
        )
        subprocess.run(
            ["bcdedit", "/set", "disabledynamictick", "yes"],
            capture_output=True, timeout=8
        )
        return True
    except Exception:
        return False

def restore_bcdedit_timer():
    try:
        subprocess.run(
            ["bcdedit", "/deletevalue", "useplatformclock"],
            capture_output=True, timeout=8
        )
        subprocess.run(
            ["bcdedit", "/set", "disabledynamictick", "no"],
            capture_output=True, timeout=8
        )
        return True
    except Exception:
        return False
