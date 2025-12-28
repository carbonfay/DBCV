# Wildberries Integration Test Script
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Wildberries Integration Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Переходим в директорию скрипта
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Запускаем тест
Write-Host "Running test..." -ForegroundColor Yellow
python run_wildberries_test.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Test completed" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "To run the full integration with real data, use:" -ForegroundColor Yellow
Write-Host "  python run_wildberries_integration.py" -ForegroundColor White
Write-Host ""
