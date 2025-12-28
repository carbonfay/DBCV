# PowerShell script to test Wildberries integration via Docker

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Wildberries Integration Test via Docker" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info 2>$null | Out-Null
    Write-Host "[✓] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[✗] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if backend container is running
$backendStatus = docker ps --filter "name=backend_dbcv" --format "{{.Status}}" 2>$null

if (-not $backendStatus) {
    Write-Host "[✗] Backend container is not running" -ForegroundColor Red
    Write-Host "Starting containers..." -ForegroundColor Yellow
    
    cd ..
    docker-compose --env-file env.prod up -d
    
    Write-Host "Waiting 30 seconds for containers to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

Write-Host ""
Write-Host "Running Wildberries integration test..." -ForegroundColor Cyan
Write-Host ""

# Copy test file to container if needed
docker cp test_wb_quick.py backend_dbcv:/backend/test_wb_quick.py 2>$null

# Run the test
docker exec backend_dbcv python /backend/test_wb_quick.py

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "✅ Wildberries integration test PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Integration details:" -ForegroundColor Cyan
    Write-Host "  - ID: wildberries_update_stock" -ForegroundColor White
    Write-Host "  - Version: 1.0.0" -ForegroundColor White
    Write-Host "  - Category: ecommerce" -ForegroundColor White
    Write-Host "  - Description: Обновляет количество товара на Wildberries" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Add Wildberries credentials to database" -ForegroundColor White
    Write-Host "  2. Run integration: docker exec backend_dbcv python /backend/run_wildberries_integration.py" -ForegroundColor White
    Write-Host "  3. Use mock library for development: python -c ""from wildberries_api import Client; c = Client('test'); print(c.update_stock('SKU', 100))""" -ForegroundColor White
} else {
    Write-Host "❌ Wildberries integration test FAILED" -ForegroundColor Red
    Write-Host "Exit code: $exitCode" -ForegroundColor Yellow
}

Write-Host ""
</contents>