# Grad Program Hunter

Tracks Summer 2027 graduate programme openings at banks, boutiques, and
other finance firms in Madrid, London, Dublin, the Netherlands, and other
EU countries with English-language programmes. Runs daily via GitHub
Actions and emails a digest when it detects a signal.

## How detection works

- **Career page scraping (daily)**: each firm/location in `config/firms.yaml`
  has a `career_url`. Every run fetches the page (via a headless browser,
  since many career sites are JS-rendered), and flags it if the page's
  content changed *and* now mentions "2027" compared to the last run.
- **Search check (weekly, per firm)**: once every 7 days per firm, runs a
  Google Programmable Search query (`"<firm> graduate programme 2027"`) and
  flags any new result URL not seen last time — catches postings that show
  up on job boards/LinkedIn before a firm's own career page updates.
- Fetch/search failures never crash the run — they're logged and listed in
  a "needs manual check" section instead.
- An email digest is only sent when there's an actual signal (page change
  or new search result); a quiet day just prints "No changes detected."
  to the run log.

## Editing the firm list

Edit `config/firms.yaml`. Each entry:

```yaml
- name: Firm Name
  tier: 1
  locations:
    - location: Madrid
      career_url: https://example.com/careers
      verify: true   # remove once you've confirmed the URL is correct
```

Every URL currently in the file is a best-effort guess and marked
`verify: true` — none have been live-checked yet. Open each one once,
confirm it's the right early-careers/graduate page, and remove the
`verify` flag (or fix the URL) as you go. A broken URL doesn't break the
tracker; it just shows up in the "needs manual check" email/log section
until fixed.

## Secrets (GitHub Actions)

Set these as repo secrets (`gh secret set NAME` or Settings → Secrets and
variables → Actions):

| Secret | Purpose |
|---|---|
| `GMAIL_USER` | Gmail address the digest is sent from (and to, by default) |
| `GMAIL_APP_PASSWORD` | [Gmail App Password](https://myaccount.google.com/apppasswords) (not your normal password — requires 2FA enabled) |
| `GOOGLE_CSE_API_KEY` | Google Cloud API key with the Custom Search API enabled |
| `GOOGLE_CSE_ID` | Search Engine ID from [Programmable Search Engine](https://programmablesearchengine.google.com/) (configure it to search the whole web) |

If the search-related secrets are missing, the tracker skips search checks
and still runs career-page scraping. If the email secrets are missing, it
prints the digest instead of emailing.

## Running locally

```bash
pip install -r requirements.txt
playwright install chromium

# PowerShell
$env:GMAIL_USER = "you@gmail.com"
$env:GMAIL_APP_PASSWORD = "..."
$env:GOOGLE_CSE_API_KEY = "..."
$env:GOOGLE_CSE_ID = "..."
python src/main.py
```

The first run against any given firm/location just records a baseline
(nothing to compare against yet) — it won't email anything, but it will
populate `state.json` and the "needs manual check" list for any bad URLs.
Fix those, then run again to confirm a clean pass before relying on the
scheduled workflow.

## Schedule

`.github/workflows/daily-check.yml` runs daily at 07:00 UTC
(`workflow_dispatch` is also enabled for manual runs via
`gh workflow run daily-check.yml`). Adjust the cron expression if you want
a different time.
