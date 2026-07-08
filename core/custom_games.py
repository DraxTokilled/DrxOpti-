import json
import os
from core.paths import data_dir

GAMES_FILE = os.path.join(data_dir(), "custom_games.json")

def load() -> dict:
    if not os.path.exists(GAMES_FILE):
        return {}
    try:
        with open(GAMES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save(games: dict):
    with open(GAMES_FILE, "w") as f:
        json.dump(games, f, indent=2)

def add(display_name: str, exe_name: str):
    games = load()
    games[exe_name] = display_name
    save(games)

def remove(exe_name: str):
    games = load()
    games.pop(exe_name, None)
    save(games)
