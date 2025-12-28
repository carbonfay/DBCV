# Wildberries Integration - Improved Test & Run Script
# ============================================================

Write-Host "" 
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Wildberries Integration - Test & Run" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Переходим в директорию скрипта
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Функция для проверки существования файла
function Test-FileExists {
    param([string]$FilePath)
    if (Test-Path $FilePath) {
        Write-Host "[OK] Found: $FilePath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[ERROR] Not found: $FilePath" -ForegroundColor Red
        return $false
    }
}

# Функция для безопасного запуска Python скриптов
function Invoke-PythonScript {
    param(
        [string]$ScriptPath,
        [string]$Description
    )
    
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Running: $Description" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $ScriptPath -NoNewWindow -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Host "" 
            Write-Host "[SUCCESS] $Description completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host ""
            Write-Host "[ERROR] $Description failed with exit code: $($process.ExitCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host ""
        Write-Host "[ERROR] Failed to run $Description : $_" -ForegroundColor Red
        return $false
    }
}

# Шаг 1: Проверка файлов
Write-Host "Step 1: Checking files..." -ForegroundColor Cyan
Write-Host ""

$files = @(
    "run_wildberries_test.py",
    "run_wildberries_integration.py",
    "wildberries_api.py",
    "app/integrations/Wildberries/update_stock.py"
)

$allFilesExist = $true
foreach ($file in $files) {
    if (-not (Test-FileExists $file)) {
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "[ERROR] Some required files are missing!" -ForegroundColor Red
    Write-Host "Please ensure all integration files are present." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[OK] All required files found" -ForegroundColor Green

# Шаг 2: Проверка Mock библиотеки
Write-Host ""
Write-Host "Step 2: Checking wildberries_api mock library..." -ForegroundColor Cyan
Write-Host ""

$mockLibraryCheck = python -c "import wildberries_api; print('OK')"
if ($mockLibraryCheck -eq "OK") {
    Write-Host "[OK] wildberries_api library is available" -ForegroundColor Green
    
    $version = python -c "import wildberries_api; print(wildberries_api.__version__)"
    Write-Host "[INFO] Version: $version" -ForegroundColor Cyan
} else {
    Write-Host "[WARNING] wildberries_api library not found" -ForegroundColor Yellow
    Write-Host "[INFO] Using mock library from wildberries_api.py" -ForegroundColor Cyan
}

# Шаг 3: Запуск теста регистрации
Write-Host ""
Write-Host "Step 3: Running registration test..." -ForegroundColor Cyan

$testResult = Invoke-PythonScript -ScriptPath "run_wildberries_test.py" -Description "Registry Test"

if (-not $testResult) {
    Write-Host ""
    Write-Host "[ERROR] Registry test failed!" -ForegroundColor Red
    Write-Host "[INFO] Please check the integration registration." -ForegroundColor Yellow
    
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Шаг 4: Выбор режима запуска
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Integration Execution Options" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Run with environment variables (.env file)" -ForegroundColor White
Write-Host "2. Run in interactive mode (manual input)" -ForegroundColor White
Write-Host "3. Run minimal structure test (no DB)" -ForegroundColor White
Write-Host "4. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select option (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "[INFO] Running with environment variables..." -ForegroundColor Cyan
        
        if (-not (Test-Path ".env")) {
            Write-Host "[WARNING] .env file not found" -ForegroundColor Yellow
            Write-Host "[INFO] Please create .env file from .env.example" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Example .env content:" -ForegroundColor Yellow
            Write-Host "WB_BOT_ID=your-bot-uuid"
            Write-Host "WB_TEST_SKU=TEST-SKU-123"
            Write-Host "WB_TEST_STOCK=100"
            Write-Host "WB_DRY_RUN=true"
            exit 1
        }
        
        Invoke-PythonScript -ScriptPath "run_wildberries_integration.py" -Description "Wildberries Integration"
    }
    "2" {
        Write-Host ""
        Write-Host "[INFO] Running in interactive mode..." -ForegroundColor Cyan
        Invoke-PythonScript -ScriptPath "run_wildberries_integration.py" -Description "Wildberries Integration (Interactive)"
    }
    "3" {
        Write-Host ""
        Write-Host "[INFO] Running minimal structure test..." -ForegroundColor Cyan
        Invoke-PythonScript -ScriptPath "minimal_wb_test.py" -Description "Minimal Structure Test"
    }
    "4" {
        Write-Host ""
        Write-Host "[INFO] Exiting..." -ForegroundColor Cyan
        exit 0
    }
    default {
        Write-Host ""
        Write-Host "[ERROR] Invalid option" -ForegroundColor Red
        exit 1
    }
}

# Финальное сообщение
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Script Completed" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "For more information, see:" -ForegroundColor Yellow
Write-Host "  - WILDBERRIES_INTEGRATION_GUIDE.md" -ForegroundColor White
Write-Host "  - README.md" -ForegroundColor White
Write-Host ""
