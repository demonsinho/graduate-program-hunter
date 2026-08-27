"""Google Programmable Search (Custom Search JSON API) lookup for a firm.

Used as a secondary detection signal alongside direct career-page scraping —
catches postings that show up on job boards/LinkedIn before (or instead of)
a firm's own career page.
"""
import requests

SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def search_firm(firm_name: str, api_key: str, cse_id: str, num: int = 5) -> dict:
    query = f"{firm_name} graduate programme 2027"
    try:
        resp = requests.get(
            SEARCH_ENDPOINT,
            params={"key": api_key, "cx": cse_id, "q": query, "num": num},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        urls = [item["link"] for item in data.get("items", [])]
        return {"ok": True, "urls": urls, "error": None}
    except Exception as e:
        # requests' HTTPError message embeds the full request URL, which
        # includes the API key/CSE ID as query params — never let those
        # reach logs, the digest email, or the committed/published dashboard.
        error = str(e).replace(api_key, "***").replace(cse_id, "***")
        return {"ok": False, "urls": [], "error": error}
