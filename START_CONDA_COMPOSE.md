Краткий запуск через conda и Docker Compose
===========================================

Этот сценарий запускает backend и вспомогательные сервисы (PostgreSQL, Redis, MinIO, FastStream, MCP) из готовых Docker-образов/сборок. Делайте шаги последовательно — после них приложение доступно на `http://localhost:8003`.

Что нужно установить заранее
- Docker + Docker Compose plugin.
- Miniconda/Anaconda.
- Свободные порты: 8003, 8005, 9000, 9002, 5433, 6379, 6389.

Шаги
1) Перейдите в корень проекта:
   ```bash
   cd /Users/sbiktimirov/Documents/MTI/prodaction_practic/dbcv_backend
   ```

2) Создайте conda-окружение и активируйте его (нужно для локальных CLI-утилит, миграций и управления зависимостями):
   ```bash
   conda env create -f environment.yml
   conda activate DBCV
   ```

3) Подготовьте переменные окружения (используются контейнерами):
   ```bash
   cp env.example env.prod
   ```
   Минимум заполните:
   - `OPENAI_API_KEY` — ключ OpenAI.
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — при необходимости измените, значения по умолчанию уже согласованы с Compose.
   - `S3_ENDPOINT`, `S3_PUBLIC_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` — оставьте дефолты, если запускаете локально.
   - `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD` — логин/пароль администратора.

4) Запустите все сервисы (сборка локальных образов backend/faststream/mcp и загрузка готовых образов зависимостей из Docker Hub):
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```

5) Убедитесь, что контейнеры поднялись:
   ```bash
   docker compose -f docker-compose.yml ps
   ```
   Backend будет доступен после прохождения healthcheck на `http://localhost:8003/health`. MCP — `http://localhost:8005/health`. MinIO — `http://localhost:9000` (консоль `http://localhost:9002`).

6) Остановить/очистить (при необходимости):
   ```bash
   docker compose -f docker-compose.yml down        # просто остановить
   docker compose -f docker-compose.yml down -v     # остановить и удалить данные (в т.ч. БД/MinIO)
   ```

Примечания
- Используемый файл Compose: `docker-compose.yml` в корне `dbcv_backend` (уже в репозитории).
- Для разработки с hot-reload можно использовать `docker-compose.dev.yml` с монтированием кода (`env.dev` вместо `env.prod`).
- Если нужно обновить зависимости без пересоздания окружения: `conda activate DBCV && pip install -r backend/requirements.txt`.
