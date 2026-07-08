import subprocess
import winreg
import ctypes

# Registro de valores originales para restaurar
_original_values = {}

NETWORK_TWEAKS = {
    "nagle_disabled": "Nagle's Algorithm desactivado",
    "tcp_ack_freq": "ACK frecuency optimizado",
    "tcp_no_delay": "TCP No Delay activado",
    "congestion_ctcp": "Algoritmo de congestión → CTCP",
    "dns_cache_boost": "Caché DNS boosteada",
    "network_throttle_off": "Throttling de red desactivado",
}

def apply_network_tweaks() -> dict:
    results = {}
    results["nagle_disabled"] = _disable_nagle()
    results["tcp_no_delay"] = _set_tcp_nodelay()
    results["congestion_ctcp"] = _set_ctcp()
    results["dns_cache_boost"] = _boost_dns_cache()
    results["network_throttle_off"] = _disable_network_throttle()
    return results

def restore_network_tweaks():
    _restore_nagle()

def get_current_ping_class() -> str:
    # Estima calidad de red por configuración actual
    try:
        result = subprocess.run(
            ["netsh", "interface", "tcp", "show", "global"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        if "ctcp" in output.lower() or "cubic" in output.lower():
            return "optimizado"
        return "default"
    except Exception:
        return "unknown"

def _disable_nagle():
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as interfaces:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(interfaces, i)
                    sub_path = f"{key_path}\\{sub}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_path, 0, winreg.KEY_ALL_ACCESS) as k:
                        winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                        winreg.SetValueEx(k, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                    i += 1
                except OSError:
                    break
        return True
    except Exception:
        return False

def _restore_nagle():
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as interfaces:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(interfaces, i)
                    sub_path = f"{key_path}\\{sub}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_path, 0, winreg.KEY_ALL_ACCESS) as k:
                        winreg.SetValueEx(k, "TcpAckFrequency", 0, winreg.REG_DWORD, 2)
                        winreg.SetValueEx(k, "TCPNoDelay", 0, winreg.REG_DWORD, 0)
                    i += 1
                except OSError:
                    break
    except Exception:
        pass

def _set_tcp_nodelay():
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as k:
            winreg.SetValueEx(k, "DefaultTTL", 0, winreg.REG_DWORD, 64)
            winreg.SetValueEx(k, "MaxUserPort", 0, winreg.REG_DWORD, 65534)
            winreg.SetValueEx(k, "TcpTimedWaitDelay", 0, winreg.REG_DWORD, 30)
        return True
    except Exception:
        return False

def _set_ctcp():
    try:
        subprocess.run(
            ["netsh", "int", "tcp", "set", "global", "congestionprovider=ctcp"],
            capture_output=True, timeout=8
        )
        subprocess.run(
            ["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
            capture_output=True, timeout=8
        )
        subprocess.run(
            ["netsh", "int", "tcp", "set", "global", "ecncapability=enabled"],
            capture_output=True, timeout=8
        )
        return True
    except Exception:
        return False

def _boost_dns_cache():
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as k:
            winreg.SetValueEx(k, "CacheHashTableBucketSize", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "CacheHashTableSize", 0, winreg.REG_DWORD, 384)
            winreg.SetValueEx(k, "MaxCacheEntryTtlLimit", 0, winreg.REG_DWORD, 64000)
            winreg.SetValueEx(k, "MaxSOACacheEntryTtlLimit", 0, winreg.REG_DWORD, 301)
        return True
    except Exception:
        return False

def _disable_network_throttle():
    try:
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS) as k:
            winreg.SetValueEx(k, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xffffffff)
            winreg.SetValueEx(k, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
        return True
    except Exception:
        return False
