# Start SkillPath: the API in a new window, the Expo web app in this one.
# Usage (from the repo folder):
#   .\start.ps1          this computer only        -> http://localhost:8081
#   .\start.ps1 -Phone   phone via Expo Go (same Wi-Fi)
#   .\start.ps1 -Live    public live link via a Cloudflare quick tunnel (needs cloudflared; no account)
param([switch]$Phone, [switch]$Live)

$root = $PSScriptRoot
# Call npx.cmd / npm.cmd directly: launching npx.ps1 from inside a script can exit silently in some setups.
$npx = (Get-Command npx.cmd -ErrorAction SilentlyContinue).Source
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npx) {
    Write-Host "Node.js was not found. Install Node.js LTS from https://nodejs.org, reopen the terminal and try again."
    exit 1
}

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment and installing requirements (first run only)..."
    python -m venv (Join-Path $root ".venv")
    & $python -m pip install -q -r (Join-Path $root "requirements.txt")
}
if (-not (Test-Path (Join-Path $root "app\node_modules"))) {
    Write-Host "Installing app packages (first run only)..."
    Push-Location (Join-Path $root "app"); & $npm install; Pop-Location
}
if ($Live -and -not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "cloudflared is not installed. Install it once with:"
    Write-Host "  winget install --id Cloudflare.cloudflared"
    Write-Host "then close and reopen the terminal and run .\start.ps1 -Live again."
    exit 1
}

function Start-App([string[]]$expoArgs) {
    & $npx expo start @expoArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "The app server stopped (exit code $LASTEXITCODE). Run this to see the error:"
        Write-Host "  cd app; npx.cmd expo start --web"
    }
}

function Start-Tunnel([int]$port) {
    # Cloudflare quick tunnel: prints a random https://<words>.trycloudflare.com address on stderr.
    $log = Join-Path $env:TEMP "skillpath-tunnel-$port.log"
    Remove-Item $log -ErrorAction SilentlyContinue
    $proc = Start-Process cloudflared -ArgumentList @("tunnel", "--no-autoupdate", "--url", "http://localhost:$port") `
        -RedirectStandardError $log -NoNewWindow -PassThru
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $log) {
            $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
            if ($m) { return @{ Url = $m.Matches[0].Value; Process = $proc } }
        }
    }
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    throw "Could not open a tunnel for port $port (see $log)."
}

$apiHost = if ($Phone) { "0.0.0.0" } else { "127.0.0.1" }
Start-Process powershell -WorkingDirectory $root -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle='SkillPath API'; & '$python' -m uvicorn api.main:app --host $apiHost --port 8000")

Push-Location (Join-Path $root "app")
try {
    if ($Live) {
        $tunnels = @()
        try {
            Write-Host "Opening live tunnels (about 10-20 seconds)..."
            $api = Start-Tunnel 8000; $tunnels += $api.Process
            $env:EXPO_PUBLIC_API_URL = $api.Url
            $app = Start-Tunnel 8081; $tunnels += $app.Process
            Write-Host ""
            Write-Host "=================================================================="
            Write-Host " SkillPath LIVE LINK:  $($app.Url)"
            Write-Host " (API: $($api.Url))"
            Write-Host " Works while this terminal and the 'SkillPath API' window stay open."
            Write-Host " Anyone with the link can open it: share only for demos."
            Write-Host "=================================================================="
            Write-Host ""
            Start-App @("--web", "--port", "8081")
        } finally {
            $tunnels | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }
            Write-Host "Live tunnels closed."
        }
    } elseif ($Phone) {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 |
               Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.PrefixOrigin -ne "WellKnown" } |
               Select-Object -First 1).IPAddress
        $env:EXPO_PUBLIC_API_URL = "http://${ip}:8000"
        Write-Host "API for phone: $env:EXPO_PUBLIC_API_URL  (scan the QR code with Expo Go)"
        Start-App @()
    } else {
        Write-Host "Starting SkillPath. When you see 'Waiting on http://localhost:8081', open http://localhost:8081"
        Write-Host "(Ctrl+C here stops the app; close the 'SkillPath API' window to stop the API)"
        Start-App @("--web", "--port", "8081")
    }
} finally {
    Pop-Location
}
