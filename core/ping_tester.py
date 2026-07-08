import socket
import time

# IPs reales de servidores de juegos competitivos
GAME_SERVERS = {
    "Epic / Fortnite": [
        ("epicgames.com",           80, "US"),
        ("www.epicgames.com",       80, "CDN"),
    ],
    "Riot / Valorant": [
        ("riotgames.com",           80, "Global"),
        ("www.riotgames.com",       80, "CDN"),
    ],
    "Steam / CS2": [
        ("store.steampowered.com",  80, "US"),
        ("steamcommunity.com",      80, "CDN"),
    ],
    "EA / Apex": [
        ("www.ea.com",              80, "Global"),
        ("origin.com",              80, "CDN"),
    ],
}


def ping_host(host: str, port: int, timeout: float = 3.0) -> float | None:
    """Retorna latencia en ms o None si no conecta."""
    try:
        start = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return round((time.perf_counter() - start) * 1000, 1)
    except Exception:
        return None


def test_all_servers(progress_cb=None) -> dict:
    """
    Retorna dict: { "Fortnite": {"NA-East": 32.1, "EU-West": 89.4}, ... }
    progress_cb(game, region, ms) llamado por cada resultado.
    """
    results = {}
    for game, servers in GAME_SERVERS.items():
        results[game] = {}
        for host, port, region in servers:
            ms = ping_host(host, port)
            results[game][region] = ms
            if progress_cb:
                progress_cb(game, region, ms)
    return results


def best_ping(results: dict) -> dict:
    """Retorna el mejor ping por juego."""
    best = {}
    for game, regions in results.items():
        valid = {r: ms for r, ms in regions.items() if ms is not None}
        if valid:
            best[game] = min(valid.values())
        else:
            best[game] = None
    return best


def ping_rating(ms: float | None) -> tuple[str, str]:
    """Retorna (texto, color_hex)."""
    if ms is None:
        return "SIN CONEXIÓN", "#FF4444"
    if ms < 40:
        return f"{ms:.0f}ms  ✦ EXCELENTE", "#00FF87"
    if ms < 80:
        return f"{ms:.0f}ms  ◈ BUENO",     "#00D4FF"
    if ms < 130:
        return f"{ms:.0f}ms  ○ ACEPTABLE",  "#FFD700"
    return f"{ms:.0f}ms  ✗ ALTO",          "#FF4444"
