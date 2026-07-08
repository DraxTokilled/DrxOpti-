import customtkinter as ctk
import os
from tkinter import filedialog
from core.whitelist import load, add, remove, DEFAULT_WHITELIST
from ui.rgb_engine import RGBEngine
from ui.glass import glass_header_row, apply_window_glass, GLASS_BG, GLASS_BORDER

DARK_BG    = "#0A0A0F"
CARD_BG    = "#0F0F1A"
NEON_GREEN = "#00FF87"
NEON_BLUE  = "#00D4FF"
NEON_RED   = "#FF4444"
NEON_GOLD  = "#FFD700"
CARD_BORDER= "#1A1A2E"


class WhitelistWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("DrxOpti — Whitelist de Procesos")
        self.geometry("560x520")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.grab_set()

        self._rgb = RGBEngine(self)
        apply_window_glass(self, 0.97)
        self._build_ui()
        self._reload()

    def _build_ui(self):
        hdr, title_lbl = glass_header_row(
            self, "🛡  PROCESOS PROTEGIDOS",
            "Estos programas NUNCA serán cerrados por el Modo Tryhard",
            NEON_GOLD,
        )
        self._rgb.register(title_lbl, mode="text", speed=0.5, sat=0.8)

        body = ctk.CTkFrame(self, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=14, pady=10)

        # Aviso
        warning = ctk.CTkFrame(body, fg_color="#100A00", corner_radius=8,
                                border_width=1, border_color="#332200")
        warning.pack(fill="x", pady=(0, 10))
        self._rgb.register(warning, mode="border", offset=30, speed=0.4, sat=0.7)

        ctk.CTkLabel(warning,
                     text="⚠  Si estás en llamada de Discord o streamando, agrégalos aquí para que no se cierren.",
                     font=ctk.CTkFont("Consolas", 9),
                     text_color=NEON_GOLD,
                     wraplength=500, justify="left").pack(padx=14, pady=10)

        # Agregar proceso
        add_card = ctk.CTkFrame(body, fg_color=GLASS_BG, corner_radius=10,
                                border_width=1, border_color=GLASS_BORDER)
        add_card.pack(fill="x", pady=(0, 10))
        self._rgb.register(add_card, mode="border", offset=90, speed=0.5)

        add_row = ctk.CTkFrame(add_card, fg_color="transparent")
        add_row.pack(fill="x", padx=14, pady=12)

        self._exe_entry = ctk.CTkEntry(add_row, placeholder_text="proceso.exe",
                                       font=ctk.CTkFont("Consolas", 11),
                                       fg_color="#080810", border_color="#1A1A2E",
                                       height=36)
        self._exe_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(add_row, text="📁",
                      font=ctk.CTkFont("Consolas", 12),
                      fg_color="#0A0A14", hover_color="#111122",
                      text_color="#445566", border_color=CARD_BORDER, border_width=1,
                      corner_radius=6, height=36, width=36,
                      command=self._browse).pack(side="left", padx=(0, 8))

        ctk.CTkButton(add_row, text="+ PROTEGER",
                      font=ctk.CTkFont("Consolas", 11, "bold"),
                      fg_color="#1A1000", hover_color="#221600",
                      text_color=NEON_GOLD, border_color=NEON_GOLD, border_width=1,
                      corner_radius=6, height=36, width=130,
                      command=self._add).pack(side="left")

        # Lista
        ctk.CTkLabel(body, text="PROTEGIDOS ACTUALMENTE",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color="#445566").pack(anchor="w", padx=4, pady=(0, 4))

        self._list = ctk.CTkScrollableFrame(body, fg_color=CARD_BG, corner_radius=10,
                                            scrollbar_button_color=CARD_BORDER)
        self._list.pack(fill="both", expand=True)

        ctk.CTkButton(body, text="GUARDAR Y CERRAR",
                      font=ctk.CTkFont("Consolas", 11, "bold"),
                      fg_color="#1A1000", hover_color="#221600",
                      text_color=NEON_GOLD, border_color=NEON_GOLD, border_width=1,
                      corner_radius=6, height=38,
                      command=self._close).pack(fill="x", pady=(8, 0))

    def _reload(self):
        for w in self._list.winfo_children():
            w.destroy()
        entries = load()
        for exe in entries:
            self._entry_row(exe)

    def _entry_row(self, exe: str):
        is_default = exe in DEFAULT_WHITELIST
        row = ctk.CTkFrame(self._list, fg_color="#080810", corner_radius=6)
        row.pack(fill="x", pady=3, padx=4)

        icon = "🎙" if "discord" in exe.lower() or "voice" in exe.lower() or "cable" in exe.lower() else \
               "📹" if "obs" in exe.lower() or "stream" in exe.lower() else "🛡"
        color = NEON_GOLD if is_default else NEON_GREEN

        ctk.CTkLabel(row, text=f"{icon}  {exe}",
                     font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=color, anchor="w").pack(side="left", padx=12, pady=10)

        badge_text = "  DEFAULT  " if is_default else "  CUSTOM  "
        badge_bg   = "#0A0800" if is_default else "#001A00"
        ctk.CTkLabel(row, text=badge_text,
                     font=ctk.CTkFont("Consolas", 8, "bold"),
                     text_color=color, fg_color=badge_bg, corner_radius=4).pack(side="right", padx=(4, 8))

        ctk.CTkButton(row, text="✕",
                      font=ctk.CTkFont("Consolas", 10, "bold"),
                      fg_color="#1A0000", hover_color="#330000",
                      text_color=NEON_RED, border_color=NEON_RED, border_width=1,
                      corner_radius=4, height=24, width=28,
                      command=lambda e=exe: self._remove(e)).pack(side="right", padx=4, pady=8)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecciona el proceso a proteger",
            filetypes=[("Ejecutable", "*.exe")],
        )
        if path:
            self._exe_entry.delete(0, "end")
            self._exe_entry.insert(0, os.path.basename(path))

    def _add(self):
        exe = self._exe_entry.get().strip()
        if not exe:
            return
        if not exe.endswith(".exe"):
            exe += ".exe"
        add(exe)
        self._exe_entry.delete(0, "end")
        self._reload()

    def _remove(self, exe: str):
        remove(exe)
        self._reload()

    def _close(self):
        self._rgb.stop()
        self.grab_release()
        self.destroy()
