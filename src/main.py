"""Grad Program Hunter — daily orchestrator.

Loads config/firms.yaml, checks each firm's career page(s) for content
changes mentioning "2027", runs a weekly-per-firm search check as a
secondary signal, emails a digest if anything new was found, and persists
state.json so future runs can diff against today's snapshot.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import yaml

from state import load_state, save_state
from scraper import Scraper
from search import search_firm
from notifier import send_digest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "firms.yaml")
STATE_PATH = os.path.join(BASE_DIR, "state.json")

OPENING_KEYWORDS = ["2027"]
SEARCH_INTERVAL_DAYS = 7


def load_config() -> list:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("firms", [])


def check_pages(firms: list, state: dict, scraper: Scraper) -> tuple:
    page_changes = []
    manual_check = []
    for firm in firms:
        name = firm["name"]
        for loc in firm.get("locations", []):
            location = loc["location"]
            url = loc["career_url"]
            key = f"{name}|{location}"
            result = scraper.check_page(url)
            if not result["ok"]:
                manual_check.append(f"{name} ({location}): fetch failed for {url} — {result['error']}")
                continue

            prev = state["pages"].get(key)
            new_hash = result["hash"]
            has_signal = any(k.lower() in result["text"].lower() for k in OPENING_KEYWORDS)

            if prev is not None and prev["hash"] != new_hash and has_signal:
                page_changes.append(f"{name} ({location}): page changed and mentions 2027 — {url}")

            state["pages"][key] = {
                "hash": new_hash,
                "last_checked": datetime.now(timezone.utc).isoformat(),
            }
    return page_changes, manual_check


def check_searches(firms: list, state: dict, api_key: str, cse_id: str) -> tuple:
    search_hits = []
    manual_check = []
    now = datetime.now(timezone.utc)

    for firm in firms:
        name = firm["name"]
        prev = state["search"].get(name)
        if prev:
            last_checked = datetime.fromisoformat(prev["last_checked"])
            if now - last_checked < timedelta(days=SEARCH_INTERVAL_DAYS):
                continue

        result = search_firm(name, api_key, cse_id)
        if not result["ok"]:
            manual_check.append(f"{name}: search check failed — {result['error']}")
            continue

        prev_urls = set(prev["result_urls"]) if prev else set()
        if prev is not None:
            for url in result["urls"]:
                if url not in prev_urls:
                    search_hits.append(f"{name}: new search result — {url}")

        state["search"][name] = {
            "last_checked": now.isoformat(),
            "result_urls": result["urls"],
        }
    return search_hits, manual_check


def build_digest(page_changes: list, search_hits: list, manual_check: list) -> str:
    lines = []
    if page_changes:
        lines.append("=== Career page changes mentioning 2027 ===")
        lines.extend(f"- {line}" for line in page_changes)
        lines.append("")
    if search_hits:
        lines.append("=== New search results mentioning 2027 ===")
        lines.extend(f"- {line}" for line in search_hits)
        lines.append("")
    if manual_check:
        lines.append("=== Needs manual check (fetch/search failures) ===")
        lines.extend(f"- {line}" for line in manual_check)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    firms = load_config()
    state = load_state(STATE_PATH)

    with Scraper() as scraper:
        page_changes, page_failures = check_pages(firms, state, scraper)

    api_key = os.environ.get("GOOGLE_CSE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if api_key and cse_id:
        search_hits, search_failures = check_searches(firms, state, api_key, cse_id)
    else:
        print("GOOGLE_CSE_API_KEY/GOOGLE_CSE_ID not set — skipping search checks.")
        search_hits, search_failures = [], []

    manual_check = page_failures + search_failures
    digest = build_digest(page_changes, search_hits, manual_check)
    print(digest if digest else "No changes detected.")

    if page_changes or search_hits:
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
        to_addr = os.environ.get("DIGEST_TO", gmail_user)
        if not gmail_user or not gmail_app_password:
            print("GMAIL_USER/GMAIL_APP_PASSWORD not set — cannot send email. Digest printed above instead.")
        else:
            send_digest(
                to_addr=to_addr,
                subject="Grad Program Hunter: new Summer 2027 signals",
                body=digest,
                gmail_user=gmail_user,
                gmail_app_password=gmail_app_password,
            )
            print(f"Digest emailed to {to_addr}.")

    save_state(STATE_PATH, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
