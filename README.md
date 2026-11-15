# TalentFlow × Acme: Q3 roadmap exercise

| File | What |
|---|---|
| `SUBMISSION.md` | Memo (D5), verdicts (D1), roadmap (D2), metric spec (D3), data audit (D4), findings table |
| `outputs/findings.csv` | Findings table: claim, metric, value, method, confidence |
| `outputs/data_quality.csv` | All 31 data-quality checks with counts and denominators |
| `outputs/source_funnel.csv` | Per-source applications/hires/hire rate under two attributions |
| `outputs/run_log.txt` | Full stdout of `analyze.py` |
| `fetch.py` | Pulls all 8 tables once (paginated, rate-limited, 429-safe) → `data/raw/*.json` |
| `analyze.py` | All analysis, offline, pandas only |
| `PROCESS.md` | How the session went |

## Re-run
```bash
pip install pandas
cp .env.example .env        # put the Airtable token in it (never in code)
python fetch.py             # ~10 requests, 2-3 seconds
python analyze.py           # writes outputs/*.csv, prints everything
```
Expected headline output: `Job Board app->hire rate: 7/236 = 3.0%`, `Acceptance among decided offers: 26/31 = 83.9%`.
