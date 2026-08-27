"""Fetches a career page with a headless browser and extracts its visible text.

Uses Playwright (not plain requests) because many bank career sites are
JS-rendered SPAs that don't return usable content from a raw HTTP fetch.
"""
import hashlib

from playwright.sync_api import sync_playwright


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class Scraper:
    def __init__(self, timeout_ms: int = 30000, settle_ms: int = 3000):
        self.timeout_ms = timeout_ms
        self.settle_ms = settle_ms
        self._playwright = None
        self._browser = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._browser.close()
        self._playwright.stop()

    def check_page(self, url: str) -> dict:
        try:
            page = self._browser.new_page(user_agent=USER_AGENT)
            # domcontentloaded, not networkidle: many career sites run
            # persistent chat-widget/analytics polling that never goes
            # network-idle, which turned real page loads into false timeouts.
            page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(self.settle_ms)
            text = page.inner_text("body")
            page.close()
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return {"ok": True, "hash": digest, "text": text, "error": None}
        except Exception as e:
            return {"ok": False, "hash": None, "text": "", "error": str(e)}
