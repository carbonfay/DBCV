Локальный запуск backend
========================

**Требования:** Docker, Miniconda/Anaconda

**Шаги:**

1. Подготовить окружение:
   ```bash
   conda env create -f environment.yml
   conda activate DBCV
   ```

2. Создать `env.dev` (скопировать из `env.example` и настроить):
   ```bash
   cp env.example env.dev
   ```
   Убедитесь, что в `env.dev` указаны правильные значения для локальных сервисов:
   - `DATABASE_URL=postgresql+asyncpg://dbcv_test:dbcv_test@localhost:5433/dbcv_test`
   - `REDIS_URL=redis://localhost:6379/0`
   - `CACHE_REDIS_URL=redis://localhost:6389/0`
   - `S3_ENDPOINT=http://localhost:9000`

3. Запустить зависимости в Docker:
   ```bash
   docker compose -f docker-compose.deps.yml up -d
   ```

4. Применить миграции:
   ```bash
   cd backend/app
   alembic upgrade head
   python initial_data.py
   ```

5. Запустить backend:
   ```bash
   cd backend/app
   uvicorn main:app --host 0.0.0.0 --port 8003 --reload
   ```
   
   Или без активации conda:
   ```bash
   cd backend/app
   conda run -n DBCV uvicorn main:app --host 0.0.0.0 --port 8003 --reload
   ```

**Проверка:** `curl http://localhost:8003/health`

**Остановка:**
- Backend: `Ctrl+C` или `lsof -ti:8003 | xargs kill -9`
- Docker: `docker compose -f docker-compose.deps.yml down`

**Примечание:** Приложение автоматически загружает `env.dev` и настраивает `PYTHONPATH`.
