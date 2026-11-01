#!/usr/bin/env python3
"""Gateway-23 literature metadata miner; standard library only."""
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

QUERIES = [
    "magnetic mirror plasma confinement",
    "field reversed configuration plasma stability",
    "plasma loss cone collisions",
    "traversable wormhole quantum energy inequalities",
    "magnetic confinement plasma diagnostics",
    "plasma vortex magnetic field experiment",
]
OUT = Path("data/research.csv")
FIELDS = ["doi", "title", "year", "query", "source", "url", "retrieved_utc"]

def search(query):
    params = urllib.parse.urlencode({
        "query.bibliographic": query, "rows": 50,
        "filter": "from-pub-date:1950-01-01",
        "select": "DOI,title,published,URL",
    })
    url = "https://api.crossref.org/works?" + params
    request = urllib.request.Request(url, headers={
        "User-Agent": "Gateway23ResearchMiner/0.1 (research metadata; https://github.com/justinnbrwn/hello)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)["message"]["items"]

def main():
    records = {}
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("doi"):
                    records[row["doi"]] = row
    for query in QUERIES:
        try:
            for item in search(query):
                doi = str(item.get("DOI", "")).lower().strip()
                if not doi:
                    continue
                parts = item.get("published", {}).get("date-parts", [[]])
                year = parts[0][0] if parts and parts[0] else ""
                records[doi] = {
                    "doi": doi, "title": (item.get("title") or [""])[0],
                    "year": year, "query": query, "source": "Crossref",
                    "url": item.get("URL", "https://doi.org/" + doi),
                    "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                }
            print("OK", query)
        except Exception as exc:
            print("FAILED", query, type(exc).__name__, str(exc)[:200])
        time.sleep(2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(records.values(), key=lambda r: (str(r["year"]), r["doi"]), reverse=True))
    print("Unique records:", len(records), "Saved:", OUT)

if __name__ == "__main__":
    main()
