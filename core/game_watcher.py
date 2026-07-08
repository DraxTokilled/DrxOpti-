import psutil
import threading
import time
import ctypes
from core.optimizer import apply_game_mode, restore_normal_mode

GAME_PROCESSES = {
    "FortniteClient-Win64-Shipping.exe": "Fortnite",
    "VALORANT-Win64-Shipping.exe": "Valorant",
    "cs2.exe": "CS2",
    "ModernWarfare4.exe": "Warzone",
    "r5apex.exe": "Apex Legends",
}

class GameWatcher:
    def __init__(self, on_game_start=None, on_game_stop=None):
        self.on_game_start = on_game_start
        self.on_game_stop = on_game_stop
        self._running = False
        self._thread = None
        self._active_game = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _watch_loop(self):
        while self._running:
            detected = self._detect_game()

            if detected and self._active_game is None:
                self._active_game = detected
                apply_game_mode(detected)
                if self.on_game_start:
                    self.on_game_start(detected)

            elif not detected and self._active_game is not None:
                restore_normal_mode()
                if self.on_game_stop:
                    self.on_game_stop(self._active_game)
                self._active_game = None

            time.sleep(2)

    def _detect_game(self):
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name in GAME_PROCESSES:
                    return GAME_PROCESSES[name]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    @property
    def active_game(self):
        return self._active_game
