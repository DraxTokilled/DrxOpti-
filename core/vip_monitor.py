import subprocess
import time
import threading
import statistics

_NVIDIA_SMI = r"C:\Windows\System32\nvidia-smi.exe"


def get_gpu_stats() -> dict:
    """Temperatura, uso y VRAM de la GPU via nvidia-smi. Retorna None en campos no disponibles."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,clocks.sm",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=4,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            return {}
        parts = [p.strip() for p in result.stdout.strip().split(",")]
        return {
            "temp_c":     int(parts[0]),
            "usage_pct":  int(parts[1]),
            "vram_used":  int(parts[2]),
            "vram_total": int(parts[3]),
            "clock_mhz":  int(parts[4]),
        }
    except Exception:
        return {}


def measure_timer_jitter(samples: int = 50) -> dict:
    """
    Mide el jitter del scheduler de Windows: pide sleeps de 1ms y mide
    cuánto se pasa de lo pedido. Proxy honesto de la fluidez del sistema.
    Con timer a 15.6ms el overshoot es alto; con 0.5ms baja drásticamente.
    """
    deltas = []
    for _ in range(samples):
        start = time.perf_counter()
        time.sleep(0.001)
        elapsed_ms = (time.perf_counter() - start) * 1000
        deltas.append(elapsed_ms - 1.0)  # overshoot sobre 1ms pedido

    return {
        "avg_ms": round(statistics.mean(deltas), 2),
        "max_ms": round(max(deltas), 2),
        "p95_ms": round(sorted(deltas)[int(len(deltas) * 0.95)], 2),
    }


def jitter_rating(avg_ms: float) -> tuple[str, str]:
    if avg_ms < 0.6:
        return "✦ ÓPTIMO",    "#00FF87"
    if avg_ms < 2.0:
        return "◈ BUENO",     "#00D4FF"
    if avg_ms < 8.0:
        return "○ MEJORABLE", "#FFD700"
    return "✗ LENTO",         "#FF4444"


def temp_rating(temp_c: int) -> tuple[str, str]:
    if temp_c < 60:
        return "FRÍA",     "#00FF87"
    if temp_c < 75:
        return "NORMAL",   "#00D4FF"
    if temp_c < 85:
        return "CALIENTE", "#FFD700"
    return "THROTTLING",   "#FF4444"


class VipMonitor:
    """Hilo de monitoreo continuo: GPU + jitter cada N segundos."""

    def __init__(self, on_update, interval_s: float = 3.0):
        self._on_update = on_update
        self._interval  = interval_s
        self._running   = False

    def start(self):
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            gpu    = get_gpu_stats()
            jitter = measure_timer_jitter(samples=25)
            try:
                self._on_update(gpu, jitter)
            except Exception:
                pass
            time.sleep(self._interval)
