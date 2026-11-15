"""Pull every table from the Acme Airtable base once and cache it to data/raw/<Table>.json.

Usage:
    export AIRTABLE_TOKEN=pat...        # or put AIRTABLE_TOKEN=... in a .env file next to this script
    python fetch.py

Respects the API constraints: max 100 records/page (follows `offset`), and stays under
5 req/s per base (sleeps 0.25s between calls; on a 429 it waits 31s and retries).
"""
import json
import os
import pathlib
import time
import urllib.parse
import urllib.request
import urllib.error

BASE_ID = "appYePRAI75PMbQNQ"
TABLES = ["Departments", "People", "Job Openings", "Candidates",
          "Applications", "Interviews", "Offers", "Findings"]
OUT = pathlib.Path(__file__).parent / "data" / "raw"


def token() -> str:
    tok = os.environ.get("AIRTABLE_TOKEN")
    env = pathlib.Path(__file__).parent / ".env"
    if not tok and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("AIRTABLE_TOKEN="):
                tok = line.split("=", 1)[1].strip()
    if not tok:
        raise SystemExit("Set AIRTABLE_TOKEN in the environment or a .env file")
    return tok


def get(url: str, tok: str) -> dict:
    while True:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("  429 rate-limited; waiting 31s")
                time.sleep(31)
                continue
            raise


def pull(table: str, tok: str) -> list:
    records, offset = [], None
    while True:
        q = {"pageSize": 100}
        if offset:
            q["offset"] = offset
        url = f"https://api.airtable.com/v0/{BASE_ID}/{urllib.parse.quote(table)}?{urllib.parse.urlencode(q)}"
        page = get(url, tok)
        records += page["records"]
        offset = page.get("offset")
        time.sleep(0.25)
        if not offset:
            return records


def main():
    tok = token()
    OUT.mkdir(parents=True, exist_ok=True)
    for t in TABLES:
        recs = pull(t, tok)
        (OUT / f"{t.replace(' ', '_')}.json").write_text(json.dumps(recs, indent=1))
        print(f"{t:14s} {len(recs):4d} records")


if __name__ == "__main__":
    main()
