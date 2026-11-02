#!/usr/bin/env python3
"""Focused Gateway-23 literature metadata audit. Discovery only, NOT novelty verification."""
import csv, json, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
OUT=Path("data/wormhole_literature.csv")
QUERIES=[
 "Ellis Bronnikov wormhole conformally coupled scalar scattering",
 "Ellis wormhole scalar zero frequency Jost transmission",
 "Ellis Bronnikov Klein Gordon exact solutions conformal coupling",
 "wormhole quantum field Hadamard V0 V1 transport",
 "Ellis wormhole renormalized stress tensor point splitting",
 "wormhole quantum energy inequalities semiclassical backreaction",
 "Ellis wormhole scalar Euclidean Green function spectral resolvent",
]
FIELDS=["doi","title","year","query","source","url","retrieved_utc","relevance_flag"]
KEYWORDS=("wormhole","ellis","bronnikov","hadamard","semiclassical","quantum energy","jost","green function","point splitting")
def request(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Gateway23FocusedAudit/1.0 (https://github.com/justinnbrwn/hello)","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=35) as response:return json.load(response)
def crossref(query):
 params=urllib.parse.urlencode({"query.bibliographic":query,"rows":30,"select":"DOI,title,published,URL"})
 for item in request("https://api.crossref.org/works?"+params)["message"]["items"]:
  dates=item.get("published",{}).get("date-parts",[[]])
  yield item.get("DOI"),(item.get("title") or [""])[0],dates[0][0] if dates and dates[0] else "",item.get("URL","")
def main():
 records={}
 if OUT.exists():
  with OUT.open(encoding="utf-8",newline="") as f:
   for row in csv.DictReader(f):
    if row.get("doi"):records[row["doi"]]=row
 errors=[]
 for query in QUERIES:
  try:
   for doi,title,year,url in crossref(query):
    doi=str(doi or "").lower().replace("https://doi.org/","").strip()
    if not doi:continue
    flag="candidate_title_match" if any(word in title.lower() for word in KEYWORDS) else "manual_screen_needed"
    if doi not in records:
     records[doi]=dict(doi=doi,title=title,year=year,query=query,source="Crossref",url=url or "https://doi.org/"+doi,retrieved_utc=datetime.now(timezone.utc).isoformat(),relevance_flag=flag)
  except Exception as exc:errors.append({"query":query,"error":str(exc)})
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open("w",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(sorted(records.values(),key=lambda x:x["doi"]))
 Path("data/wormhole_audit_status.json").write_text(json.dumps({"timestamp_utc":datetime.now(timezone.utc).isoformat(),"unique_dois":len(records),"queries":len(QUERIES),"errors":errors,"warning":"Metadata search only. Relevance and novelty require manual full-text equation comparison."},indent=2)+"\n")
 print("DOIs",len(records),"query errors",len(errors))
 if errors:raise SystemExit(1)
if __name__=="__main__":main()
