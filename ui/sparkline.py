import tkinter as tk
import customtkinter as ctk
from collections import deque

NEON_GREEN = "#00FF87"
NEON_BLUE  = "#00D4FF"
NEON_RED   = "#FF4444"
GRID_COLOR = "#0F0F1A"
BG_COLOR   = "#080810"


class SparklineWidget(ctk.CTkFrame):
    """Gráfico de línea en tiempo real para CPU y RAM."""

    HISTORY = 60   # puntos máximos visibles

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_COLOR, corner_radius=8, **kwargs)

        self._cpu_data = deque([0.0] * self.HISTORY, maxlen=self.HISTORY)
        self._ram_data = deque([0.0] * self.HISTORY, maxlen=self.HISTORY)

        self._canvas = tk.Canvas(
            self,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True, padx=8, pady=6)

        self._build_legend()
        self._canvas.bind("<Configure>", lambda e: self._redraw())

    def _build_legend(self):
        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", padx=10, pady=(6, 0))

        ctk.CTkLabel(legend, text="━  CPU", font=ctk.CTkFont("Consolas", 9, "bold"), text_color=NEON_GREEN).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(legend, text="━  RAM", font=ctk.CTkFont("Consolas", 9, "bold"), text_color=NEON_BLUE).pack(side="left")

        self._peak_label = ctk.CTkLabel(legend, text="", font=ctk.CTkFont("Consolas", 9), text_color="#334455")
        self._peak_label.pack(side="right")

    def push(self, cpu: float, ram: float):
        self._cpu_data.append(cpu)
        self._ram_data.append(ram)
        self._redraw()

        peak_cpu = max(self._cpu_data)
        peak_ram = max(self._ram_data)
        self._peak_label.configure(text=f"peak CPU {peak_cpu:.0f}%  RAM {peak_ram:.0f}%")

    def _redraw(self):
        c = self._canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        c.delete("all")
        self._draw_grid(w, h)
        self._draw_series(list(self._cpu_data), NEON_GREEN, w, h)
        self._draw_series(list(self._ram_data), NEON_BLUE, w, h)
        self._draw_threshold(80, NEON_RED, w, h)

    def _draw_grid(self, w, h):
        c = self._canvas
        for pct in (25, 50, 75, 100):
            y = h - int(h * pct / 100)
            c.create_line(0, y, w, y, fill="#111120", width=1)
            c.create_text(4, y - 2, text=f"{pct}", fill="#1A1A30", font=("Consolas", 7), anchor="sw")

    def _draw_series(self, data: list, color: str, w: int, h: int):
        if len(data) < 2:
            return
        n   = len(data)
        pts = []
        for i, v in enumerate(data):
            x = int(i * w / (n - 1))
            y = h - int(h * min(v, 100) / 100)
            pts.extend([x, y])

        # Área rellena translúcida (simulada con líneas degradadas)
        fill_color = self._dim(color, 0.08)
        for i in range(0, len(pts) - 2, 2):
            x1, y1 = pts[i], pts[i + 1]
            x2, y2 = pts[i + 2], pts[i + 3]
            self._canvas.create_polygon(x1, y1, x2, y2, x2, h, x1, h, fill=fill_color, outline="")

        # Línea principal
        self._canvas.create_line(*pts, fill=color, width=1, smooth=True)

        # Punto actual (último valor)
        lx, ly = pts[-2], pts[-1]
        self._canvas.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill=color, outline="")

    def _draw_threshold(self, pct: float, color: str, w: int, h: int):
        y = h - int(h * pct / 100)
        self._canvas.create_line(0, y, w, y, fill=color, width=1, dash=(4, 6))

    @staticmethod
    def _dim(hex_color: str, factor: float) -> str:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
        return f"#{int(r*factor):02X}{int(g*factor):02X}{int(b*factor):02X}"
