from PIL import Image, ImageDraw, ImageFont
import os, time, math
from core.paths import exports_dir

OUTPUT_DIR = exports_dir()

# Colores
BG       = (10,  10,  15)
CARD     = (15,  15,  26)
GREEN    = (0,   255, 135)
BLUE     = (0,   212, 255)
GOLD     = (255, 215, 0)
RED      = (255, 68,  68)
DIM      = (68,  85,  102)
WHITE    = (200, 220, 235)

W, H = 900, 520


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _score_color(score: float) -> tuple:
    if score >= 75:
        return GREEN
    if score >= 50:
        return BLUE
    return RED


def _draw_bar(draw: ImageDraw, x, y, w, h, pct: float, color: tuple, bg=(20, 20, 35)):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    filled = max(int(w * pct / 100), 4)
    draw.rounded_rectangle([x, y, x + filled, y + h], radius=h // 2, fill=color)


def generate(
    score_before: float,
    score_after:  float,
    hw_profile:   dict,
    ping_results: dict,
    tweaks_applied: int,
    ram_freed_gb: float,
    procs_killed: int,
) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fondo con gradiente sutil (líneas horizontales)
    for y in range(H):
        alpha = int(y / H * 12)
        draw.line([(0, y), (W, y)], fill=(10 + alpha, 10, 15 + alpha))

    # Borde neón superior
    sc = _score_color(score_after)
    draw.rectangle([0, 0, W, 3], fill=sc)

    # Header
    draw.text((32, 24), "DRX", font=_font(42, True), fill=GREEN)
    draw.text((98, 24), "OPTI", font=_font(42, True), fill=BLUE)
    draw.text((210, 38), "Gaming Optimizer", font=_font(16), fill=DIM)

    ts = time.strftime("%d/%m/%Y  %H:%M")
    draw.text((W - 180, 38), ts, font=_font(14), fill=DIM)

    # Separador
    draw.rectangle([32, 82, W - 32, 83], fill=(30, 30, 50))

    # Score grande — antes / después
    draw.text((32, 100), "PUNTUACIÓN DEL SISTEMA", font=_font(13), fill=DIM)

    bx, ax = 32, 260

    draw.text((bx, 122), f"{score_before:.0f}", font=_font(72, True), fill=DIM)
    draw.text((bx, 200), "ANTES", font=_font(12), fill=DIM)

    draw.text((bx + 130, 158), "→", font=_font(32), fill=DIM)

    draw.text((ax, 122), f"{score_after:.0f}", font=_font(72, True), fill=sc)
    draw.text((ax, 200), "DESPUÉS", font=_font(12), fill=sc)

    delta = score_after - score_before
    sign  = "+" if delta >= 0 else ""
    draw.text((ax + 95, 148), f"{sign}{delta:.0f} pts", font=_font(18, True), fill=sc)

    # Línea vertical divisoria
    draw.rectangle([520, 95, 521, 430], fill=(25, 25, 45))

    # Columna derecha — Hardware
    draw.text((545, 100), "HARDWARE", font=_font(13), fill=DIM)
    draw.text((545, 122), hw_profile.get("cpu", "—")[:36], font=_font(13, True), fill=WHITE)
    draw.text((545, 144), hw_profile.get("gpu", "—")[:36], font=_font(13, True), fill=WHITE)
    draw.text((545, 166), f"{hw_profile.get('ram_gb', 0)} GB RAM  ·  {hw_profile.get('cores', 0)} núcleos", font=_font(12), fill=DIM)

    # Tweaks aplicados / RAM / Procesos
    draw.rectangle([545, 192, W - 32, 193], fill=(25, 25, 45))
    draw.text((545, 202), "OPTIMIZACIONES", font=_font(13), fill=DIM)

    items = [
        (f"✓  {tweaks_applied} tweaks aplicados",  GREEN),
        (f"✓  +{ram_freed_gb:.1f} GB RAM liberada", BLUE),
        (f"✓  -{procs_killed} procesos cerrados",    BLUE),
    ]
    for i, (txt, col) in enumerate(items):
        draw.text((545, 222 + i * 22), txt, font=_font(13, True), fill=col)

    # Ping por juego
    if ping_results:
        draw.rectangle([545, 295, W - 32, 296], fill=(25, 25, 45))
        draw.text((545, 305), "LATENCIA A SERVIDORES (red)", font=_font(13), fill=DIM)
        yi = 325
        for game, regions in ping_results.items():
            valid = {r: ms for r, ms in regions.items() if ms is not None}
            best  = min(valid.values()) if valid else None
            col   = GREEN if best and best < 40 else (BLUE if best and best < 80 else (GOLD if best and best < 130 else RED))
            val   = f"{best:.0f}ms" if best else "—"
            draw.text((545, yi), f"{game:<14} {val}", font=_font(13, True), fill=col)
            yi += 22

    # Barras CPU / RAM en columna izquierda
    draw.text((32, 228), "CPU / RAM AL OPTIMIZAR", font=_font(13), fill=DIM)
    _draw_bar(draw, 32, 252, 460, 14, score_after, sc)
    draw.text((32, 274), f"Índice de rendimiento: {score_after:.0f}%", font=_font(12), fill=DIM)

    # Footer
    draw.rectangle([0, H - 48, W, H - 47], fill=(20, 20, 35))
    draw.text((32, H - 36), "drxopti.gumroad.com  |  Generado con DrxOpti PRO", font=_font(12), fill=DIM)
    draw.text((W - 220, H - 36), "discord.gg/drxopti", font=_font(12), fill=(114, 137, 218))

    path = os.path.join(OUTPUT_DIR, f"drxopti_score_{int(time.time())}.png")
    img.save(path, "PNG")
    return path
