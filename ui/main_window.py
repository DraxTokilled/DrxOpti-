import customtkinter as ctk
import threading
import time
import webbrowser
from core.game_watcher import GameWatcher
from core.hardware_profile import get_hardware_profile
from core.network_optimizer import apply_network_tweaks, NETWORK_TWEAKS
from core.timer_resolution import get_current_resolution, set_gaming_resolution, restore_default_resolution, apply_bcdedit_timer
from core.snapshot import capture_snapshot, compare_snapshots
from core.license_manager import get_license, is_pro
from ui.animations import pulse_button, fade_text, flash_border
from ui.sparkline import SparklineWidget
from ui.optimize_all import OptimizeAllOverlay
from ui.rgb_engine import RGBEngine, RGBLabel
from ui.startup_window import StartupWindow
from ui.shader_window import ShaderWindow
from ui.custom_games_window import CustomGamesWindow
from ui.whitelist_window import WhitelistWindow
from core.updater import check_async
from core.custom_games import load as load_custom_games
from ui.glass import apply_window_glass, GLASS_BG, GLASS_BORDER
from ui.tooltip import Tooltip
from core.vip_monitor import VipMonitor, jitter_rating, temp_rating
from core.dns_boost import apply_dns, restore_dhcp_dns, DNS_PROVIDERS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NEON_GREEN  = "#00FF87"
NEON_BLUE   = "#00D4FF"
NEON_RED    = "#FF4444"
NEON_GOLD   = "#FFD700"
DARK_BG     = "#06060B"   # negro profundo — base de toda la app
RAIL_BG     = "#0A0A12"   # rail de navegación, un paso más claro
CARD_BG     = "#0D0D16"   # cards
CARD_HOVER  = "#12121E"   # cards al hover
CARD_BORDER = "#1C1C2E"   # bordes sutiles
TEXT_DIM    = "#3A4455"   # texto secundario
TEXT_MID    = "#66788C"   # texto medio


class DrxOptiApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DrxOpti — Gaming Optimizer")
        self.geometry("1050x680")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        apply_window_glass(self, 0.98)

        self._tryhard_active = False
        self._watcher        = None
        self._hw             = get_hardware_profile()
        self._license        = get_license()
        self._snapshot_before = None
        self._current_score   = 0
        self._blink_state     = False
        self._net_applied     = False
        self._timer_applied   = False

        self._build_ui()
        self._rgb = RGBEngine(self)
        self._apply_rgb()
        self._start_stats_loop()
        check_async(self._on_update_check)

        self._vip_monitor = VipMonitor(on_update=self._on_vip_update)
        self._vip_monitor.start()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Nav rail vertical (estilo Discord/Spotify) ────────────────────────
        rail = ctk.CTkFrame(self, fg_color=RAIL_BG, corner_radius=0, width=190)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        self._build_rail(rail)

        # ── Columna principal ─────────────────────────────────────────────────
        main_col = ctk.CTkFrame(self, fg_color=DARK_BG)
        main_col.pack(side="left", fill="both", expand=True)

        self._build_header(main_col)

        body = ctk.CTkFrame(main_col, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        # Contenedor de secciones — se intercambian con el rail
        self._content = ctk.CTkFrame(body, fg_color=DARK_BG)
        self._content.pack(side="left", fill="both", expand=True)

        right = ctk.CTkFrame(body, fg_color=DARK_BG, width=300)
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)

        # Secciones
        self._sections = {}
        for key in ("home", "pro", "stats"):
            self._sections[key] = ctk.CTkFrame(self._content, fg_color=DARK_BG)

        self._build_hero_button(self._sections["home"])
        self._build_tryhard_card(self._sections["home"])
        self._build_quickstart_card(self._sections["home"])
        self._build_pro_tools_card(self._sections["pro"])
        self._build_stats_card(self._sections["stats"])

        self._build_status_panel(right)
        self._build_vip_monitor_panel(right)
        self._build_before_after_panel(right)
        self._build_log_panel(right)

        self._show_section("home")

    def _build_rail(self, rail):
        # Logo
        logo_row = ctk.CTkFrame(rail, fg_color="transparent")
        logo_row.pack(fill="x", padx=18, pady=(22, 4))
        self._logo_drx = ctk.CTkLabel(logo_row, text="DRX", font=ctk.CTkFont("Consolas", 24, "bold"), text_color=NEON_GREEN)
        self._logo_drx.pack(side="left")
        self._logo_opti = ctk.CTkLabel(logo_row, text="OPTI", font=ctk.CTkFont("Consolas", 24, "bold"), text_color=NEON_BLUE)
        self._logo_opti.pack(side="left")

        ctk.CTkLabel(rail, text="GAMING OPTIMIZER  v1.1",
                     font=ctk.CTkFont("Consolas", 8), text_color=TEXT_DIM).pack(anchor="w", padx=20)

        ctk.CTkFrame(rail, fg_color=CARD_BORDER, height=1).pack(fill="x", padx=16, pady=14)

        # Navegación
        self._nav_buttons = {}
        nav_items = [
            ("home",  "⚡", "Inicio",      NEON_GREEN),
            ("pro",   "★", "PRO Tools",   NEON_GOLD),
            ("stats", "◈", "Diagnóstico", NEON_BLUE),
        ]
        for key, icon, label, color in nav_items:
            btn = ctk.CTkButton(
                rail, text=f"  {icon}   {label}",
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                fg_color="transparent", hover_color=CARD_HOVER,
                text_color=TEXT_MID, anchor="w",
                corner_radius=8, height=42,
                command=lambda k=key: self._show_section(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = (btn, color)

        ctk.CTkFrame(rail, fg_color=CARD_BORDER, height=1).pack(fill="x", padx=16, pady=14)

        # Herramientas rápidas
        ctk.CTkLabel(rail, text="HERRAMIENTAS",
                     font=ctk.CTkFont("Consolas", 8, "bold"), text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(0, 4))

        quick_tools = [
            ("🧹  Shader Cleaner",   self._open_shader),
            ("🚀  Startup Manager",  self._open_startup),
            ("🛡  Proteger Proceso", self._open_whitelist),
            ("🌐  DNS Boost",        self._boost_dns),
        ]
        for text, cmd in quick_tools:
            ctk.CTkButton(
                rail, text=f"  {text}",
                font=ctk.CTkFont("Segoe UI", 11),
                fg_color="transparent", hover_color=CARD_HOVER,
                text_color=TEXT_MID, anchor="w",
                corner_radius=8, height=34,
                command=cmd,
            ).pack(fill="x", padx=10, pady=1)

        # Badge de licencia al fondo del rail
        tier = self._license.get("tier", "free")
        tier_text  = "★  DRXOPTI PRO" if tier == "pro" else "◇  VERSIÓN FREE"
        tier_color = NEON_GOLD if tier == "pro" else TEXT_MID

        self._tier_badge = ctk.CTkButton(
            rail, text=tier_text,
            font=ctk.CTkFont("Consolas", 10, "bold"),
            fg_color=CARD_BG, hover_color=CARD_HOVER,
            text_color=tier_color, border_color=CARD_BORDER, border_width=1,
            corner_radius=8, height=36,
            command=self._open_license_modal,
        )
        self._tier_badge.pack(side="bottom", fill="x", padx=12, pady=14)

    _SECTION_TITLES = {
        "home":  "Panel de Control",
        "pro":   "Herramientas PRO",
        "stats": "Diagnóstico en Vivo",
    }

    def _show_section(self, key: str):
        for k, frame in self._sections.items():
            frame.pack_forget()
        self._sections[key].pack(fill="both", expand=True)
        self._header_title.configure(text=self._SECTION_TITLES.get(key, ""))

        for k, (btn, color) in self._nav_buttons.items():
            if k == key:
                btn.configure(text_color=color, fg_color=CARD_BG)
            else:
                btn.configure(text_color=TEXT_MID, fg_color="transparent")

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=DARK_BG, corner_radius=0, height=52)
        header.pack(fill="x", padx=16, pady=(12, 0))
        header.pack_propagate(False)

        self._header_title = ctk.CTkLabel(header, text="Panel de Control",
                                          font=ctk.CTkFont("Segoe UI", 18, "bold"),
                                          text_color="#CCDDEE")
        self._header_title.pack(side="left")

        hw_text = f"{self._hw['cpu'].split(' with')[0]}   ·   {self._hw['gpu']}   ·   {self._hw['ram_gb']} GB"
        ctk.CTkLabel(
            header, text=hw_text,
            font=ctk.CTkFont("Consolas", 9), text_color=TEXT_DIM,
        ).pack(side="right")

    def _build_hero_button(self, parent):
        card = ctk.CTkFrame(parent, fg_color="#050510", corner_radius=14, border_width=2, border_color=NEON_GREEN)
        card.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=18)

        left_info = ctk.CTkFrame(inner, fg_color="transparent")
        left_info.pack(side="left", fill="y")

        ctk.CTkLabel(left_info, text="OPTIMIZAR TODO", font=ctk.CTkFont("Consolas", 18, "bold"), text_color=NEON_GREEN).pack(anchor="w")
        ctk.CTkLabel(
            left_info,
            text="Todo en un clic: red, RAM, CPU, timer y test de ping.",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_MID,
        ).pack(anchor="w", pady=(2, 0))

        self._hero_btn = ctk.CTkButton(
            inner,
            text="⚡  OPTIMIZAR AHORA",
            font=ctk.CTkFont("Consolas", 14, "bold"),
            fg_color=NEON_GREEN,
            hover_color="#00CC6A",
            text_color="#000000",
            corner_radius=8,
            height=50,
            width=220,
            command=self._launch_optimize_all,
        )
        self._hero_btn.pack(side="right")

    def _build_tryhard_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(card, text="⚡  MODO TRYHARD", font=ctk.CTkFont("Consolas", 13, "bold"), text_color=NEON_GREEN).pack(anchor="w", padx=20, pady=(16, 2))
        ctk.CTkLabel(card, text="Detecta tu juego automáticamente y optimiza la PC al instante.", font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_MID).pack(anchor="w", padx=20)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=12)

        self._tryhard_btn = ctk.CTkButton(
            row, text="ACTIVAR MODO TRYHARD",
            font=ctk.CTkFont("Consolas", 12, "bold"),
            fg_color="#003322", hover_color="#004433",
            text_color=NEON_GREEN, border_color=NEON_GREEN, border_width=1,
            corner_radius=6, height=40, width=260,
            command=self._toggle_tryhard,
        )
        self._tryhard_btn.pack(side="left")

        self._tryhard_status_label = ctk.CTkLabel(row, text="●  INACTIVO", font=ctk.CTkFont("Consolas", 11, "bold"), text_color="#333355")
        self._tryhard_status_label.pack(side="left", padx=20)

        bar = ctk.CTkFrame(card, fg_color="#080810", corner_radius=6)
        bar.pack(fill="x", padx=20, pady=(0, 8))

        self._games_label = ctk.CTkLabel(bar, text="Fortnite  ·  Valorant  ·  CS2  ·  Warzone  ·  Apex Legends",
                                         font=ctk.CTkFont("Consolas", 9), text_color="#334455")
        self._games_label.pack(side="left", padx=12, pady=6)

        ctk.CTkButton(bar, text="+ Agregar juego",
                      font=ctk.CTkFont("Consolas", 9),
                      fg_color="transparent", hover_color="#080818",
                      text_color="#334466", border_width=0, height=24,
                      command=self._open_custom_games).pack(side="right", padx=8)

        ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    def _build_quickstart_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color="#08080E", corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(card, text="CÓMO EMPEZAR", font=ctk.CTkFont("Consolas", 10, "bold"), text_color="#445566").pack(anchor="w", padx=20, pady=(12, 6))

        steps = [
            ("1", "Pulsa OPTIMIZAR AHORA para el boost completo", NEON_GREEN),
            ("2", "Activa MODO TRYHARD y déjalo en segundo plano", NEON_BLUE),
            ("3", "Abre tu juego — la PC se optimiza sola", NEON_GOLD),
        ]
        for num, text, color in steps:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=num, font=ctk.CTkFont("Consolas", 12, "bold"),
                         text_color=color, fg_color="#0A0A14", corner_radius=6,
                         width=26, height=26).pack(side="left")
            ctk.CTkLabel(row, text=text, font=ctk.CTkFont("Segoe UI", 11),
                         text_color=TEXT_MID).pack(side="left", padx=10)

        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()

    def _build_pro_tools_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=(0, 8))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(14, 8))
        ctk.CTkLabel(hdr, text="🔧  HERRAMIENTAS PRO", font=ctk.CTkFont("Consolas", 13, "bold"), text_color=NEON_BLUE).pack(side="left")
        ctk.CTkLabel(hdr, text="  ★ PRO  ", font=ctk.CTkFont("Consolas", 9, "bold"), text_color=NEON_GOLD, fg_color="#1A1400", corner_radius=4).pack(side="left", padx=8)

        tools_row = ctk.CTkFrame(card, fg_color="transparent")
        tools_row.pack(fill="x", padx=20, pady=(0, 8))

        # Network Optimizer
        net_frame = ctk.CTkFrame(tools_row, fg_color="#080810", corner_radius=8)
        net_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        ctk.CTkLabel(net_frame, text="🌐  RED", font=ctk.CTkFont("Consolas", 10, "bold"), text_color=NEON_BLUE).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(net_frame, text="Nagle off · CTCP · DNS boost\nReduce ping y paquetes perdidos.", font=ctk.CTkFont("Consolas", 9), text_color="#445566").pack(anchor="w", padx=12)

        self._net_btn = ctk.CTkButton(
            net_frame, text="OPTIMIZAR RED",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            fg_color="#001122", hover_color="#001833",
            text_color=NEON_BLUE, border_color=NEON_BLUE, border_width=1,
            corner_radius=6, height=32,
            command=self._apply_network,
        )
        self._net_btn.pack(fill="x", padx=12, pady=(8, 12))

        # Timer Resolution
        timer_frame = ctk.CTkFrame(tools_row, fg_color="#080810", corner_radius=8)
        timer_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))

        ctk.CTkLabel(timer_frame, text="⏱  TIMER", font=ctk.CTkFont("Consolas", 10, "bold"), text_color=NEON_GREEN).pack(anchor="w", padx=12, pady=(10, 2))

        timer_ms = get_current_resolution()
        ctk.CTkLabel(timer_frame, text=f"Actual: {timer_ms:.1f}ms → Meta: 0.5ms\nReduce input lag medible.", font=ctk.CTkFont("Consolas", 9), text_color="#445566").pack(anchor="w", padx=12)

        self._timer_btn = ctk.CTkButton(
            timer_frame, text="APLICAR TIMER",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            fg_color="#001A00", hover_color="#002200",
            text_color=NEON_GREEN, border_color=NEON_GREEN, border_width=1,
            corner_radius=6, height=32,
            command=self._apply_timer,
        )
        self._timer_btn.pack(fill="x", padx=12, pady=(8, 12))

        # Discord VIP
        discord_frame = ctk.CTkFrame(card, fg_color="#08080E", corner_radius=8, border_width=1, border_color="#1A1A35")
        discord_frame.pack(fill="x", padx=20, pady=(0, 14))

        disc_left = ctk.CTkFrame(discord_frame, fg_color="transparent")
        disc_left.pack(side="left", fill="y", padx=(14, 0), pady=10)

        ctk.CTkLabel(disc_left, text="💬  COMUNIDAD VIP", font=ctk.CTkFont("Consolas", 10, "bold"), text_color="#7289DA").pack(anchor="w")
        ctk.CTkLabel(disc_left, text="Soporte directo · Perfiles exclusivos · Canal PRO only", font=ctk.CTkFont("Consolas", 9), text_color="#334455").pack(anchor="w")

        self._discord_btn = ctk.CTkButton(
            discord_frame,
            text="UNIRSE AL DISCORD  →",
            font=ctk.CTkFont("Consolas", 10, "bold"),
            fg_color="#1A1A2E", hover_color="#23234A",
            text_color="#7289DA", border_color="#7289DA", border_width=1,
            corner_radius=6, height=32, width=180,
            command=self._open_discord,
        )
        self._discord_btn.pack(side="right", padx=14, pady=10)

    def _build_stats_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(card, text="📊  DIAGNÓSTICO DEL SISTEMA", font=ctk.CTkFont("Consolas", 13, "bold"), text_color=NEON_BLUE).pack(anchor="w", padx=20, pady=(14, 10))

        metrics = ctk.CTkFrame(card, fg_color="transparent")
        metrics.pack(fill="x", padx=20, pady=(0, 8))
        metrics.columnconfigure((0, 1), weight=1)

        self._cpu_bar, self._cpu_label = self._make_metric(metrics, "CPU", NEON_GREEN, 0, 0)
        self._ram_bar, self._ram_label = self._make_metric(metrics, "RAM", NEON_BLUE, 0, 1)

        # Sparkline — gráfico de tendencia en tiempo real
        self._sparkline = SparklineWidget(card, height=180)
        self._sparkline.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self._score_label = ctk.CTkLabel(
            card, text="NIVEL:  Calculando...  ›",
            font=ctk.CTkFont("Consolas", 12, "bold"),
            text_color="#445566", cursor="hand2",
        )
        self._score_label.pack(anchor="w", padx=20, pady=(0, 14))
        self._score_label.bind("<Button-1>", lambda e: self._open_score_modal())

    def _make_metric(self, parent, name, color, row, col):
        frame = ctk.CTkFrame(parent, fg_color="#080810", corner_radius=8)
        frame.grid(row=row, column=col, padx=6, pady=4, sticky="ew")
        ctk.CTkLabel(frame, text=name, font=ctk.CTkFont("Consolas", 10), text_color="#445566").pack(anchor="w", padx=12, pady=(10, 2))
        bar = ctk.CTkProgressBar(frame, height=8, corner_radius=4, fg_color="#0A0A14", progress_color=color)
        bar.set(0)
        bar.pack(fill="x", padx=12, pady=(0, 4))
        lbl = ctk.CTkLabel(frame, text="0%", font=ctk.CTkFont("Consolas", 10, "bold"), text_color=color)
        lbl.pack(anchor="e", padx=12, pady=(0, 10))
        return bar, lbl

    def _build_status_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(card, text="ESTADO", font=ctk.CTkFont("Consolas", 11, "bold"), text_color="#445566").pack(anchor="w", padx=16, pady=(14, 6))

        self._game_label = ctk.CTkLabel(card, text="Sin juego activo", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=TEXT_MID)
        self._game_label.pack(anchor="w", padx=16, pady=(0, 4))

        self._game_active_badge = ctk.CTkLabel(card, text="", font=ctk.CTkFont("Consolas", 9, "bold"), text_color=NEON_GREEN, fg_color="transparent", corner_radius=4)
        self._game_active_badge.pack(anchor="w", padx=16, pady=(0, 14))

    def _build_vip_monitor_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color="#1A1400")
        card.pack(fill="x", pady=(0, 8))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 8))
        self._vip_title = ctk.CTkLabel(hdr, text="⬡ MONITOR VIP",
                                       font=ctk.CTkFont("Consolas", 11, "bold"),
                                       text_color=NEON_GOLD)
        self._vip_title.pack(side="left")

        # GPU temp
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(row1, text="GPU Temp", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=TEXT_DIM, width=76, anchor="w").pack(side="left")
        self._vip_temp = ctk.CTkLabel(row1, text="--°C", font=ctk.CTkFont("Consolas", 11, "bold"),
                                      text_color="#445566", anchor="e")
        self._vip_temp.pack(side="right", fill="x", expand=True)

        # GPU usage / VRAM
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(row2, text="GPU / VRAM", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=TEXT_DIM, width=76, anchor="w").pack(side="left")
        self._vip_gpu = ctk.CTkLabel(row2, text="--", font=ctk.CTkFont("Consolas", 10, "bold"),
                                     text_color="#445566", anchor="e")
        self._vip_gpu.pack(side="right", fill="x", expand=True)

        # Jitter del sistema
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(row3, text="Fluidez", font=ctk.CTkFont("Segoe UI", 10),
                     text_color=TEXT_DIM, width=76, anchor="w").pack(side="left")
        self._vip_jitter = ctk.CTkLabel(row3, text="--", font=ctk.CTkFont("Consolas", 10, "bold"),
                                        text_color="#445566", anchor="e")
        self._vip_jitter.pack(side="right", fill="x", expand=True)

        Tooltip(self._vip_jitter, "Overshoot promedio del scheduler de Windows.\nBaja al aplicar el Timer de 0.5ms — pruébalo\ny mira cómo cambia este número en vivo.")
        Tooltip(self._vip_temp, "Temperatura real de tu GPU vía nvidia-smi.\n+85°C = thermal throttling (pierdes FPS).")

        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _build_before_after_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(card, text="ANTES / DESPUÉS", font=ctk.CTkFont("Consolas", 11, "bold"), text_color="#445566").pack(anchor="w", padx=16, pady=(14, 8))

        self._ba_ram = self._make_ba_row(card, "RAM liberada", "--")
        self._ba_procs = self._make_ba_row(card, "Procesos cerrados", "--")
        self._ba_cpu = self._make_ba_row(card, "CPU delta", "--")

        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _make_ba_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=2)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont("Consolas", 9), text_color="#334455", width=120, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=value, font=ctk.CTkFont("Consolas", 9, "bold"), text_color="#445566")
        val_lbl.pack(side="right")
        return val_lbl

    def _build_extra_tools_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(card, text="HERRAMIENTAS",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color="#445566").pack(anchor="w", padx=14, pady=(12, 6))

        tools = [
            ("🧹  Shader Cleaner",   NEON_GREEN, self._open_shader),
            ("🚀  Startup Manager",  NEON_BLUE,  self._open_startup),
            ("🛡  Proteger Proceso", NEON_GOLD,  self._open_whitelist),
            ("🌐  DNS Boost",        NEON_BLUE,  self._boost_dns),
        ]
        for text, color, cmd in tools:
            btn = ctk.CTkButton(
                card, text=text,
                font=ctk.CTkFont("Consolas", 10, "bold"),
                fg_color="#080810", hover_color="#0F0F1A",
                text_color=color, border_color=color, border_width=1,
                corner_radius=6, height=32,
                command=cmd,
            )
            btn.pack(fill="x", padx=10, pady=3)

        ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    def _build_log_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(card, text="LOG", font=ctk.CTkFont("Consolas", 11, "bold"), text_color="#445566").pack(anchor="w", padx=16, pady=(14, 4))

        self._log_box = ctk.CTkTextbox(card, font=ctk.CTkFont("Consolas", 9), fg_color="#080810", text_color="#335544", corner_radius=6, state="disabled")
        self._log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _toggle_tryhard(self):
        if not self._tryhard_active:
            self._snapshot_before = capture_snapshot()
            self._tryhard_active = True
            self._watcher = GameWatcher(on_game_start=self._on_game_start, on_game_stop=self._on_game_stop)
            self._watcher.start()
            self._tryhard_btn.configure(text="DESACTIVAR MODO TRYHARD", fg_color="#220011", hover_color="#330011", text_color=NEON_RED, border_color=NEON_RED)
            self._tryhard_status_label.configure(text="●  ACTIVO", text_color=NEON_GREEN)
            self._log("Modo Tryhard activado. Esperando juego...")
        else:
            self._tryhard_active = False
            if self._watcher:
                self._watcher.stop()
                self._watcher = None
            self._tryhard_btn.configure(text="ACTIVAR MODO TRYHARD", fg_color="#003322", hover_color="#004433", text_color=NEON_GREEN, border_color=NEON_GREEN)
            self._tryhard_status_label.configure(text="●  INACTIVO", text_color="#333355")
            self._game_label.configure(text="Sin juego activo", text_color="#333355")
            self._game_active_badge.configure(text="", fg_color="transparent")
            self._log("Modo Tryhard desactivado.")

    def _apply_network(self):
        if not is_pro():
            flash_border(self._net_btn, NEON_RED, NEON_BLUE)
            self._open_license_modal()
            return

        self._log("Optimizando red...")
        self._net_btn.configure(state="disabled")
        fade_text(self._net_btn, "APLICANDO...", NEON_BLUE, "#001122")

        def run():
            results = apply_network_tweaks()
            ok = sum(1 for v in results.values() if v)
            self._net_applied = True

            def done():
                self._net_btn.configure(state="normal", fg_color="#001A00", border_color=NEON_GREEN)
                fade_text(self._net_btn, f"✓ RED OPTIMIZADA  {ok}/{len(results)}", NEON_GREEN, "#001122")
                pulse_button(self._net_btn, NEON_GREEN, "#FFFFFF", cycles=2)
                flash_border(self._net_btn, "#FFFFFF", NEON_GREEN)
                self._log(f"Red optimizada — {ok}/{len(results)} tweaks aplicados")

            self.after(0, done)

        threading.Thread(target=run, daemon=True).start()

    def _apply_timer(self):
        if not is_pro():
            flash_border(self._timer_btn, NEON_RED, NEON_GREEN)
            self._open_license_modal()
            return

        self._log("Aplicando timer resolution 0.5ms...")
        fade_text(self._timer_btn, "APLICANDO...", NEON_GREEN, "#001A00")
        ok = set_gaming_resolution()
        apply_bcdedit_timer()

        if ok:
            self._timer_applied = True
            self._timer_btn.configure(fg_color="#001A00", border_color=NEON_GREEN)
            fade_text(self._timer_btn, "✓ TIMER 0.5ms ACTIVO", NEON_GREEN, "#001A00")
            pulse_button(self._timer_btn, NEON_GREEN, "#FFFFFF", cycles=2)
            flash_border(self._timer_btn, "#FFFFFF", NEON_GREEN)
            self._log("✓ Timer resolution aplicado — input lag reducido")
        else:
            fade_text(self._timer_btn, "✗ FALLÓ — reinicia admin", NEON_RED, "#001A00")
            self._log("✗ Timer resolution falló — reinicia como admin")

    def _on_game_start(self, game_name):
        snap_after = capture_snapshot()
        if self._snapshot_before:
            diff = compare_snapshots(self._snapshot_before, snap_after)
            self.after(0, lambda: self._update_before_after(diff))

        self.after(0, lambda: self._game_label.configure(text=f"🎮  {game_name}", text_color=NEON_GREEN))
        self.after(0, lambda: self._game_active_badge.configure(text="  ⚡ MODO TRYHARD ACTIVO  ", fg_color="#001A0D"))
        self.after(0, self._start_badge_blink)
        self.after(0, lambda: self._log(f"[GAME ON] {game_name} detectado"))
        self.after(0, lambda: self._log("→ Procesos cerrados · CPU elevada · RAM limpia"))

    def _on_game_stop(self, game_name):
        self.after(0, lambda: self._game_label.configure(text="Sin juego activo", text_color="#333355"))
        self.after(0, lambda: self._game_active_badge.configure(text="", fg_color="transparent"))
        self.after(0, lambda: self._log(f"[GAME OFF] {game_name} — restaurando sistema..."))

    def _update_before_after(self, diff: dict):
        ram = diff["ram_freed_gb"]
        procs = diff["processes_killed"]
        cpu = diff["cpu_delta"]

        ram_color  = NEON_GREEN if ram > 0 else "#445566"
        proc_color = NEON_GREEN if procs > 0 else "#445566"
        cpu_color  = NEON_GREEN if cpu > 0 else "#445566"

        self._ba_ram.configure(text=f"+{ram} GB", text_color=ram_color)
        self._ba_procs.configure(text=f"-{procs}", text_color=proc_color)
        self._ba_cpu.configure(text=f"-{cpu}%", text_color=cpu_color)

    def _start_badge_blink(self):
        if self._watcher and self._watcher.active_game:
            self._blink_state = not self._blink_state
            self._game_active_badge.configure(text_color=NEON_GREEN if self._blink_state else "#007744")
            self.after(600, self._start_badge_blink)

    def _log(self, message: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"> {message}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _start_stats_loop(self):
        def loop():
            import psutil
            while True:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                self.after(0, lambda c=cpu: self._cpu_bar.set(c / 100))
                self.after(0, lambda c=cpu: self._cpu_label.configure(text=f"{c:.0f}%"))
                self.after(0, lambda r=ram: self._ram_bar.set(r / 100))
                self.after(0, lambda r=ram: self._ram_label.configure(text=f"{r:.0f}%"))
                self.after(0, lambda c=cpu, r=ram: self._update_score(c, r))
                self.after(0, lambda c=cpu, r=ram: self._sparkline.push(c, r))
                time.sleep(2)

        threading.Thread(target=loop, daemon=True).start()

    def _update_score(self, cpu, ram):
        self._current_score = 100 - (cpu * 0.5 + ram * 0.5)
        if self._current_score >= 75:
            text, color = "NIVEL:  ✦ MODO COMPETITIVO  ›", NEON_GREEN
        elif self._current_score >= 50:
            text, color = "NIVEL:  ◈ CASI OPTIMIZADO  ›", NEON_BLUE
        else:
            text, color = "NIVEL:  ○ MODO OFICINA  ›", NEON_RED
        self._score_label.configure(text=text, text_color=color)

    # ── Modales ───────────────────────────────────────────────────────────────

    def _launch_optimize_all(self):
        snap = capture_snapshot()
        self._hero_btn.configure(state="disabled", text="EJECUTANDO...")

        def on_done():
            self._hero_btn.configure(state="normal")
            fade_text(self._hero_btn, "⚡  OPTIMIZAR AHORA", "#000000", "#005522")

        OptimizeAllOverlay(self, self._hw, snap, on_complete=on_done)

    def _open_discord(self):
        if not is_pro():
            flash_border(self._discord_btn, NEON_RED, "#7289DA")
            self._open_license_modal()
            return
        pulse_button(self._discord_btn, "#7289DA", "#FFFFFF", cycles=2)
        # Reemplaza este link con tu Discord real
        webbrowser.open("https://discord.gg/acszKrpaG")

    def _open_score_modal(self):
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        modal = ctk.CTkToplevel(self)
        modal.title("Diagnóstico Detallado")
        modal.geometry("500x440")
        modal.resizable(False, False)
        modal.configure(fg_color=DARK_BG)
        modal.grab_set()

        ctk.CTkLabel(modal, text="📊  DIAGNÓSTICO DETALLADO", font=ctk.CTkFont("Consolas", 14, "bold"), text_color=NEON_BLUE).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(modal, text=f"Puntuación: {self._current_score:.0f} / 100", font=ctk.CTkFont("Consolas", 10), text_color="#445566").pack(anchor="w", padx=24, pady=(0, 14))

        scroll = ctk.CTkScrollableFrame(modal, fg_color=CARD_BG, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        for tweak in self._get_pending_tweaks(self._current_score, cpu, ram):
            row = ctk.CTkFrame(scroll, fg_color="#080810", corner_radius=8)
            row.pack(fill="x", pady=4, padx=4)
            color = NEON_GREEN if tweak["done"] else NEON_RED
            ctk.CTkLabel(row, text="✓" if tweak["done"] else "✗", font=ctk.CTkFont("Consolas", 13, "bold"), text_color=color, width=28).pack(side="left", padx=(12, 4), pady=12)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(info, text=tweak["title"], font=ctk.CTkFont("Consolas", 11, "bold"), text_color="#CCDDEE", anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=tweak["desc"], font=ctk.CTkFont("Consolas", 9), text_color="#445566", anchor="w", wraplength=360, justify="left").pack(anchor="w")

        ctk.CTkButton(modal, text="CERRAR", font=ctk.CTkFont("Consolas", 11, "bold"), fg_color="#111122", hover_color="#1A1A33", text_color="#445566", border_color="#1A1A2E", border_width=1, corner_radius=6, height=36, command=modal.destroy).pack(pady=(0, 16))

    def _open_license_modal(self):
        # Si ya es PRO, mostrar estado en vez del formulario
        already_pro = is_pro()

        modal = ctk.CTkToplevel(self)
        modal.title("DrxOpti PRO")
        modal.geometry("480x420")
        modal.resizable(False, False)
        modal.configure(fg_color=DARK_BG)
        modal.transient(self)
        modal.after(60, modal.grab_set)

        # Encabezado con banda dorada
        head = ctk.CTkFrame(modal, fg_color="#12100A", corner_radius=0, height=90)
        head.pack(fill="x")
        head.pack_propagate(False)
        ctk.CTkLabel(head, text="★", font=ctk.CTkFont("Segoe UI", 30, "bold"), text_color=NEON_GOLD).pack(pady=(16, 0))
        ctk.CTkLabel(head, text="DrxOpti PRO", font=ctk.CTkFont("Segoe UI", 17, "bold"), text_color=NEON_GOLD).pack()

        if already_pro:
            ctk.CTkLabel(modal, text="✓  Tu licencia PRO está activa",
                         font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=NEON_GREEN).pack(pady=(34, 8))
            ctk.CTkLabel(modal, text="Ya tienes acceso a todas las funciones:\nOptimizador de red, Timer 0.5ms y DNS Boost.",
                         font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_MID, justify="center").pack(pady=(0, 24))
            ctk.CTkButton(modal, text="Cerrar", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          fg_color=CARD_BG, hover_color=CARD_HOVER, text_color=TEXT_MID,
                          border_color=CARD_BORDER, border_width=1, corner_radius=8, height=40, width=200,
                          command=modal.destroy).pack()
            return

        ctk.CTkLabel(modal, text="Pega tu clave de licencia para desbloquear\ntodas las funciones PRO.",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_MID, justify="center").pack(pady=(22, 16))

        entry = ctk.CTkEntry(modal, placeholder_text="Pega aquí tu clave DRXO-...",
                             font=ctk.CTkFont("Consolas", 11), fg_color="#0A0A14",
                             border_color=NEON_GOLD, border_width=1, corner_radius=8,
                             height=44, width=380)
        entry.pack()
        entry.focus_set()

        status_lbl = ctk.CTkLabel(modal, text="", font=ctk.CTkFont("Segoe UI", 11))
        status_lbl.pack(pady=12)

        def activate(_evt=None):
            # Limpiar espacios, saltos de línea y comillas al pegar
            raw = entry.get().strip().strip('"').strip("'").replace("\n", "").replace("\r", "").replace(" ", "")
            if not raw:
                status_lbl.configure(text="Pega tu clave primero.", text_color=NEON_GOLD)
                return

            from core.license_manager import activate as do_activate
            result = do_activate(raw)
            if result["success"]:
                self._license = {"tier": "pro", "activated": True}
                self._refresh_pro_ui()
                status_lbl.configure(text="✓ ¡Activado! Bienvenido a PRO.", text_color=NEON_GREEN)
                act_btn.configure(text="✓ ACTIVADO", fg_color="#0A2A18", text_color=NEON_GREEN)
                modal.after(1400, modal.destroy)
            else:
                status_lbl.configure(text=f"✗ {result['reason']}", text_color=NEON_RED)

        entry.bind("<Return>", activate)

        act_btn = ctk.CTkButton(modal, text="ACTIVAR PRO", font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                fg_color=NEON_GOLD, hover_color="#E6C200", text_color="#000000",
                                corner_radius=8, height=44, width=380, command=activate)
        act_btn.pack(pady=(0, 14))

        ctk.CTkLabel(modal, text="¿No tienes clave todavía?",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=TEXT_DIM).pack()
        buy = ctk.CTkLabel(modal, text="Consíguela en el Discord  →",
                           font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#7289DA", cursor="hand2")
        buy.pack(pady=(2, 0))
        buy.bind("<Button-1>", lambda e: webbrowser.open("https://discord.gg/drxopti"))

    def _refresh_pro_ui(self):
        """Actualiza el badge y todo lo que dependa del estado PRO tras activar."""
        self._tier_badge.configure(text="★  DRXOPTI PRO", text_color=NEON_GOLD)
        self._log("Licencia PRO activada — funciones desbloqueadas.")

    def _get_pending_tweaks(self, score, cpu, ram):
        hw = self._hw
        return [
            {"title": "Plan de energía: Alto Rendimiento", "desc": "Activa el plan máximo para evitar throttling.", "done": score >= 75},
            {"title": "Caché de shaders limpia", "desc": "Shaders acumulados causan stuttering.", "done": score >= 80},
            {"title": "Servicios de telemetría pausados", "desc": "DiagTrack y SysMain consumen CPU.", "done": self._tryhard_active and self._watcher and self._watcher.active_game is not None},
            {"title": f"CPU en buen estado ({cpu:.0f}%)", "desc": "Ideal < 30% en reposo.", "done": cpu < 30},
            {"title": f"RAM disponible ({ram:.0f}%)", "desc": "Ideal < 60% antes de jugar.", "done": ram < 60},
            {"title": "Red optimizada (Nagle off · CTCP)", "desc": "Reduce ping y paquetes perdidos.", "done": self._net_applied},
            {"title": "Timer Resolution 0.5ms", "desc": "Reduce input lag medible en competitivo.", "done": self._timer_applied},
            {"title": "Modo Tryhard activo", "desc": "Detecta juegos y optimiza automáticamente.", "done": self._tryhard_active},
            {"title": f"GPU detectada: {hw['gpu_brand'].upper()}", "desc": f"{hw['gpu']}", "done": hw["gpu_brand"] in ("nvidia", "amd")},
        ]

    # ── RGB y extras ──────────────────────────────────────────────────────────

    def _apply_rgb(self):
        self._rgb.register(self._logo_drx,    mode="text",   offset=0,   speed=0.4, sat=0.9)
        self._rgb.register(self._logo_opti,   mode="text",   offset=180, speed=0.4, sat=0.9)
        self._rgb.register(self._hero_btn,    mode="border", speed=0.9, sat=1.0)
        self._rgb.register(self._tryhard_btn, mode="border", offset=120, speed=0.7, sat=0.8, val=0.6)
        self._rgb.register(self._score_label, mode="text",   offset=240, speed=0.5, sat=0.6, val=0.8)
        self._rgb.register(self._net_btn,     mode="border", offset=60,  speed=0.6, sat=0.7, val=0.7)
        self._rgb.register(self._timer_btn,   mode="border", offset=200, speed=0.6, sat=0.7, val=0.7)
        self._rgb.register(self._discord_btn, mode="border", offset=280, speed=0.5, sat=0.6, val=0.7)

        self._rgb.register(self._vip_title, mode="text", offset=45, speed=0.4, sat=0.7)

        # Tooltips — ayuda contextual al pasar el mouse
        Tooltip(self._hero_btn,    "Ejecuta TODAS las optimizaciones en un clic:\nRAM + CPU + Red + Timer + Ping test.\nAl final genera tu tarjeta compartible.")
        Tooltip(self._tryhard_btn, "Vigila en segundo plano. Cuando abras un juego,\noptimiza la PC automáticamente y la restaura al salir.")
        Tooltip(self._net_btn,     "Desactiva Nagle, activa CTCP y boostea DNS.\nReduce ping en juegos online. Requiere PRO.")
        Tooltip(self._timer_btn,   "Baja el timer de Windows de 15.6ms a 0.5ms.\nMenos input lag en shooters. Requiere PRO.")
        Tooltip(self._score_label, "Clic para ver el detalle de tweaks pendientes.")

    def _on_vip_update(self, gpu: dict, jitter: dict):
        def apply():
            if gpu:
                temp = gpu["temp_c"]
                rating, color = temp_rating(temp)
                self._vip_temp.configure(text=f"{temp}°C  {rating}", text_color=color)
                vram_pct = int(gpu["vram_used"] * 100 / max(gpu["vram_total"], 1))
                self._vip_gpu.configure(text=f"{gpu['usage_pct']}%  ·  VRAM {vram_pct}%",
                                        text_color=NEON_BLUE if gpu["usage_pct"] < 80 else NEON_GOLD)
            else:
                self._vip_temp.configure(text="GPU no detectada", text_color="#334455")

            avg = jitter["avg_ms"]
            rating, color = jitter_rating(avg)
            self._vip_jitter.configure(text=f"{avg:.2f}ms  {rating}", text_color=color)
        self.after(0, apply)

    def _boost_dns(self):
        if not is_pro():
            self._open_license_modal()
            return
        self._log("Aplicando DNS Cloudflare + flush de caché...")

        def run():
            primary, secondary = DNS_PROVIDERS["Cloudflare (1.1.1.1)"]
            result = apply_dns(primary, secondary)
            if result["success"]:
                ifaces = ", ".join(result["interfaces"])
                self.after(0, lambda: self._log(f"✓ DNS 1.1.1.1 aplicado en: {ifaces}"))
            else:
                self.after(0, lambda: self._log(f"✗ DNS falló: {result.get('reason', 'error')}"))

        threading.Thread(target=run, daemon=True).start()

    def _open_whitelist(self):
        WhitelistWindow(self)

    def _open_shader(self):
        ShaderWindow(self)

    def _open_startup(self):
        StartupWindow(self)

    def _open_custom_games(self):
        def on_save():
            custom = load_custom_games()
            all_names = ["Fortnite", "Valorant", "CS2", "Warzone", "Apex Legends"] + list(custom.values())
            self._games_label.configure(text="  ·  ".join(all_names[:5]) + (f"  +{len(all_names)-5}" if len(all_names) > 5 else ""))
            if self._watcher:
                self._watcher.stop()
                from core.game_watcher import GameWatcher
                self._watcher = GameWatcher(on_game_start=self._on_game_start, on_game_stop=self._on_game_stop)
                self._watcher.start()
        CustomGamesWindow(self, on_save=on_save)

    def _on_update_check(self, result: dict):
        if result.get("has_update"):
            self.after(0, lambda: self._show_update_banner(result))

    def _show_update_banner(self, result: dict):
        banner = ctk.CTkFrame(self, fg_color="#1A1400", corner_radius=0, height=36)
        banner.pack(fill="x", side="bottom")
        banner.pack_propagate(False)
        self._rgb.register(banner, mode="border", offset=30, speed=0.4)

        ctk.CTkLabel(banner,
                     text=f"⬆  Nueva versión disponible: v{result['latest']}  —  {result['changelog']}",
                     font=ctk.CTkFont("Consolas", 10, "bold"),
                     text_color=NEON_GOLD).pack(side="left", padx=14, pady=8)

        if result.get("url"):
            ctk.CTkButton(banner, text="ACTUALIZAR",
                          font=ctk.CTkFont("Consolas", 10, "bold"),
                          fg_color="#332200", hover_color="#443300",
                          text_color=NEON_GOLD, border_color=NEON_GOLD, border_width=1,
                          corner_radius=4, height=24, width=100,
                          command=lambda: webbrowser.open(result["url"])).pack(side="right", padx=14)

        ctk.CTkButton(banner, text="✕",
                      font=ctk.CTkFont("Consolas", 10),
                      fg_color="transparent", hover_color="#1A1400",
                      text_color="#665500", border_width=0, height=24, width=28,
                      command=banner.destroy).pack(side="right", padx=2)
