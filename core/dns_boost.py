import subprocess

DNS_PROVIDERS = {
    "Cloudflare (1.1.1.1)": ("1.1.1.1", "1.0.0.1"),
    "Google (8.8.8.8)":     ("8.8.8.8", "8.8.4.4"),
}

_FLAGS = subprocess.CREATE_NO_WINDOW


def get_active_interfaces() -> list[str]:
    """Nombres de interfaces de red conectadas."""
    try:
        result = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True, text=True, timeout=6, creationflags=_FLAGS,
        )
        names = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[0] == "Habilitado" or (len(parts) >= 4 and parts[0] == "Enabled"):
                if "Conectado" in line or "Connected" in line:
                    names.append(" ".join(parts[3:]))
        return names
    except Exception:
        return []


def apply_dns(primary: str, secondary: str) -> dict:
    """Aplica DNS a todas las interfaces conectadas y limpia la caché."""
    interfaces = get_active_interfaces()
    if not interfaces:
        return {"success": False, "reason": "No se detectaron interfaces conectadas"}

    applied = []
    for iface in interfaces:
        try:
            subprocess.run(
                ["netsh", "interface", "ipv4", "set", "dnsservers", f'name={iface}',
                 "static", primary, "primary"],
                capture_output=True, timeout=8, creationflags=_FLAGS,
            )
            subprocess.run(
                ["netsh", "interface", "ipv4", "add", "dnsservers", f'name={iface}',
                 secondary, "index=2"],
                capture_output=True, timeout=8, creationflags=_FLAGS,
            )
            applied.append(iface)
        except Exception:
            continue

    flush_dns()
    return {"success": bool(applied), "interfaces": applied}


def restore_dhcp_dns() -> bool:
    """Vuelve a DNS automático (DHCP) — el botón de deshacer."""
    ok = False
    for iface in get_active_interfaces():
        try:
            subprocess.run(
                ["netsh", "interface", "ipv4", "set", "dnsservers", f'name={iface}', "dhcp"],
                capture_output=True, timeout=8, creationflags=_FLAGS,
            )
            ok = True
        except Exception:
            continue
    flush_dns()
    return ok


def flush_dns():
    try:
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=8, creationflags=_FLAGS)
    except Exception:
        pass
