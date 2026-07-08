import customtkinter as ctk
import threading
from core.shader_cleaner import get_cache_size, clean_all
from ui.rgb_engine import RGBEngine, RGBProgressBar
from ui.glass import glass_header_row, apply_window_glass, GLASS_BG, GLASS_BORDER

DARK_BG    = "#0A0A0F"
CARD_BG    = "#0F0F1A"
NEON_GREEN = "#00FF87"
NEON_BLUE  = "#00D4FF"
NEON_RED   = "#FF4444"
CARD_BORDER= "#1A1A2E"


class ShaderWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("DrxOpti — Shader Cache Cleaner")
        self.geometry("560x460")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.grab_set()

        self._rgb = RGBEngine(self)
        apply_window_glass(self, 0.97)
        self._build_ui()
        threading.Thread(target=self._scan, daemon=True).start()

    def _build_ui(self):
        hdr, title_lbl = glass_header_row(
            self, "🧹  SHADER CACHE CLEANER",
            "Elimina shaders acumulados que causan stuttering en tus juegos",
            NEON_GREEN,
        )
        self._rgb.register(title_lbl, mode="text", speed=0.7)

        body = ctk.CTkFrame(self, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Card de tamaño total
        size_card = ctk.CTkFrame(body, fg_color=GLASS_BG, corner_radius=10,
                                 border_width=1, border_color=GLASS_BORDER)
        size_card.pack(fill="x", pady=(0, 10))
        self._rgb.register(size_card, mode="border", speed=0.5, sat=0.85)

        row = ctk.CTkFrame(size_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=16)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(left, text="CACHÉ ACUMULADA",
                     font=ctk.CTkFont("Consolas", 10), text_color="#445566").pack(anchor="w")
        self._total_label = ctk.CTkLabel(left, text="Escaneando...",
                                         font=ctk.CTkFont("Consolas", 28, "bold"),
                                         text_color=NEON_GREEN)
        self._total_label.pack(anchor="w")

        self._clean_btn = ctk.CTkButton(
            row, text="LIMPIAR TODO",
            font=ctk.CTkFont("Consolas", 13, "bold"),
            fg_color="#001A00", hover_color="#002500",
            text_color=NEON_GREEN, border_color=NEON_GREEN, border_width=1,
            corner_radius=8, height=46, width=180,
            command=self._clean,
        )
        self._clean_btn.pack(side="right")
        self._rgb.register(self._clean_btn, mode="border", offset=90, speed=0.6)

        # Lista de caches
        self._list_frame = ctk.CTkScrollableFrame(body, fg_color=CARD_BG,
                                                  corner_radius=10,
                                                  scrollbar_button_color=CARD_BORDER)
        self._list_frame.pack(fill="both", expand=True)

        # Barra de progreso (oculta hasta limpiar)
        self._prog_bar = RGBProgressBar(body, speed=1.2, height=8, corner_radius=4,
                                        fg_color="#0A0A14")
        self._prog_bar.set(0)
        self._status_label = ctk.CTkLabel(body, text="",
                                          font=ctk.CTkFont("Consolas", 10),
                                          text_color="#334455")

    def _scan(self):
        total, sizes = get_cache_size()
        self.after(0, lambda: self._show_sizes(total, sizes))

    def _show_sizes(self, total, sizes):
        self._total_label.configure(text=f"{total:.1f} MB")
        for w in self._list_frame.winfo_children():
            w.destroy()

        for name, mb in sizes.items():
            if mb < 0.01:
                continue
            row = ctk.CTkFrame(self._list_frame, fg_color="#080810", corner_radius=6)
            row.pack(fill="x", pady=3, padx=4)

            color = NEON_GREEN if mb > 50 else (NEON_BLUE if mb > 10 else "#445566")
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont("Consolas", 10, "bold"),
                         text_color=color, anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(row, text=f"{mb:.1f} MB", font=ctk.CTkFont("Consolas", 10, "bold"),
                         text_color=color).pack(side="right", padx=12, pady=8)

        if total < 0.1:
            ctk.CTkLabel(self._list_frame, text="✓  No se encontró caché acumulada",
                         font=ctk.CTkFont("Consolas", 11), text_color=NEON_GREEN).pack(pady=20)

    def _clean(self):
        self._clean_btn.configure(state="disabled", text="LIMPIANDO...")
        self._prog_bar.pack(fill="x", padx=16, pady=(6, 0))
        self._prog_bar.set(0)
        self._status_label.pack(pady=4)

        total_freed = [0.0]
        done_count  = [0]
        total_count = len([p for p in __import__("core.shader_cleaner", fromlist=["CACHE_PATHS"]).CACHE_PATHS.values()
                           if __import__("os").path.exists(p)])
        if total_count == 0:
            total_count = 1

        def progress(name, freed):
            total_freed[0] += freed
            done_count[0]  += 1
            pct = min(done_count[0] / total_count, 1.0)
            self.after(0, lambda: self._prog_bar.set(pct))
            self.after(0, lambda: self._status_label.configure(text=f"Limpiando {name}..."))

        def run():
            clean_all(progress_cb=progress)
            self.after(0, self._on_clean_done)

        threading.Thread(target=run, daemon=True).start()

    def _on_clean_done(self):
        self._prog_bar.set(1.0)
        self._status_label.configure(text="✓  Limpieza completa — reinicia para aplicar cambios", text_color=NEON_GREEN)
        self._clean_btn.configure(state="normal", text="✓  LIMPIEZACOMPLETA",
                                  fg_color="#001A00", text_color=NEON_GREEN)
        threading.Thread(target=self._scan, daemon=True).start()
