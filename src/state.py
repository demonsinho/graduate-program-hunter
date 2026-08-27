"""Load/save the tracker's persisted state (page hashes, last search results)."""
import json
from pathlib import Path


def load_state(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"pages": {}, "search": {}}
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("pages", {})
    data.setdefault("search", {})
    data.setdefault("manual_check", [])
    return data


def save_state(path: str, state: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")
