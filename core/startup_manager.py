import winreg
import os

STARTUP_KEYS = [
    (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",        "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",        "HKLM"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM32"),
]

SAFE_TO_DISABLE = {
    "discord", "spotify", "steam", "onedrive", "teams", "skype",
    "slack", "zoom", "epicgameslauncher", "upc", "uplay", "origin",
    "battlenet", "googledrivefs", "dropbox", "box", "mega",
    "acrobat", "adobe", "cortana", "copilot", "yourphone",
}


def get_startup_entries() -> list[dict]:
    entries = []
    for hive, path, label in STARTUP_KEYS:
        try:
            with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        exe = _extract_exe(value)
                        entries.append({
                            "name":     name,
                            "path":     value,
                            "exe":      exe,
                            "hive":     hive,
                            "reg_path": path,
                            "label":    label,
                            "safe":     _is_safe(name, exe),
                            "enabled":  True,
                        })
                        i += 1
                    except OSError:
                        break
        except Exception:
            continue

    # Startup folder del usuario
    startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    try:
        for f in os.listdir(startup_folder):
            if f.lower().endswith((".lnk", ".bat", ".cmd", ".exe")):
                entries.append({
                    "name":     f,
                    "path":     os.path.join(startup_folder, f),
                    "exe":      f,
                    "hive":     None,
                    "reg_path": startup_folder,
                    "label":    "Folder",
                    "safe":     _is_safe(f, f),
                    "enabled":  True,
                })
    except Exception:
        pass

    return entries


def disable_entry(entry: dict) -> bool:
    if entry["hive"] is None:
        # Startup folder — renombrar para desactivar
        src = entry["path"]
        dst = src + ".disabled"
        try:
            os.rename(src, dst)
            return True
        except Exception:
            return False
    try:
        with winreg.OpenKey(entry["hive"], entry["reg_path"], 0, winreg.KEY_ALL_ACCESS) as key:
            # Guardar en clave de backup
            value, _ = winreg.QueryValueEx(key, entry["name"])
            backup_path = entry["reg_path"].replace("Run", "Run-DrxOpti-Backup")
            try:
                with winreg.CreateKey(entry["hive"], backup_path) as bk:
                    winreg.SetValueEx(bk, entry["name"], 0, winreg.REG_SZ, value)
            except Exception:
                pass
            winreg.DeleteValue(key, entry["name"])
            return True
    except Exception:
        return False


def enable_entry(entry: dict) -> bool:
    if entry["hive"] is None:
        src = entry["path"] + ".disabled"
        dst = entry["path"]
        try:
            os.rename(src, dst)
            return True
        except Exception:
            return False
    try:
        backup_path = entry["reg_path"].replace("Run", "Run-DrxOpti-Backup")
        with winreg.OpenKey(entry["hive"], backup_path, 0, winreg.KEY_READ) as bk:
            value, _ = winreg.QueryValueEx(bk, entry["name"])
        with winreg.OpenKey(entry["hive"], entry["reg_path"], 0, winreg.KEY_ALL_ACCESS) as key:
            winreg.SetValueEx(key, entry["name"], 0, winreg.REG_SZ, value)
        return True
    except Exception:
        return False


def _extract_exe(value: str) -> str:
    parts = value.strip().strip('"').split('"')
    path  = parts[0] if parts else value
    return os.path.basename(path).lower()


def _is_safe(name: str, exe: str) -> bool:
    n = name.lower()
    e = exe.lower()
    return any(k in n or k in e for k in SAFE_TO_DISABLE)
