# Gateway-23 Research Miner

This existing repository now contains a scheduled scientific-literature metadata collector.

- Run manually: GitHub **Actions → Gateway-23 literature miner → Run workflow**
- Automatic schedule: daily at 08:17 UTC (GitHub may delay scheduled jobs).
- Download CSV: open a completed workflow run and download the `gateway23-research` artifact.
- Run locally: `python miner.py` (Python 3.12+, no packages).

The initial version searches Crossref for six plasma and wormhole topics and records DOI, title, year, query, source and URL, deduplicated by DOI. It starts from 1950 and requests up to 50 results per topic per run. It does **not** yet search a million databases, extract full text, or validate portal physics. No paid services are enabled.