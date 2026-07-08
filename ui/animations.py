import customtkinter as ctk

# ── Helpers de color ──────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(r, g, b) -> str:
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"

def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)

# ── Animaciones públicas ──────────────────────────────────────────────────────

def pulse_button(widget, base_color: str, peak_color: str, cycles: int = 3, duration_ms: int = 400):
    """Pulso de color neón en un botón: base → peak → base, N veces."""
    steps = 20
    half  = duration_ms // 2

    def step(cycle, i, going_up):
        if cycle >= cycles:
            widget.configure(text_color=base_color)
            return
        t = i / steps
        color = _lerp_color(base_color, peak_color, t) if going_up else _lerp_color(peak_color, base_color, t)
        try:
            widget.configure(text_color=color)
        except Exception:
            return
        next_i = i + 1
        if next_i > steps:
            widget.after(half // steps, lambda: step(cycle + (0 if going_up else 1), 0, not going_up))
        else:
            widget.after(half // steps, lambda: step(cycle, next_i, going_up))

    step(0, 0, True)


def fade_text(widget, new_text: str, base_color: str, fade_color: str = "#0A0A0F", steps: int = 12, ms: int = 18):
    """Desvanece el texto actual y aparece el nuevo texto."""
    def fade_out(i):
        if i > steps:
            widget.configure(text=new_text)
            fade_in(0)
            return
        t = i / steps
        widget.configure(text_color=_lerp_color(base_color, fade_color, t))
        widget.after(ms, lambda: fade_out(i + 1))

    def fade_in(i):
        if i > steps:
            widget.configure(text_color=base_color)
            return
        t = i / steps
        widget.configure(text_color=_lerp_color(fade_color, base_color, t))
        widget.after(ms, lambda: fade_in(i + 1))

    fade_out(0)


def flash_border(widget, peak_color: str, base_color: str, steps: int = 16, ms: int = 20):
    """Flash en el borde del widget."""
    def to_peak(i):
        if i > steps:
            to_base(0)
            return
        widget.configure(border_color=_lerp_color(base_color, peak_color, i / steps))
        widget.after(ms, lambda: to_peak(i + 1))

    def to_base(i):
        if i > steps:
            widget.configure(border_color=base_color)
            return
        widget.configure(border_color=_lerp_color(peak_color, base_color, i / steps))
        widget.after(ms, lambda: to_base(i + 1))

    to_peak(0)
