JobBot — Canada TPM / Data Center / Physical Security Job Scanner

Overview
- Lightweight scraper that collects job postings from JobBank (jobbank.gc.ca) and Indeed Canada (indeed.ca).
- Filters: Canada-wide, non-remote, senior/TPM/PM/data center/physical security keywords, LMIA/GTS cue detection.
- Outputs CSV: `jobs_results.csv` with basic fields + visa signal score.

Quick start
1. Create and activate a Python 3.10+ venv.

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows
pip install -r requirements.txt
```

2. Run the scanner (default keywords cover TPM / Program Manager / Physical Security):

```bash
python scraper.py
```

3. Output: `jobs_results.csv` in the project folder.

Notes & next steps
- LinkedIn, Workday, Greenhouse, and site-specific ATS pages require Playwright and authenticated automation — I can add Playwright actors next.
- This initial version parses public HTML and may require selector tuning over time.
- To add auto-apply or Playwright scraping, confirm whether you want headless credentials stored and I will add secure storage instructions.
