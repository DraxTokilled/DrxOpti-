import customtkinter as ctk
import os
from tkinter import filedialog
from core.custom_games import load, add, remove
from ui.rgb_engine import RGBEngine
from ui.glass import glass_header_row, apply_window_glass, GLASS_BG, GLASS_BORDER

DARK_BG    = "#0A0A0F"
CARD_BG    = "#0F0F1A"
NEON_GREEN = "#00FF87"
NEON_BLUE  = "#00D4FF"
NEON_RED   = "#FF4444"
CARD_BORDER= "#1A1A2E"

DEFAULT_GAMES = {
    "FortniteClient-Win64-Shipping.exe": "Fortnite",
    "VALORANT-Win64-Shipping.exe":       "Valorant",
    "cs2.exe":                           "CS2",
    "ModernWarfare4.exe":               "Warzone",
    "r5apex.exe":                        "Apex Legends",
}


class CustomGamesWindow(ctk.CTkToplevel):
    def __init__(self, master, on_save=None):
        super().__init__(master)
        self.title("DrxOpti — Juegos Detectados")
        self.geometry("580x500")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.grab_set()

        self._on_save = on_save
        self._rgb     = RGBEngine(self)
        apply_window_glass(self, 0.97)
        self._build_ui()
        self._reload()

    def _build_ui(self):
        hdr, title_lbl = glass_header_row(
            self, "🎮  JUEGOS PERSONALIZADOS",
            "Agrega cualquier juego al Modo Tryhard",
            NEON_BLUE,
        )
        self._rgb.register(title_lbl, mode="text", offset=120)

        body = ctk.CTkFrame(self, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=14, pady=10)

        # Agregar nuevo
        add_card = ctk.CTkFrame(body, fg_color=GLASS_BG, corner_radius=10,
                                border_width=1, border_color=GLASS_BORDER)
        add_card.pack(fill="x", pady=(0, 10))
        self._rgb.register(add_card, mode="border", offset=60, speed=0.55, sat=0.85)

        add_inner = ctk.CTkFrame(add_card, fg_color="transparent")
        add_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(add_inner, text="AGREGAR JUEGO",
                     font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=NEON_BLUE).pack(anchor="w", pady=(0, 8))

        row1 = ctk.CTkFrame(add_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))

        self._name_entry = ctk.CTkEntry(row1, placeholder_text="Nombre (ej: Minecraft)",
                                        font=ctk.CTkFont("Consolas", 11),
                                        fg_color="#080810", border_color="#1A1A2E",
                                        height=36)
        self._name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._exe_entry = ctk.CTkEntry(row1, placeholder_text="proceso.exe",
                                       font=ctk.CTkFont("Consolas", 11),
                                       fg_color="#080810", border_color="#1A1A2E",
                                       height=36, width=180)
        self._exe_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(row1, text="📁",
                      font=ctk.CTkFont("Consolas", 12),
                      fg_color="#0A0A14", hover_color="#111122",
                      text_color="#445566", border_color=CARD_BORDER, border_width=1,
                      corner_radius=6, height=36, width=36,
                      command=self._browse).pack(side="left", padx=(0, 8))

        ctk.CTkButton(add_inner, text="+ AGREGAR",
                      font=ctk.CTkFont("Consolas", 11, "bold"),
                      fg_color="#001122", hover_color="#001833",
                      text_color=NEON_BLUE, border_color=NEON_BLUE, border_width=1,
                      corner_radius=6, height=34,
                      command=self._add).pack(fill="x")

        # Lista
        ctk.CTkLabel(body, text="JUEGOS REGISTRADOS",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color="#445566").pack(anchor="w", padx=4, pady=(0, 4))

        self._list = ctk.CTkScrollableFrame(body, fg_color=CARD_BG, corner_radius=10,
                                            scrollbar_button_color=CARD_BORDER)
        self._list.pack(fill="both", expand=True)

        ctk.CTkButton(body, text="GUARDAR Y CERRAR",
                      font=ctk.CTkFont("Consolas", 11, "bold"),
                      fg_color="#001A00", hover_color="#002500",
                      text_color=NEON_GREEN, border_color=NEON_GREEN, border_width=1,
                      corner_radius=6, height=38,
                      command=self._save_close).pack(fill="x", pady=(8, 0))

    def _reload(self):
        for w in self._list.winfo_children():
            w.destroy()

        custom = load()
        all_games = {**DEFAULT_GAMES, **custom}

        for exe, name in all_games.items():
            is_default = exe in DEFAULT_GAMES
            self._game_row(exe, name, is_default)

    def _game_row(self, exe, name, is_default):
        row = ctk.CTkFrame(self._list, fg_color="#080810", corner_radius=6)
        row.pack(fill="x", pady=3, padx=4)

        color = "#334455" if is_default else NEON_GREEN
        badge = "  DEFAULT  " if is_default else "  CUSTOM  "
        badge_bg = "#0A0A14" if is_default else "#001A00"

        ctk.CTkLabel(row, text=name, font=ctk.CTkFont("Consolas", 11, "bold"),
                     text_color=color, anchor="w").pack(side="left", padx=12, pady=(6, 2))
        ctk.CTkLabel(row, text=exe, font=ctk.CTkFont("Consolas", 9),
                     text_color="#223333", anchor="w").place(x=12, rely=0.72, anchor="w")
        ctk.CTkLabel(row, text=badge, font=ctk.CTkFont("Consolas", 8, "bold"),
                     text_color=color, fg_color=badge_bg, corner_radius=4).pack(side="right", padx=8)

        if not is_default:
            ctk.CTkButton(row, text="✕", font=ctk.CTkFont("Consolas", 10, "bold"),
                          fg_color="#1A0000", hover_color="#330000",
                          text_color=NEON_RED, border_color=NEON_RED, border_width=1,
                          corner_radius=4, height=24, width=28,
                          command=lambda e=exe: self._remove(e)).pack(side="right", padx=(0, 4), pady=8)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecciona el ejecutable del juego",
            filetypes=[("Ejecutable", "*.exe")],
        )
        if path:
            exe = os.path.basename(path)
            self._exe_entry.delete(0, "end")
            self._exe_entry.insert(0, exe)
            if not self._name_entry.get():
                self._name_entry.insert(0, exe.replace(".exe", "").replace("-", " ").title())

    def _add(self):
        name = self._name_entry.get().strip()
        exe  = self._exe_entry.get().strip()
        if not name or not exe:
            return
        if not exe.endswith(".exe"):
            exe += ".exe"
        add(name, exe)
        self._name_entry.delete(0, "end")
        self._exe_entry.delete(0, "end")
        self._reload()

    def _remove(self, exe):
        remove(exe)
        self._reload()

    def _save_close(self):
        if self._on_save:
            self._on_save()
        self._rgb.stop()
        self.grab_release()
        self.destroy()
