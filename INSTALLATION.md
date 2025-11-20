# Инструкция по установке DBCV

Этот документ содержит подробные инструкции по установке и настройке backend и frontend для платформы DBCV.

## Содержание

1. [Требования](#требования)
2. [Backend установка](#backend-установка)
3. [Frontend установка](#frontend-установка)
4. [Проверка установки](#проверка-установки)
5. [Решение проблем](#решение-проблем)

---

## Требования

### Для Backend

- **Python**: 3.12 или выше
- **PostgreSQL**: 14 или выше
- **Redis**: 7 или выше
- **Docker и Docker Compose** (опционально, но рекомендуется)

### Для Frontend

- **Node.js**: 18 или выше
- **npm**: 9 или выше (или yarn)

### Дополнительно

- **Git** для клонирования репозитория
- **Текстовый редактор** (VS Code, PyCharm и т.д.)

---

## Backend установка

### Вариант 1: Установка через Docker (рекомендуется)

Этот вариант проще и не требует ручной настройки окружения.

#### Шаг 1: Клонировать репозиторий

```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd DBCV
```

#### Шаг 2: Настроить переменные окружения

```bash
# Скопировать пример файла окружения
cp env.example env.dev

# Отредактировать env.dev (используйте любой текстовый редактор)
# Указать необходимые переменные:
# - DATABASE_URL
# - REDIS_URL
# - S3 настройки
# - и другие
```

**Минимальные переменные для работы:**

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/dbcv
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://s3:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dbcv
```

#### Шаг 3: Запустить через Docker Compose

```bash
# Запустить все сервисы
docker-compose -f docker-compose.dev.yml up -d

# Проверить статус
docker-compose -f docker-compose.dev.yml ps
```

#### Шаг 4: Проверить логи

```bash
# Просмотр логов backend
docker-compose -f docker-compose.dev.yml logs -f backend

# Просмотр логов всех сервисов
docker-compose -f docker-compose.dev.yml logs -f
```

#### Шаг 5: Остановка сервисов

```bash
# Остановить все сервисы
docker-compose -f docker-compose.dev.yml down

# Остановить и удалить volumes (БД будет очищена)
docker-compose -f docker-compose.dev.yml down -v
```

---

### Вариант 2: Установка вручную

Этот вариант требует ручной настройки PostgreSQL и Redis.

#### Шаг 1: Клонировать репозиторий

```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd DBCV/backend
```

#### Шаг 2: Создать виртуальное окружение

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### Шаг 3: Установить зависимости

```bash
# Обновить pip
pip install --upgrade pip

# Установить основные зависимости
pip install -r requirements.txt

# Установить зависимости для интеграций (если нужно)
pip install -r requirements_integrations.txt
```

#### Шаг 4: Настроить PostgreSQL

1. Установить PostgreSQL (если еще не установлен)
2. Создать базу данных:

```sql
CREATE DATABASE dbcv;
CREATE USER dbcv_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dbcv TO dbcv_user;
```

#### Шаг 5: Настроить Redis

1. Установить Redis (если еще не установлен)
2. Запустить Redis:

```bash
# Linux/macOS
redis-server

# Windows (через WSL или установить Redis для Windows)
```

#### Шаг 6: Настроить переменные окружения

```bash
# Вернуться в корень проекта
cd ..

# Скопировать пример файла
cp env.example env.dev

# Отредактировать env.dev
```

**Минимальные переменные:**

```env
DATABASE_URL=postgresql+asyncpg://dbcv_user:your_password@localhost:5432/dbcv
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dbcv
```

#### Шаг 7: Запустить миграции

```bash
cd backend
alembic upgrade head
```

#### Шаг 8: Загрузить начальные данные

```bash
python initial_data.py
```

#### Шаг 9: Запустить сервер

```bash
python main.py
```

Сервер должен запуститься на `http://localhost:8003`

---

## Frontend установка

### Шаг 1: Перейти в директорию frontend

```bash
# Если frontend в отдельном репозитории
cd <ПУТЬ_К_FRONTEND_ПРОЕКТУ>
# Например: cd C:\Users\user\VueProjects\DBCV_Builder

# Или если frontend в том же репозитории
cd DBCV/frontend
```

### Шаг 2: Установить зависимости

```bash
# Используя npm
npm install

# Или используя yarn
yarn install
```

### Шаг 3: Настроить переменные окружения

```bash
# Создать .env файл
cp .env.example .env

# Отредактировать .env
```

**Минимальные переменные:**

```env
VITE_API_URL=http://localhost:8003
```

### Шаг 4: Запустить dev сервер

```bash
# Используя npm
npm run dev

# Или используя yarn
yarn dev
```

Сервер должен запуститься на `http://localhost:5173` (или другом порту, указанном в консоли)

### Шаг 5: Сборка для продакшена (опционально)

```bash
# Используя npm
npm run build

# Или используя yarn
yarn build
```

---

## Проверка установки

### Backend

#### 1. Проверить health endpoint

```bash
curl http://localhost:8003/health
```

Ожидаемый ответ:
```json
{"status": "ok"}
```

#### 2. Проверить API документацию

Откройте в браузере:
```
http://localhost:8003/docs
```

Должна открыться интерактивная документация Swagger.

#### 3. Проверить каталог интеграций

```bash
curl http://localhost:8003/api/integrations/catalog
```

Должен вернуться список доступных интеграций.

### Frontend

#### 1. Открыть в браузере

```
http://localhost:5173
```

Должен загрузиться интерфейс приложения.

#### 2. Проверить API запросы

1. Открыть DevTools (F12)
2. Перейти на вкладку Network
3. Выполнить какое-либо действие в интерфейсе
4. Проверить, что запросы к API выполняются успешно

#### 3. Проверить консоль на ошибки

В DevTools → Console не должно быть критических ошибок.

---

## Решение проблем

### Backend не запускается

#### Проблема: Ошибка подключения к базе данных

**Решение:**
1. Проверить, что PostgreSQL запущен
2. Проверить правильность `DATABASE_URL` в `env.dev`
3. Проверить, что база данных создана
4. Проверить права доступа пользователя

#### Проблема: Ошибка подключения к Redis

**Решение:**
1. Проверить, что Redis запущен
2. Проверить правильность `REDIS_URL` в `env.dev`
3. Проверить доступность порта 6379

#### Проблема: Ошибки миграций

**Решение:**
```bash
# Откатить миграции
alembic downgrade -1

# Применить заново
alembic upgrade head
```

#### Проблема: Модуль не найден

**Решение:**
```bash
# Убедиться, что виртуальное окружение активировано
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Переустановить зависимости
pip install -r requirements.txt
```

### Frontend не запускается

#### Проблема: Ошибки при npm install

**Решение:**
```bash
# Очистить кеш
npm cache clean --force

# Удалить node_modules и package-lock.json
rm -rf node_modules package-lock.json

# Переустановить
npm install
```

#### Проблема: Ошибки при сборке

**Решение:**
1. Проверить версию Node.js: `node --version` (должна быть >= 18)
2. Обновить зависимости: `npm update`
3. Проверить ошибки в консоли

#### Проблема: API запросы не работают

**Решение:**
1. Проверить `VITE_API_URL` в `.env`
2. Проверить, что backend запущен и доступен
3. Проверить CORS настройки на backend
4. Проверить Network вкладку в DevTools

### Docker проблемы

#### Проблема: Контейнеры не запускаются

**Решение:**
```bash
# Проверить логи
docker-compose -f docker-compose.dev.yml logs

# Пересоздать контейнеры
docker-compose -f docker-compose.dev.yml up -d --force-recreate
```

#### Проблема: Порты заняты

**Решение:**
1. Изменить порты в `docker-compose.dev.yml`
2. Или остановить процессы, использующие эти порты

---

## Дополнительная настройка

### Настройка S3/MinIO

Если используете MinIO локально:

1. MinIO должен быть доступен по адресу из `S3_ENDPOINT`
2. Создать bucket с именем из `S3_BUCKET`
3. Настроить публичный доступ (если нужно)

### Настройка переменных окружения для разработки

Рекомендуемые значения для локальной разработки:

```env
# База данных
DATABASE_URL=postgresql+asyncpg://dbcv_user:password@localhost:5432/dbcv

# Redis
REDIS_URL=redis://localhost:6379/0

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_PUBLIC_ENDPOINT=http://localhost:9000
S3_REGION=us-east-1
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=dbcv

# Приложение
DEBUG=True
LOG_LEVEL=DEBUG
```

---

## Следующие шаги

После успешной установки:

1. Изучить [STUDENT_WORKFLOW.md](./STUDENT_WORKFLOW.md) для понимания процесса работы
2. Изучить [STUDENT_AI_PROMPT.md](./STUDENT_AI_PROMPT.md) для работы с нейросетями
3. Выбрать интеграцию из [TASK_DISTRIBUTION.md](./TASK_DISTRIBUTION.md)
4. Начать реализацию!

---

**Удачи в работе!**

