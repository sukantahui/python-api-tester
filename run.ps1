# PyRestForge - PowerShell Launch Script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[PyRestForge] Launching Application..." -ForegroundColor Cyan

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython "src\main.py" $args
} else {
    & python "src\main.py" $args
}
