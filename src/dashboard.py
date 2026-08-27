"""Renders docs/index.html — a static status dashboard for GitHub Pages.

Reads config/firms.yaml + state.json + data/alerts_history.json and
produces one self-contained HTML file (no external assets, no build step).
"""
import html
import json
import os
from datetime import datetime, timezone

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "firms.yaml")
STATE_PATH = os.path.join(BASE_DIR, "state.json")
HISTORY_PATH = os.path.join(BASE_DIR, "data", "alerts_history.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "docs", "index.html")


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_firms() -> list:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("firms", [])


def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def render_status_rows(firms: list, pages: dict) -> str:
    rows = []
    for firm in sorted(firms, key=lambda f: (f.get("tier", 999), f["name"])):
        name = firm["name"]
        for loc in firm.get("locations", []):
            location = loc["location"]
            url = loc["career_url"]
            entry = pages.get(f"{name}|{location}")
            if entry is None:
                signal = '<span class="dot dot-pending" title="Never successfully fetched"></span>'
                last_checked = "—"
            elif entry.get("has_signal"):
                signal = '<span class="dot dot-yes" title="Mentions 2027"></span> Yes'
                last_checked = esc(entry.get("last_checked", "—"))
            else:
                signal = '<span class="dot dot-no" title="No 2027 mention"></span> No'
                last_checked = esc(entry.get("last_checked", "—"))
            rows.append(
                f"<tr><td>{esc(name)}</td><td>{esc(location)}</td>"
                f"<td>{signal}</td><td class=\"mono\">{last_checked}</td>"
                f"<td><a href=\"{esc(url)}\" target=\"_blank\" rel=\"noopener\">career page</a></td></tr>"
            )
    return "\n".join(rows)


def render_manual_check_rows(entries: list) -> str:
    if not entries:
        return '<tr><td colspan="4" class="empty">Nothing currently failing.</td></tr>'
    rows = []
    for e in entries:
        where = esc(e.get("location")) if e.get("location") else "—"
        url = f'<a href="{esc(e["url"])}" target="_blank" rel="noopener">link</a>' if e.get("url") else "—"
        rows.append(
            f"<tr><td>{esc(e.get('firm'))}</td><td>{where}</td>"
            f"<td>{url}</td><td>{esc(e.get('reason'))}</td></tr>"
        )
    return "\n".join(rows)


def render_search_check_rows(entries: list) -> str:
    if not entries:
        return '<tr><td colspan="2" class="empty">Nothing currently failing.</td></tr>'
    rows = []
    for e in entries:
        reason = e.get("reason", "")
        reason = reason.split(" for url:")[0]  # the redacted URL is identical across every row
        rows.append(f"<tr><td>{esc(e.get('firm'))}</td><td>{esc(reason)}</td></tr>")
    return "\n".join(rows)


def render_history_rows(history: list) -> str:
    if not history:
        return '<tr><td colspan="5" class="empty">No signals detected yet.</td></tr>'
    rows = []
    for e in sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True):
        where = esc(e.get("location")) if e.get("location") else "—"
        url = f'<a href="{esc(e["url"])}" target="_blank" rel="noopener">link</a>' if e.get("url") else "—"
        rows.append(
            f"<tr><td class=\"mono\">{esc(e.get('timestamp'))}</td><td>{esc(e.get('firm'))}</td>"
            f"<td>{where}</td><td>{esc(e.get('detail'))}</td><td>{url}</td></tr>"
        )
    return "\n".join(rows)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grad Program Hunter — Dashboard</title>
<style>
  :root {{
    --bg: #0f1117; --panel: #161923; --border: #2a2e3d; --text: #e6e8ef;
    --muted: #8b90a3; --accent: #5b8def; --yes: #3ecf8e; --no: #6b7280; --pending: #e3b341;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f7f8fb; --panel: #ffffff; --border: #e2e5ec; --text: #1a1d29;
      --muted: #5a5f73; --accent: #2f6fed; --yes: #1f9d63; --no: #9aa0b0; --pending: #b8860b;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem 1.25rem 4rem; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .subtitle {{ color: var(--muted); margin-bottom: 2rem; font-size: 0.9rem; }}
  h2 {{ font-size: 1.1rem; margin: 2.5rem 0 0.75rem; }}
  .panel {{
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    overflow-x: auto;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th, td {{ text-align: left; padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; }}
  tr:last-child td {{ border-bottom: none; }}
  td.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; color: var(--muted); }}
  td.empty {{ color: var(--muted); text-align: center; padding: 1.25rem; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.35rem; }}
  .dot-yes {{ background: var(--yes); }}
  .dot-no {{ background: var(--no); }}
  .dot-pending {{ background: var(--pending); }}
  .stats {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }}
  .stat {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 0.9rem 1.2rem; min-width: 120px; }}
  .stat .n {{ font-size: 1.5rem; font-weight: 600; }}
  .stat .l {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Grad Program Hunter</h1>
  <div class="subtitle">Summer 2027 EU finance graduate programme tracker &middot; generated {generated_at}</div>

  <div class="stats">
    <div class="stat"><div class="n">{n_entries}</div><div class="l">Tracked entries</div></div>
    <div class="stat"><div class="n">{n_signal}</div><div class="l">Currently mention 2027</div></div>
    <div class="stat"><div class="n">{n_manual}</div><div class="l">Career pages need check</div></div>
    <div class="stat"><div class="n">{n_history}</div><div class="l">Signals detected all-time</div></div>
  </div>

  <h2>Career pages needing manual check</h2>
  <div class="panel">
    <table>
      <thead><tr><th>Firm</th><th>Location</th><th>URL</th><th>Reason</th></tr></thead>
      <tbody>
{page_manual_check_rows}
      </tbody>
    </table>
  </div>

  <h2>Search checks failing</h2>
  <div class="subtitle" style="margin: 0 0 0.75rem;">Usually one systemic issue (e.g. API quota/access), not per-firm problems.</div>
  <div class="panel">
    <table>
      <thead><tr><th>Firm</th><th>Reason</th></tr></thead>
      <tbody>
{search_manual_check_rows}
      </tbody>
    </table>
  </div>

  <h2>Alert history</h2>
  <div class="panel">
    <table>
      <thead><tr><th>When (UTC)</th><th>Firm</th><th>Location</th><th>Signal</th><th>Link</th></tr></thead>
      <tbody>
{history_rows}
      </tbody>
    </table>
  </div>

  <h2>Status grid</h2>
  <div class="panel">
    <table>
      <thead><tr><th>Firm</th><th>Location</th><th>Mentions 2027</th><th>Last checked (UTC)</th><th>Career page</th></tr></thead>
      <tbody>
{status_rows}
      </tbody>
    </table>
  </div>
</div>
</body>
</html>
"""


def main() -> int:
    firms = load_firms()
    state = load_json(STATE_PATH, {"pages": {}, "manual_check": []})
    history = load_json(HISTORY_PATH, [])

    pages = state.get("pages", {})
    manual_check = state.get("manual_check", [])
    page_failures = [e for e in manual_check if e.get("url")]
    search_failures = [e for e in manual_check if not e.get("url")]
    n_entries = sum(len(f.get("locations", [])) for f in firms)
    n_signal = sum(1 for v in pages.values() if v.get("has_signal"))

    html_out = PAGE_TEMPLATE.format(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        n_entries=n_entries,
        n_signal=n_signal,
        n_manual=len(page_failures),
        n_history=len(history),
        page_manual_check_rows=render_manual_check_rows(page_failures),
        search_manual_check_rows=render_search_check_rows(search_failures),
        history_rows=render_history_rows(history),
        status_rows=render_status_rows(firms, pages),
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Dashboard written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
