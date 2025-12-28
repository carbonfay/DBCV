# Docker Container Health Check and Start Script
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  DBCV Docker Container Health Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Переходим в директорию проекта
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Функция для проверки существования файла
function Test-FileExists {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        Write-Host "[✓] Found: $FilePath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[✗] Missing: $FilePath" -ForegroundColor Red
        return $false
    }
}

# Функция для вывода статуса контейнера
function Get-ContainerStatus {
    param([string]$ContainerName)
    
    $status = docker ps -a --filter "name=$ContainerName" --format "{{.Status}}" 2>$null
    
    if ($status) {
        if ($status -match "Up.*healthy") {
            Write-Host "[✓] $ContainerName : Healthy" -ForegroundColor Green
            return "healthy"
        }
        elseif ($status -match "Up") {
            Write-Host "[!] $ContainerName : Running (checking health...)" -ForegroundColor Yellow
            return "running"
        }
        elseif ($status -match "Restarting") {
            Write-Host "[✗] $ContainerName : Restarting (error)" -ForegroundColor Red
            return "restarting"
        }
        elseif ($status -match "Exited") {
            Write-Host "[✗] $ContainerName : Exited" -ForegroundColor Red
            return "exited"
        }
        else {
            Write-Host "[!] $ContainerName : $status" -ForegroundColor Yellow
            return "unknown"
        }
    }
    else {
        Write-Host "[?] $ContainerName : Not found" -ForegroundColor Gray
        return "not_found"
    }
}

# Шаг 1: Проверка файлов конфигурации
Write-Host "Step 1: Checking configuration files..." -ForegroundColor Cyan
Write-Host ""

$envProdExists = Test-FileExists "env.prod"
$dockerComposeExists = Test-FileExists "docker-compose.yml"

if (-not $envProdExists) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "  WARNING: env.prod file is missing!" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  1. Generate secure secrets automatically" -ForegroundColor White
    Write-Host "  2. Copy from env.example manually" -ForegroundColor White
    Write-Host "  3. Exit" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Select option (1-3)"
    
    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "Generating secure secrets..." -ForegroundColor Cyan
            python generate_secrets.py
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host ""
                Write-Host "[✗] Failed to generate secrets" -ForegroundColor Red
                Write-Host "Falling back to manual copy..." -ForegroundColor Yellow
                Copy-Item "env.example" "env.prod"
                Write-Host "[!] IMPORTANT: Edit env.prod and change all passwords!" -ForegroundColor Yellow
            }
        }
        "2" {
            Write-Host ""
            Write-Host "Copying env.example to env.prod..." -ForegroundColor Cyan
            Copy-Item "env.example" "env.prod"
            Write-Host "[!] IMPORTANT: Edit env.prod and change all passwords!" -ForegroundColor Yellow
        }
        "3" {
            Write-Host ""
            Write-Host "Exiting..." -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "[✗] Invalid option" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""

# Шаг 2: Проверка Docker
Write-Host "Step 2: Checking Docker..." -ForegroundColor Cyan
Write-Host ""

$dockerRunning = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[✗] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "[✓] Docker is running" -ForegroundColor Green
Write-Host ""

# Шаг 3: Проверка статуса контейнеров
Write-Host "Step 3: Checking container status..." -ForegroundColor Cyan
Write-Host ""

$containers = @(
    "postgres_dbcv",
    "redis_dbcv",
    "cache_redis_dbcv",
    "s3_dbcv",
    "backend_dbcv",
    "mcp_dbcv",
    "scheduler_dbcv",
    "dbcv-faststream-bot-1",
    "dbcv-faststream-user-1"
)

$statuses = @{}
foreach ($container in $containers) {
    $status = Get-ContainerStatus $container
    $statuses[$container] = $status
}

Write-Host ""

# Подсчет проблемных контейнеров
$problematic = ($statuses.Values | Where-Object { $_ -in @("restarting", "exited", "not_found") }).Count
$healthy = ($statuses.Values | Where-Object { $_ -eq "healthy" }).Count

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Healthy: $healthy" -ForegroundColor Green
Write-Host "  Problematic: $problematic" -ForegroundColor $(if ($problematic -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Шаг 4: Действия
if ($problematic -gt 0) {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "  Some containers have issues" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Cyan
    Write-Host "  1. View logs of problematic containers" -ForegroundColor White
    Write-Host "  2. Restart all containers" -ForegroundColor White
    Write-Host "  3. Stop and remove all containers (clean restart)" -ForegroundColor White
    Write-Host "  4. Exit" -ForegroundColor White
    Write-Host ""
    
    $action = Read-Host "Select action (1-4)"
    
    switch ($action) {
        "1" {
            Write-Host ""
            Write-Host "Showing logs for problematic containers..." -ForegroundColor Cyan
            Write-Host ""
            
            foreach ($container in $containers) {
                if ($statuses[$container] -in @("restarting", "exited")) {
                    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
                    Write-Host "Logs for: $container" -ForegroundColor Yellow
                    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
                    docker logs $container --tail 30
                    Write-Host ""
                }
            }
        }
        "2" {
            Write-Host ""
            Write-Host "Restarting all containers..." -ForegroundColor Cyan
            docker-compose restart
            Write-Host ""
            Write-Host "[✓] Containers restarted" -ForegroundColor Green
            Write-Host "Waiting 10 seconds for health checks..." -ForegroundColor Cyan
            Start-Sleep -Seconds 10
            
            Write-Host ""
            Write-Host "Updated status:" -ForegroundColor Cyan
            docker-compose ps
        }
        "3" {
            Write-Host ""
            Write-Host "[!] This will stop and remove all containers!" -ForegroundColor Yellow
            $confirm = Read-Host "Are you sure? (yes/no)"
            
            if ($confirm -eq "yes") {
                Write-Host ""
                Write-Host "Stopping containers..." -ForegroundColor Cyan
                docker-compose down
                
                Write-Host "Starting containers..." -ForegroundColor Cyan
                docker-compose up -d
                
                Write-Host ""
                Write-Host "[✓] Containers restarted from scratch" -ForegroundColor Green
                Write-Host "Waiting 15 seconds for initialization..." -ForegroundColor Cyan
                Start-Sleep -Seconds 15
                
                Write-Host ""
                Write-Host "Updated status:" -ForegroundColor Cyan
                docker-compose ps
            }
            else {
                Write-Host "Operation cancelled" -ForegroundColor Yellow
            }
        }
        "4" {
            Write-Host ""
            Write-Host "Exiting..." -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host ""
            Write-Host "[✗] Invalid action" -ForegroundColor Red
            exit 1
        }
    }
else {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  All containers are healthy!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services are ready:" -ForegroundColor Cyan
    Write-Host "  Backend API: http://localhost:8003" -ForegroundColor White
    Write-Host "  MCP Service: http://localhost:8005" -ForegroundColor White
    Write-Host "  MinIO Console: http://localhost:9002" -ForegroundColor White
    Write-Host "  MinIO API: http://localhost:9000" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Script Completed" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
