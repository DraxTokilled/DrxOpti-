import os
import shutil

CACHE_PATHS = {
    "NVIDIA DXCache":     os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA\DXCache"),
    "NVIDIA GLCache":     os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA\GLCache"),
    "AMD DxCache":        os.path.expandvars(r"%LOCALAPPDATA%\AMD\DxCache"),
    "AMD VkCache":        os.path.expandvars(r"%LOCALAPPDATA%\AMD\VkCache"),
    "D3DSCache":          os.path.expandvars(r"%LOCALAPPDATA%\D3DSCache"),
    "NVIDIA Compute":     os.path.expandvars(r"%APPDATA%\NVIDIA\ComputeCache"),
    "Unity ShaderCache":  os.path.expandvars(r"%LOCALAPPDATA%\unity3d"),
}


def get_cache_size() -> tuple[float, dict]:
    """Retorna (total_mb, {nombre: mb})."""
    sizes = {}
    total = 0.0
    for name, path in CACHE_PATHS.items():
        mb = _folder_size_mb(path)
        sizes[name] = mb
        total += mb
    return round(total, 1), sizes


def clean_all(progress_cb=None) -> dict:
    """
    Limpia todos los caches detectados.
    progress_cb(name, freed_mb) llamado por cada cache limpiada.
    Retorna {nombre: freed_mb}.
    """
    results = {}
    for name, path in CACHE_PATHS.items():
        if not os.path.exists(path):
            continue
        mb = _folder_size_mb(path)
        freed = _clean_folder(path)
        results[name] = round(freed, 1)
        if progress_cb:
            progress_cb(name, freed)
    return results


def _folder_size_mb(path: str) -> float:
    if not os.path.exists(path):
        return 0.0
    total = 0
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
    except Exception:
        pass
    return total / (1024 * 1024)


def _clean_folder(path: str) -> float:
    freed = 0.0
    try:
        for entry in os.scandir(path):
            try:
                size = _folder_size_mb(entry.path) if entry.is_dir() else entry.stat().st_size / (1024*1024)
                if entry.is_dir():
                    shutil.rmtree(entry.path, ignore_errors=True)
                else:
                    os.remove(entry.path)
                freed += size
            except Exception:
                pass
    except Exception:
        pass
    return freed
