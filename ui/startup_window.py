import customtkinter as ctk
import threading
from core.startup_manager import get_startup_entries, disable_entry, enable_entry
from ui.rgb_engine import RGBEngine
from ui.glass import glass_header_row, apply_window_glass, GLASS_BG, GLASS_BORDER

DARK_BG     = "#0A0A0F"
CARD_BG     = "#0F0F1A"
NEON_GREEN  = "#00FF87"
NEON_BLUE   = "#00D4FF"
NEON_RED    = "#FF4444"
NEON_GOLD   = "#FFD700"
CARD_BORDER = "#1A1A2E"


class StartupWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("DrxOpti — Startup Manager")
        self.geometry("700x520")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.grab_set()

        self._entries  = []
        self._switches = {}
        self._rgb      = RGBEngine(self)
        apply_window_glass(self, 0.97)

        self._build_ui()
        threading.Thread(target=self._load, daemon=True).start()

    def _build_ui(self):
        hdr, title_lbl = glass_header_row(
            self, "🚀  STARTUP MANAGER",
            "Desactiva programas que ralentizan el arranque de Windows",
            NEON_GREEN,
        )
        self._rgb.register(title_lbl, mode="text", speed=0.8)

        self._count_label = ctk.CTkLabel(hdr, text="Cargando...",
                                         font=ctk.CTkFont("Consolas", 9), text_color="#445566")
        self._count_label.place(relx=1.0, x=-16, rely=0.5, anchor="e")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=DARK_BG,
                                              scrollbar_button_color=CARD_BORDER)
        self._scroll.pack(fill="both", expand=True, padx=12, pady=10)

        footer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=48)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        ctk.CTkButton(footer, text="CERRAR",
                      font=ctk.CTkFont("Consolas", 11, "bold"),
                      fg_color="#0A0A14", hover_color="#111122",
                      text_color="#445566", border_color=CARD_BORDER, border_width=1,
                      corner_radius=6, height=32, width=120,
                      command=self._close).place(relx=1.0, x=-16, rely=0.5, anchor="e")

    def _load(self):
        entries = get_startup_entries()
        self.after(0, lambda: self._populate(entries))

    def _populate(self, entries):
        self._entries = entries
        for w in self._scroll.winfo_children():
            w.destroy()
        self._switches.clear()

        safe   = [e for e in entries if e["safe"]]
        unsafe = [e for e in entries if not e["safe"]]

        if safe:
            self._section_header("RECOMENDADOS PARA DESACTIVAR", NEON_GREEN)
            for e in safe:
                self._entry_row(e)

        if unsafe:
            self._section_header("SISTEMA / DESCONOCIDOS", "#445566")
            for e in unsafe:
                self._entry_row(e)

        self._count_label.configure(text=f"{len(entries)} programas en startup")

    def _section_header(self, text, color):
        ctk.CTkLabel(self._scroll, text=text,
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color=color).pack(anchor="w", padx=8, pady=(12, 4))

    def _entry_row(self, entry):
        row = ctk.CTkFrame(self._scroll, fg_color=CARD_BG, corner_radius=8,
                           border_width=1, border_color=CARD_BORDER)
        row.pack(fill="x", pady=3, padx=4)

        color = NEON_GREEN if entry["safe"] else "#445566"

        name_lbl = ctk.CTkLabel(row, text=entry["name"][:38],
                                font=ctk.CTkFont("Consolas", 11, "bold"),
                                text_color=color, anchor="w")
        name_lbl.pack(side="left", padx=14, pady=(8, 2), fill="x", expand=True)

        exe_lbl = ctk.CTkLabel(row, text=entry["exe"][:50],
                               font=ctk.CTkFont("Consolas", 9),
                               text_color="#334455", anchor="w")
        exe_lbl.place(x=14, rely=0.72, anchor="w")

        sw = ctk.CTkSwitch(row, text="",
                           onvalue=True, offvalue=False,
                           progress_color=NEON_GREEN,
                           button_color="#00CC66",
                           fg_color="#0A0A14",
                           width=44)
        sw.select()
        sw.pack(side="right", padx=14, pady=10)
        sw.configure(command=lambda e=entry, s=sw: self._toggle(e, s))
        self._switches[entry["name"]] = sw

    def _toggle(self, entry, switch):
        enabled = switch.get()
        def run():
            if enabled:
                enable_entry(entry)
            else:
                disable_entry(entry)
        threading.Thread(target=run, daemon=True).start()

    def _close(self):
        self._rgb.stop()
        self.grab_release()
        self.destroy()
