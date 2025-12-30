<#
PowerShell helper to install Docker Desktop on Windows.
This attempts to use winget; if not available it will open the Docker download page.

Run as an elevated PowerShell (Run as Administrator) to perform a full install.
#>

Write-Host "Checking for Docker..."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker already installed."
    exit 0
}

Write-Host "Attempting to install Docker Desktop via winget..."
if (Get-Command winget -ErrorAction SilentlyContinue) {
    try {
        winget install --id Docker.DockerDesktop -e --accept-package-agreements --accept-source-agreements
        Write-Host "Docker Desktop installation (winget) triggered. You may need to log out/in after install."
    } catch {
        Write-Warning "winget install failed: $_"
        Start-Process "https://www.docker.com/get-started" -UseShellExecute
        Write-Host "Opened Docker download page. Please download and install Docker Desktop manually."
    }
} else {
    Write-Warning "winget not found. Opening Docker download page in browser."
    Start-Process "https://www.docker.com/get-started" -UseShellExecute
    Write-Host "Please download Docker Desktop for Windows and install it, then rerun this script."
}

Write-Host "After installing Docker Desktop, ensure WSL2 (optional) or Hyper-V is configured per Docker docs."
