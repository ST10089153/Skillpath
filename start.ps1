# Start SkillPath locally: the API in a new window, the Expo web app in this one.
# Usage (from the repo folder):  .\start.ps1
# Phone via Expo Go:             .\start.ps1 -Phone
param([switch]$Phone)

$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment and installing requirements (first run only)..."
    python -m venv (Join-Path $root ".venv")
    & $python -m pip install -q -r (Join-Path $root "requirements.txt")
}
if (-not (Test-Path (Join-Path $root "app\node_modules"))) {
    Write-Host "Installing app packages (first run only)..."
    Push-Location (Join-Path $root "app"); npm install; Pop-Location
}

$apiHost = if ($Phone) { "0.0.0.0" } else { "127.0.0.1" }
Start-Process powershell -WorkingDirectory $root -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle='SkillPath API'; & '$python' -m uvicorn api.main:app --host $apiHost --port 8000")

Set-Location (Join-Path $root "app")
if ($Phone) {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 |
           Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.PrefixOrigin -ne "WellKnown" } |
           Select-Object -First 1).IPAddress
    $env:EXPO_PUBLIC_API_URL = "http://${ip}:8000"
    Write-Host "API for phone: $env:EXPO_PUBLIC_API_URL  (scan the QR code with Expo Go)"
    npx expo start
} else {
    Write-Host "Opening SkillPath at http://localhost:8081 ... (Ctrl+C here stops the app; close the 'SkillPath API' window to stop the API)"
    npx expo start --web
}
