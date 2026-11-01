#!/usr/bin/env python3
"""Gateway-23 metadata collector: Crossref + OpenAlex; rotating query queue."""
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("data/research.csv")
STATE = Path("data/miner_state.json")
FIELDS = ["doi", "title", "year", "query", "source", "url", "retrieved_utc"]
TOPICS = [
    "magnetic mirror", "field reversed configuration", "plasma vortex",
    "magnetohydrodynamic instability", "plasma confinement", "loss cone",
    "plasma diagnostics", "Helmholtz coils", "magnetic reconnection",
    "quantum energy inequalities", "traversable wormhole", "negative energy",
    "Casimir effect", "scalar tensor gravity", "quantum backreaction",
    "plasma transport", "magnetic field feedback", "plasma turbulence",
    "magnetic nozzle", "particle confinement",
]
QUALIFIERS = [
    "experiment", "measurement", "stability", "simulation", "review",
    "diagnostics", "theory", "laboratory", "confinement", "transport",
    "energy", "magnetic field", "temperature", "density", "pressure",
    "collisions", "instability", "time resolved", "numerical model", "data",
    "scaling", "control", "feedback", "spectroscopy", "field mapping",
    "particle loss", "equilibrium", "magnetic topology", "plasma rotation",
    "ionization", "experimental results", "high beta", "low beta",
    "magnetic mirror ratio", "electromagnetic fields", "vacuum",
    "stress energy tensor", "semiclassical gravity", "quantum fields",
    "field reversal", "energy balance", "uncertainty", "benchmark",
    "reproducibility", "validation", "plasma discharge", "coil design",
    "electron temperature", "ion temperature", "axial losses",
]
# Exactly 20 x 50 = 1,000 search expressions, NOT 1,000 databases.
QUERIES = [f"{a} {b}" for a in TOPICS for b in QUALIFIERS]
PER_RUN = 4

def request(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Gateway23ResearchMiner/0.2 (research; https://github.com/justinnbrwn/hello)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=35) as response:
        return json.load(response)

def crossref(query):
    p = urllib.parse.urlencode({"query.bibliographic": query, "rows": 25,
        "filter": "from-pub-date:1950-01-01",
        "select": "DOI,title,published,URL"})
    for item in request("https://api.crossref.org/works?" + p)["message"]["items"]:
        dates = item.get("published", {}).get("date-parts", [[]])
        yield item.get("DOI"), (item.get("title") or [""])[0], dates[0][0] if dates and dates[0] else "", item.get("URL", "")

def openalex(query):
    p = urllib.parse.urlencode({"search": query, "per-page": 25,
        "filter": "from_publication_date:1950-01-01"})
    for item in request("https://api.openalex.org/works?" + p).get("results", []):
        yield item.get("doi"), item.get("title", ""), item.get("publication_year", ""), item.get("doi", "")

def main():
    records = {}
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("doi"):
                    records[row["doi"]] = row
    state = json.loads(STATE.read_text()) if STATE.exists() else {"next_query": 0}
    start = int(state.get("next_query", 0)) % len(QUERIES)
    failures = 0
    for offset in range(PER_RUN):
        query = QUERIES[(start + offset) % len(QUERIES)]
        for source, fn in [("Crossref", crossref), ("OpenAlex", openalex)]:
            try:
                for doi, title, year, url in fn(query):
                    doi = str(doi or "").lower().replace("https://doi.org/", "").strip()
                    if not doi or doi in records:
                        continue
                    records[doi] = {"doi": doi, "title": title or "", "year": year,
                        "query": query, "source": source, "url": url or "https://doi.org/" + doi,
                        "retrieved_utc": datetime.now(timezone.utc).isoformat()}
                print("OK", source, query)
            except Exception as exc:
                failures += 1
                print("FAILED", source, query, type(exc).__name__, str(exc)[:200])
            time.sleep(2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(records.values(), key=lambda r: (str(r["year"]), r["doi"]), reverse=True))
    STATE.write_text(json.dumps({"next_query": (start + PER_RUN) % len(QUERIES),
        "query_count": len(QUERIES), "last_run_utc": datetime.now(timezone.utc).isoformat(),
        "failures": failures}, indent=2) + "\n")
    print("Unique DOI records:", len(records), "Queries processed:", PER_RUN, "Failures:", failures)

if __name__ == "__main__":
    main()
