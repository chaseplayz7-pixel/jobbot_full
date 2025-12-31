# JobBot — Ultimate Job Finder

## Overview
- Comprehensive job scraper that collects job postings from 8+ major job sites including JobBank, Indeed, LinkedIn, Glassdoor, Google Jobs, Monster, ZipRecruiter, and company ATS pages.
- Filters: Canada-wide, customizable keywords (default: software, data, engineer, developer, etc.), keyword matching in title/company/description.
- Outputs CSV: `jobs_results.csv` with fields: source, title, company, location, link, description.
- Features: Anti-detection measures (random user agents), CAPTCHA handling via user input, dynamic job loading via scrolling, card-based extraction for stability.

## Quick Start
1. Create and activate a Python 3.10+ venv.

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows
pip install -r requirements.txt
```

2. Configure sources and keywords in `search_control.yaml` (optional, defaults provided).

3. Run the scanner:

```bash
python playwright_full.py
```

4. (Optional) View results in web UI:

```bash
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

## Configuration
Edit `search_control.yaml` to:
- Enable/disable job sources (e.g., set `linkedin: true` for more results)
- Customize keywords for your search
- Adjust max jobs per source
- Add target companies for ATS scraping

## Features
- **Multi-Site Scraping**: Covers major Canadian and international job boards
- **Stealth Mode**: Random user agents, context isolation, scrolling for dynamic loading
- **CAPTCHA Handling**: Prompts user to solve CAPTCHAs manually (no paid services)
- **Keyword Filtering**: Matches jobs based on customizable keywords
- **Error Recovery**: Retries failed scrapes with backoff
- **CI/CD**: Automated runs via GitHub Actions

## Notes & Future Improvements
- For better stealth, consider adding proxy rotation (proxies.py exists but not integrated)
- UI for result browsing planned for next phase
- Selector tuning may be needed if sites change layout
- Headless mode disabled for CAPTCHA solving
