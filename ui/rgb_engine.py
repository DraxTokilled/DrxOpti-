import math
import customtkinter as ctk

# Convierte HSV a hex
def _hsv_to_hex(h: float, s: float = 1.0, v: float = 1.0) -> str:
    h = h % 360
    hi = int(h / 60) % 6
    f  = h / 60 - int(h / 60)
    p, q, t = v*(1-s), v*(1-f*s), v*(1-(1-f)*s)
    rgb = [
        (v, t, p), (q, v, p), (p, v, t),
        (p, q, v), (t, p, v), (v, p, q),
    ][hi]
    return "#{:02X}{:02X}{:02X}".format(*(int(c * 255) for c in rgb))


class RGBEngine:
    """
    Motor central de animaciones RGB.
    Registra widgets y les aplica efectos continuos en segundo plano.
    """
    def __init__(self, root: ctk.CTk):
        self._root    = root
        self._hue     = 0.0
        self._running = True
        self._targets: list[dict] = []   # {widget, mode, offset, speed, sat, val}
        self._tick()

    def register(self, widget, mode: str = "border", offset: float = 0.0,
                 speed: float = 1.0, sat: float = 1.0, val: float = 1.0):
        """
        mode: "border" | "text" | "fg"
        offset: desfase de fase (0–360) para que distintos widgets no estén sincronizados
        speed: multiplicador de velocidad (1 = normal, 2 = doble)
        """
        self._targets.append({
            "widget": widget,
            "mode":   mode,
            "offset": offset,
            "speed":  speed,
            "sat":    sat,
            "val":    val,
        })

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        self._hue = (self._hue + 1.2) % 360   # velocidad global

        for t in self._targets:
            hue = (self._hue * t["speed"] + t["offset"]) % 360
            color = _hsv_to_hex(hue, t["sat"], t["val"])
            try:
                if t["mode"] == "border":
                    t["widget"].configure(border_color=color)
                elif t["mode"] == "text":
                    t["widget"].configure(text_color=color)
                elif t["mode"] == "fg":
                    t["widget"].configure(fg_color=color)
            except Exception:
                pass

        self._root.after(30, self._tick)   # ~33 fps


class RGBProgressBar(ctk.CTkProgressBar):
    """Barra de progreso con color RGB animado."""
    def __init__(self, master, speed: float = 1.0, **kwargs):
        super().__init__(master, **kwargs)
        self._hue   = 0.0
        self._speed = speed
        self._animate()

    def _animate(self):
        self._hue = (self._hue + 1.5 * self._speed) % 360
        color = _hsv_to_hex(self._hue)
        try:
            self.configure(progress_color=color)
        except Exception:
            return
        self.after(30, self._animate)


class RGBLabel(ctk.CTkLabel):
    """Label con texto que cicla colores RGB."""
    def __init__(self, master, speed: float = 1.0, sat: float = 1.0, offset: float = 0.0, **kwargs):
        super().__init__(master, **kwargs)
        self._hue    = offset
        self._speed  = speed
        self._sat    = sat
        self._animate()

    def _animate(self):
        self._hue = (self._hue + 1.2 * self._speed) % 360
        color = _hsv_to_hex(self._hue, self._sat)
        try:
            self.configure(text_color=color)
        except Exception:
            return
        self.after(30, self._animate)


def pulse_border_rgb(widget, speed: float = 1.0):
    """One-shot: aplica RGB pulsante al borde de un widget."""
    state = {"hue": 0.0}
    def tick():
        state["hue"] = (state["hue"] + 1.5 * speed) % 360
        color = _hsv_to_hex(state["hue"])
        try:
            widget.configure(border_color=color)
            widget.after(30, tick)
        except Exception:
            pass
    tick()
