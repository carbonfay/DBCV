# 🐳 Docker Containers Troubleshooting Guide

## 🚨 Текущая проблема

### Статус контейнеров

**Проблемы:**
- ❌ PostgreSQL перезапускается (переменные окружения не загружаются)
- ❌ Backend, MCP, Scheduler перезапускаются (зависят от PostgreSQL)
- ⚠️ Cache Redis unhealthy
- ✅ Redis, S3 работают нормально

**Основная причина:** 
Файл `env.prod` НЕ читается автоматически через `env_file: - env.prod` в docker-compose.yml

---

## 💡 Решения

### ✅ Решение 1: Использовать .env (Рекомендуется)

Docker Compose автоматически читает файл `.env` из той же директории:

```bash
# 1. Переименуйте env.prod в .env
cd DBCV
Rename-Item env.prod .env

# 2. Перезапустите контейнеры
docker-compose down
docker-compose up -d

# 3. Проверьте статус через 30 секунд
Start-Sleep -Seconds 30
docker-compose ps
```

**Почему это работает:**
Docker Compose автоматически загружает `.env` для подстановки переменных в `docker-compose.yml`

---

### ✅ Решение 2: Экспортировать переменные окружения

```powershell
# Загрузить переменные в текущую сессию PowerShell
Get-Content DBCV/env.prod | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Запустить docker-compose
cd DBCV
docker-compose up -d
```

---

### ✅ Решение 3: Использовать env.dev

Если у вас есть рабочий `env.dev`:

```bash
# 1. Используйте dev конфигурацию
cd DBCV
cp env.dev .env

# 2. Запустите
docker-compose down
docker-compose up -d
```

---

### ✅ Решение 4: Исправить docker-compose.yml

Измените `docker-compose.yml` чтобы использовать правильный env файл:

```yaml
# Было:
env_file:
  - env.prod

# Должно быть:
env_file:
  - .env  # или ${ENV_FILE:-.env}
```

---

## 🔍 Диагностика

### Проверка загрузки переменных

```powershell
# Проверить какие переменные видит docker-compose
docker-compose config | Select-String -Pattern "POSTGRES_PASSWORD"

# Проверить переменные в запущенном контейнере
docker exec postgres_dbcv env | grep POSTGRES
```

### Проверка логов

```powershell
# PostgreSQL
docker logs postgres_dbcv --tail 50

# Backend
docker logs backend_dbcv --tail 50

# MCP
docker logs mcp_dbcv --tail 50
```

### Проверка здоровья

```powershell
# Статус всех контейнеров
docker-compose ps

# Детальная информация о контейнере
docker inspect postgres_dbcv | ConvertFrom-Json | Select-Object -ExpandProperty State
```

---

## 🎯 Быстрое решение (ВЫПОЛНИТЕ СЕЙЧАС)

```powershell
# === ШАГ 1: Остановите контейнеры ===
cd DBCV
docker-compose down

# === ШАГ 2: Переименуйте env.prod в .env ===
if (Test-Path .env) { Remove-Item .env }
Rename-Item env.prod .env

# === ШАГ 3: Запустите контейнеры ===
docker-compose up -d

# === ШАГ 4: Подождите 30 секунд ===
Write-Host "Ожидание запуска контейнеров..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# === ШАГ 5: Проверьте статус ===
Write-Host "\nСтатус контейнеров:" -ForegroundColor Cyan
docker-compose ps

# === ШАГ 6: Проверьте здоровье PostgreSQL ===
Write-Host "\nПроверка PostgreSQL:" -ForegroundColor Cyan
docker exec postgres_dbcv pg_isready -U dbcv_prod -d dbcv_prod
```

---

## 📋 Проверка после исправления

### Ожидаемый результат

```
NAME                      STATUS
backend_dbcv              Up (healthy)
mcp_dbcv                  Up (healthy)
postgres_dbcv             Up (healthy)
redis_dbcv                Up (healthy)
s3_dbcv                   Up (healthy)
scheduler_dbcv            Up (healthy)
faststream-bot-1          Up
faststream-user-1         Up
cache_redis_dbcv          Up (healthy)
```

### Проверка доступности сервисов

```powershell
# Backend API
curl http://localhost:8003/health

# MCP Service  
curl http://localhost:8005/health

# MinIO Console
Start-Process "http://localhost:9002"
```

---

## 🔧 Дополнительные проблемы

### Проблема: Cache Redis unhealthy

**Причина:** Healthcheck не проходит на порту 6389

**Решение:**
```bash
# Проверить логи
docker logs cache_redis_dbcv

# Проверить порт вручную
docker exec cache_redis_dbcv redis-cli -p 6389 ping
```

### Проблема: Backend перезапускается

**Возможные причины:**
1. Не может подключиться к PostgreSQL
2. Не может подключиться к Redis
3. Ошибка в миграциях

**Проверка:**
```bash
docker logs backend_dbcv --tail 100
```

---

## 📊 Состояние интеграции Wildberries

### После исправления контейнеров

**Что будет работать:**
- ✅ Регистрация интеграции в реестре
- ✅ Тесты структуры (`minimal_wb_test.py`)
- ✅ Mock библиотека (`wildberries_api.py`)
- ✅ Dry-run режим
- ✅ Доступ к credentials из БД
- ✅ Полная интеграция с `run_wildberries_integration.py`

**Следующие шаги для Wildberries:**

1. **Добавить credentials в БД:**
   ```sql
   -- Подключитесь к БД
   docker exec -it postgres_dbcv psql -U dbcv_prod -d dbcv_prod
   
   -- Добавьте credentials
   INSERT INTO credentials (bot_id, provider, strategy, payload)
   VALUES (
       'your-bot-uuid',
       'wildberries',
       'api_key',
       '{"api_key": "your-wildberries-api-key"}'::jsonb
   );
   ```

2. **Запустить тест:**
   ```bash
   cd DBCV/backend
   python run_wildberries_test.py
   ```

3. **Запустить интеграцию:**
   ```bash
   python run_wildberries_integration.py
   ```

---

## 🎯 Итоговая команда (КОПИРУЙ И ВЫПОЛНЯЙ)

```powershell
# === ПОЛНОЕ ИСПРАВЛЕНИЕ ===

# 1. Остановить все
cd C:\Users\User\Desktop\Учеба\ПМ.1\ Произв\Репозиторий\DBCV
docker-compose down -v  # -v удалит старые volumes

# 2. Убедиться что env.prod существует
if (-not (Test-Path env.prod)) {
    Write-Host "ERROR: env.prod не найден!" -ForegroundColor Red
    exit 1
}

# 3. Переименовать в .env
if (Test-Path .env) { Remove-Item .env -Force }
Copy-Item env.prod .env

# 4. Проверить содержимое
Write-Host "Проверка .env файла:" -ForegroundColor Cyan
Get-Content .env | Select-String -Pattern "POSTGRES_PASSWORD|MINIO_ROOT"

# 5. Запустить контейнеры
Write-Host "\nЗапуск контейнеров..." -ForegroundColor Cyan
docker-compose up -d

# 6. Ждать инициализации
Write-Host "Ожидание 45 секунд..." -ForegroundColor Yellow
for ($i=45; $i -gt 0; $i--) {
    Write-Host "$i..." -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host ""

# 7. Проверить статус
Write-Host "\nСтатус контейнеров:" -ForegroundColor Cyan
docker-compose ps

# 8. Проверить здоровье
Write-Host "\nПроверка PostgreSQL:" -ForegroundColor Cyan
docker exec postgres_dbcv pg_isready -U dbcv_prod

Write-Host "\nПроверка Redis:" -ForegroundColor Cyan
docker exec redis_dbcv redis-cli ping

Write-Host "\n✅ Готово!" -ForegroundColor Green
Write-Host "Сервисы доступны:" -ForegroundColor Cyan
Write-Host "  Backend: http://localhost:8003" -ForegroundColor White
Write-Host "  MCP: http://localhost:8005" -ForegroundColor White  
Write-Host "  MinIO: http://localhost:9002" -ForegroundColor White
```

---

**Дата:** 2024  
**Статус:** 🔧 В процессе исправления  
**Приоритет:** 🔴 Критический
