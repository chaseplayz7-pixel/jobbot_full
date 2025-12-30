**Running in Docker (recommended when you don't want to run locally)**

- Build the image (from the repo root):

```powershell
docker build -t jobbot_full:latest .
```

- Run the Playwright full scraper in the container (headless):

```powershell
docker run --rm -v ${PWD}:/app -w /app jobbot_full:latest
```

- To run the lightweight scraper (requests + BS4) instead of Playwright:

```powershell
docker run --rm -v ${PWD}:/app -w /app jobbot_full:latest python scraper.py
```

- If your scraping requires proxies or environment secrets, pass them as env vars or mount files:

```powershell
docker run --rm -v ${PWD}:/app -w /app -e APIFY_TOKEN="${env:APIFY_TOKEN}" -v C:\path\to\proxies.txt:/app/proxies.txt jobbot_full:latest
```

CI (GitHub Actions)
- A workflow is included at `.github/workflows/ci.yml` that runs unit tests and builds a Docker image on push/pull requests.

Publishing to GitHub Container Registry (GHCR)
- The included CI workflow now publishes the built image to GHCR on pushes to `main`.
- After you push this repository to GitHub, Actions will run and publish images to:
	- `ghcr.io/<org-or-username>/jobbot_full:latest`
	- `ghcr.io/<org-or-username>/jobbot_full:<commit-sha>`

Local Docker helpers
- `scripts/install_docker.ps1` — PowerShell helper that attempts to install Docker Desktop (via `winget`) or opens the Docker download page.
- `scripts/run_in_docker.ps1` — builds and runs the container locally. Example:

```powershell
.\scripts\install_docker.ps1   # run as Administrator if installing
.\scripts\run_in_docker.ps1   # builds and runs the Playwright scraper in container
```

Notes
- The container uses the Playwright official Python image which includes browser dependencies. This keeps host setup minimal.
- If you prefer a hosted actor, the `apify_actor_template/` is present and can be adapted for Apify deployment.
