How to transfer this workspace via Google Drive and resume in VS Code

1) Create ZIP
- The project archive `jobbot_full.zip` is provided in this folder. If you need to recreate it locally, run (PowerShell):
  ```powershell
  cd c:/Users/seun/jobs/jobbot
  Compress-Archive -Path * -DestinationPath ..\jobbot_full.zip
  ```

2) Upload to Google Drive
- Upload `jobbot_full.zip` to your Drive account.
- Set sharing permissions for the target account or copy the file link.

3) Download on the other computer
- Sign in to the target Google account and download `jobbot_full.zip` to a folder, e.g., `C:\Users\you\projects\`.

4) Open in VS Code
- In VS Code: File → Open Folder → select the extracted `jobbot` folder.

5) Setup and run (Windows)
- Create a Python virtual environment and install requirements:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate
  pip install -r requirements.txt
  python -m playwright install chromium
  ```
- Optional: install Node.js + Apify CLI if you plan to deploy to Apify:
  ```powershell
  choco install nodejs
  npm install -g apify-cli
  ```

6) Environment variables
- Add your secrets (do NOT commit to repo):
  - `APIFY_TOKEN` — Apify API token
  - `proxies.txt` — place a file in the repo root with one proxy per line if using proxies

7) Run tools
- Run scraper locally (Playwright):
  ```powershell
  python playwright_full.py
  ```
- Import results into review DB:
  ```powershell
  python import_jobs.py
  ```
- Start review UI:
  ```powershell
  python apply_ui.py
  # open http://127.0.0.1:5000
  ```

8) Troubleshooting
- If Playwright pages time out, run `playwright_debug.py` in headed mode to inspect selectors and behavior.
- If you plan high-volume scraping, enable `proxies.txt` and consider deploying the Apify actor for managed proxies.

Contact
- If you want me to continue remote deployment or tuning, provide the Apify token and I can run/monitor remotely.
