Apify Actor Template — Job Scanner

Overview
- This actor is a template for Apify to scrape job postings and return structured results. It is intended to be deployed on Apify and scheduled.

Files
- `main.py` — actor entry (Python). Uses Playwright to visit JobBank and provided company career pages.
- `package.json` — actor metadata.

Deploy
1. Create an Apify account and copy your API token.
2. Install Apify CLI or use the web UI to create a new actor and upload the files.
3. Configure environment variables for keywords and target companies.

Notes
- Apify provides managed proxies to avoid blocking.
- For LinkedIn/Indeed scale use Apify Marketplace actors or the Actors that include autoscaling and CAPTCHA handling.
