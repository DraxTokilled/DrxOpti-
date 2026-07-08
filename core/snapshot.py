import psutil
import time

def capture_snapshot() -> dict:
    mem = psutil.virtual_memory()
    procs = [p.info["name"] for p in psutil.process_iter(["name"]) if p.info["name"]]

    return {
        "timestamp": time.time(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_used_gb": round((mem.total - mem.available) / (1024 ** 3), 2),
        "ram_free_gb": round(mem.available / (1024 ** 3), 2),
        "ram_percent": mem.percent,
        "process_count": len(procs),
        "processes": procs,
    }

def compare_snapshots(before: dict, after: dict) -> dict:
    ram_freed = round(before["ram_used_gb"] - after["ram_used_gb"], 2)
    procs_killed = before["process_count"] - after["process_count"]
    cpu_delta = round(before["cpu_percent"] - after["cpu_percent"], 1)

    return {
        "ram_freed_gb": max(ram_freed, 0),
        "processes_killed": max(procs_killed, 0),
        "cpu_delta": cpu_delta,
        "ram_before": before["ram_percent"],
        "ram_after": after["ram_percent"],
        "cpu_before": before["cpu_percent"],
        "cpu_after": after["cpu_percent"],
    }
