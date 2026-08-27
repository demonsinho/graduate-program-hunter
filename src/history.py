"""Append-only log of past detected signals, for the dashboard's history view."""
import json
from datetime import datetime, timezone
from pathlib import Path


def append_events(path: str, events: list) -> None:
    if not events:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    history = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    now = datetime.now(timezone.utc).isoformat()
    for e in events:
        history.append({**e, "timestamp": now})
    p.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
