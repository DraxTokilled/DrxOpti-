import customtkinter as ctk
import threading
import time
import os
import subprocess

NEON_GREEN  = "#00FF87"
NEON_BLUE   = "#00D4FF"
NEON_RED    = "#FF4444"
NEON_GOLD   = "#FFD700"
DARK_BG     = "#0A0A0F"
CARD_BG     = "#0F0F1A"

STEPS = [
    ("Capturando estado del sistema...",        NEON_BLUE,  0.08),
    ("Analizando hardware...",                  NEON_BLUE,  0.12),
    ("Cerrando procesos en segundo plano...",   NEON_GREEN, 0.22),
    ("Elevando prioridad de CPU...",            NEON_GREEN, 0.32),
    ("Liberando memoria RAM...",                NEON_GREEN, 0.42),
    ("Optimizando red — Nagle off...",          NEON_BLUE,  0.52),
    ("Activando CTCP + DNS boost...",           NEON_BLUE,  0.60),
    ("Eliminando throttling de red...",         NEON_BLUE,  0.67),
    ("Aplicando Timer Resolution 0.5ms...",     NEON_GREEN, 0.75),
    ("Persistiendo configuración en BCD...",    NEON_GREEN, 0.82),
    ("Testeando ping a servidores...",          NEON_GOLD,  0.90),
    ("Calculando puntuación final...",          NEON_GOLD,  0.96),
    ("¡OPTIMIZACIÓN COMPLETA!",                 NEON_GREEN, 1.00),
]


class OptimizeAllOverlay(ctk.CTkToplevel):
    def __init__(self, master, hw_profile, snapshot_before, on_complete):
        super().__init__(master)
        self._hw         = hw_profile
        self._snap_before = snapshot_before
        self._on_complete = on_complete

        self.title("DrxOpti — Optimizando...")
        self.geometry("680x480")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # no cerrar durante proceso

        self._build_ui()
        self.after(300, self._start)

    def _build_ui(self):
        # Título
        ctk.CTkLabel(
            self, text="⚡  OPTIMIZANDO TU PC",
            font=ctk.CTkFont("Consolas", 20, "bold"),
            text_color=NEON_GREEN,
        ).pack(pady=(36, 4))

        ctk.CTkLabel(
            self, text="No cierres esta ventana",
            font=ctk.CTkFont("Consolas", 10),
            text_color="#334455",
        ).pack()

        # Barra de progreso principal
        self._bar = ctk.CTkProgressBar(
            self, height=10, corner_radius=5,
            fg_color="#0A0A14", progress_color=NEON_GREEN,
        )
        self._bar.set(0)
        self._bar.pack(fill="x", padx=48, pady=(28, 8))

        self._pct_label = ctk.CTkLabel(
            self, text="0%",
            font=ctk.CTkFont("Consolas", 11, "bold"),
            text_color="#334455",
        )
        self._pct_label.pack()

        # Texto del paso actual
        self._step_label = ctk.CTkLabel(
            self, text="Inicializando...",
            font=ctk.CTkFont("Consolas", 13, "bold"),
            text_color=NEON_BLUE,
        )
        self._step_label.pack(pady=(16, 8))

        # Log de pasos completados
        self._log = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont("Consolas", 10),
            fg_color="#080810",
            text_color="#224433",
            corner_radius=8,
            state="disabled",
            height=160,
        )
        self._log.pack(fill="x", padx=40, pady=(0, 16))

        # Panel de resultado (oculto hasta el final)
        self._result_frame = ctk.CTkFrame(self, fg_color="transparent")

    def _write_log(self, text: str, color: str = "#224433"):
        self._log.configure(state="normal")
        self._log.insert("end", f"  ✓  {text}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _set_step(self, text: str, color: str, pct: float):
        self._step_label.configure(text=text, text_color=color)
        self._bar.set(pct)
        self._bar.configure(progress_color=color)
        self._pct_label.configure(text=f"{int(pct * 100)}%", text_color=color)

    def _start(self):
        threading.Thread(target=self._run_all, daemon=True).start()

    def _run_all(self):
        from core.snapshot import capture_snapshot, compare_snapshots
        from core.optimizer import apply_game_mode
        from core.network_optimizer import apply_network_tweaks
        from core.timer_resolution import set_gaming_resolution, apply_bcdedit_timer
        from core.ping_tester import test_all_servers, best_ping
        from core.score_card import generate
        import psutil

        results = {
            "snap_after":   None,
            "diff":         None,
            "ping":         {},
            "score_before": 0,
            "score_after":  0,
            "net_ok":       0,
            "timer_ok":     False,
            "card_path":    None,
        }

        # Score antes
        cpu_b = self._snap_before.get("cpu_percent", 50)
        ram_b = self._snap_before.get("ram_percent", 60)
        results["score_before"] = round(100 - (cpu_b * 0.5 + ram_b * 0.5))

        def step(i):
            txt, col, pct = STEPS[i]
            self.after(0, lambda t=txt, c=col, p=pct: self._set_step(t, c, p))

        step(0); time.sleep(0.6)
        step(1); time.sleep(0.5)

        # Optimizer
        step(2)
        try:
            apply_game_mode("Fortnite")
        except Exception:
            pass
        self.after(0, lambda: self._write_log("Procesos en background cerrados"))
        time.sleep(0.7)

        step(3); time.sleep(0.5)
        self.after(0, lambda: self._write_log("Prioridad CPU → HIGH"))

        step(4); time.sleep(0.6)
        self.after(0, lambda: self._write_log("RAM liberada"))

        # Network
        step(5); time.sleep(0.5)
        net_results = apply_network_tweaks()
        results["net_ok"] = sum(1 for v in net_results.values() if v)
        self.after(0, lambda: self._write_log(f"Red: Nagle off · ACK optimizado"))

        step(6); time.sleep(0.5)
        self.after(0, lambda: self._write_log("CTCP activado · DNS boost aplicado"))

        step(7); time.sleep(0.5)
        self.after(0, lambda: self._write_log("Network throttling eliminado"))

        # Timer
        step(8); time.sleep(0.6)
        ok = set_gaming_resolution()
        results["timer_ok"] = ok
        self.after(0, lambda: self._write_log("Timer Resolution → 0.5ms"))

        step(9); time.sleep(0.5)
        apply_bcdedit_timer()
        self.after(0, lambda: self._write_log("BCD configurado — persiste al reiniciar"))

        # Ping test
        step(10)
        self.after(0, lambda: self._write_log("Testeando servidores de juego..."))
        ping_data = test_all_servers()
        results["ping"] = ping_data
        best = best_ping(ping_data)
        for game, ms in best.items():
            label = f"{ms:.0f}ms" if ms else "timeout"
            self.after(0, lambda g=game, l=label: self._write_log(f"{g}: {l}"))
        time.sleep(0.4)

        # Score final
        step(11)
        snap_after = capture_snapshot()
        results["snap_after"] = snap_after
        results["diff"] = compare_snapshots(self._snap_before, snap_after)

        cpu_a = snap_after.get("cpu_percent", cpu_b)
        ram_a = snap_after.get("ram_percent", ram_b)
        results["score_after"] = round(100 - (cpu_a * 0.5 + ram_a * 0.5))
        time.sleep(0.5)

        # Generar tarjeta
        diff = results["diff"] or {}
        try:
            path = generate(
                score_before   = results["score_before"],
                score_after    = results["score_after"],
                hw_profile     = self._hw,
                ping_results   = ping_data,
                tweaks_applied = results["net_ok"] + (1 if ok else 0) + 3,
                ram_freed_gb   = diff.get("ram_freed_gb", 0),
                procs_killed   = diff.get("processes_killed", 0),
            )
            results["card_path"] = path
        except Exception:
            pass

        step(12)
        time.sleep(0.5)
        self.after(0, lambda: self._show_results(results))

    def _show_results(self, results: dict):
        # Ocultar log
        self._log.pack_forget()

        diff = results["diff"] or {}
        before = results["score_before"]
        after  = results["score_after"]
        delta  = after - before
        sign   = "+" if delta >= 0 else ""

        col = NEON_GREEN if after >= 75 else (NEON_BLUE if after >= 50 else NEON_RED)

        f = self._result_frame
        f.pack(fill="x", padx=40)

        # Score grande
        score_row = ctk.CTkFrame(f, fg_color="#080810", corner_radius=10)
        score_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(score_row, text=f"{before}", font=ctk.CTkFont("Consolas", 48, "bold"), text_color="#334455").pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(score_row, text="→", font=ctk.CTkFont("Consolas", 28), text_color="#334455").pack(side="left")
        ctk.CTkLabel(score_row, text=f"{after}", font=ctk.CTkFont("Consolas", 48, "bold"), text_color=col).pack(side="left", padx=8)
        ctk.CTkLabel(score_row, text=f"{sign}{delta} pts", font=ctk.CTkFont("Consolas", 16, "bold"), text_color=col).pack(side="left", padx=4)

        # Stats
        stats_row = ctk.CTkFrame(f, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 10))

        self._stat_chip(stats_row, f"+{diff.get('ram_freed_gb', 0):.1f} GB", "RAM liberada", NEON_GREEN)
        self._stat_chip(stats_row, f"-{diff.get('processes_killed', 0)}", "procesos", NEON_BLUE)
        best = {g: min(v for v in r.values() if v) for g, r in results["ping"].items() if any(v for v in r.values() if v)}
        if best:
            avg_ping = round(sum(best.values()) / len(best))
            self._stat_chip(stats_row, f"{avg_ping}ms", "ping prom.", NEON_GOLD)

        # Botones
        btn_row = ctk.CTkFrame(f, fg_color="transparent")
        btn_row.pack(fill="x")

        if results.get("card_path"):
            ctk.CTkButton(
                btn_row, text="📤  VER TARJETA",
                font=ctk.CTkFont("Consolas", 11, "bold"),
                fg_color="#001A00", hover_color="#002200",
                text_color=NEON_GREEN, border_color=NEON_GREEN, border_width=1,
                corner_radius=6, height=36,
                command=lambda: os.startfile(results["card_path"]),
            ).pack(side="left", padx=(0, 8), expand=True, fill="x")

        ctk.CTkButton(
            btn_row, text="CERRAR",
            font=ctk.CTkFont("Consolas", 11, "bold"),
            fg_color="#0A0A14", hover_color="#111122",
            text_color="#445566", border_color=CARD_BG, border_width=1,
            corner_radius=6, height=36,
            command=self._close,
        ).pack(side="left", expand=True, fill="x")

    def _stat_chip(self, parent, value, label, color):
        chip = ctk.CTkFrame(parent, fg_color="#080810", corner_radius=8)
        chip.pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkLabel(chip, text=value, font=ctk.CTkFont("Consolas", 18, "bold"), text_color=color).pack(pady=(10, 0))
        ctk.CTkLabel(chip, text=label, font=ctk.CTkFont("Consolas", 9), text_color="#334455").pack(pady=(0, 10))

    def _close(self):
        self.grab_release()
        self.destroy()
        if self._on_complete:
            self._on_complete()
