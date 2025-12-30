<#
Builds the Docker image and runs the Playwright full scraper inside a container.
Requires Docker to be installed and running.
#>

param(
    [switch]$BuildOnly
)

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker command not found. Install Docker Desktop first. See scripts/install_docker.ps1"
    exit 1
}

$imageName = 'jobbot_full:local'

Write-Host "Building image $imageName..."
docker build -t $imageName .

if ($BuildOnly) { exit 0 }

Write-Host "Running Playwright full scraper inside container (this will use network)."
docker run --rm -v ${PWD}:/app -w /app $imageName python playwright_full.py
