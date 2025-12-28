# 🚀 Production Setup Guide

## Быстрая настройка production окружения для DBCV

---

## 📋 Текущая ситуация

### Проблемы с контейнерами:

- ❌ **PostgreSQL** - не может запуститься (нет паролей)
- ❌ **Backend** - ждет PostgreSQL
- ❌ **MCP Server** - ждет PostgreSQL
- ❌ **Scheduler** - ждет PostgreSQL
- ⚠️ **Cache Redis** - unhealthy
- ✅ **S3/MinIO** - работает
- ✅ **Redis** - работает

### Причина:

**Отсутствует файл `env.prod`** с корректными переменными окружения!

---

## ✅ Решение (3 шага)

### Шаг 1: Генерация безопасных ключей

```bash
# Перейдите в директорию проекта
cd DBCV

# Запустите генератор ключей
python generate_secure_env.py
```

**Что произойдет:**
- ✅ Создастся резервная копия текущего env.prod
- ✅ Сгенерируются безопасные случайные ключи
- ✅ Обновится файл env.prod
- ✅ Создастся файл PRODUCTION_CREDENTIALS.txt с паролями

**Важно:**
1. Скопируйте credentials из PRODUCTION_CREDENTIALS.txt
2. Сохраните в password manager
3. **УДАЛИТЕ** файл PRODUCTION_CREDENTIALS.txt

---

### Шаг 2: Проверка конфигурации

```bash
# Проверьте что env.prod создан и заполнен
cat env.prod | grep -v "^#" | grep -v "^$"

# Убедитесь что нет placeholder'ов
cat env.prod | grep "CHANGE_"
# Вывод должен быть пустым!
```

---

### Шаг 3: Запуск контейнеров

```bash
# Остановите старые контейнеры (если запущены)
docker-compose down

# Удалите старые volumes (ВНИМАНИЕ: удалятся данные!)
# Используйте только при первом запуске
docker-compose down -v

# Запустите контейнеры
docker-compose up -d

# Проверьте статус
docker-compose ps

# Проверьте логи
docker-compose logs -f
```

---

## 🔍 Проверка после запуска

### 1. Проверка контейнеров

```bash
# Все контейнеры должны быть healthy или running
docker-compose ps

# Ожидаемый результат:
# backend_dbcv          Up (healthy)
# postgres_dbcv         Up (healthy)
# redis_dbcv            Up (healthy)
# cache_redis_dbcv      Up (healthy)
# s3_dbcv               Up (healthy)
# mcp_dbcv              Up (healthy)
# scheduler_dbcv        Up
# faststream-bot-1      Up
# faststream-user-1     Up
```

### 2. Проверка логов

```bash
# PostgreSQL должен успешно стартовать
docker logs postgres_dbcv | grep "database system is ready"

# Backend должен подключиться к БД
docker logs backend_dbcv | grep -i "connected\|success\|started"

# Нет критических ошибок
docker-compose logs | grep -i "error\|critical\|fatal" | tail -20
```

### 3. Проверка здоровья сервисов

```bash
# Backend health
curl http://localhost:8003/health
# Ожидается: {"status":"ok"}

# MCP Server health
curl http://localhost:8005/health
# Ожидается: {"status":"healthy"}

# MinIO health
curl http://localhost:9000/minio/health/live
# Ожидается: успешный ответ
```

---

## 🔐 Безопасность

### Сгенерированные credentials:

| Сервис | Параметр | Где использовать |
|--------|----------|------------------|
| **PostgreSQL** | POSTGRES_PASSWORD | Подключение к БД |
| **MinIO** | MINIO_ROOT_USER/PASSWORD | S3 консоль (port 9002) |
| **Admin** | FIRST_SUPERUSER_PASSWORD | Первый вход в систему |
| **App** | SECRET_KEY | Внутренние операции |
| **App** | SECRET_BOX_KEY | Шифрование данных |

### Важные файлы:

```
DBCV/
├── env.prod                          # ⚠️ НЕ коммитить в git!
├── env.prod.backup.YYYYMMDD_HHMMSS   # Резервная копия
├── PRODUCTION_CREDENTIALS.txt        # ⚠️ УДАЛИТЬ после копирования!
└── generate_secure_env.py            # Можно коммитить
```

### Чек-лист безопасности:

- [ ] env.prod добавлен в .gitignore
- [ ] PRODUCTION_CREDENTIALS.txt удален
- [ ] Пароли сохранены в password manager
- [ ] SECRET_KEY изменен (не default)
- [ ] SECRET_BOX_KEY изменен (не default)
- [ ] POSTGRES_PASSWORD изменен (не default)
- [ ] MINIO пароли изменены (не minioadmin)
- [ ] FIRST_SUPERUSER_PASSWORD изменен (не default)

---

## 🧪 Тестирование Wildberries Integration

### После запуска контейнеров:

```bash
# 1. Войдите в backend контейнер
docker exec -it backend_dbcv bash

# 2. Запустите тест регистрации
python run_wildberries_test.py

# 3. Добавьте credentials в БД (внутри контейнера)
psql postgresql://dbcv_prod:YOUR_PASSWORD@postgres:5433/dbcv_prod <<EOF
INSERT INTO credentials (bot_id, provider, strategy, payload)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'wildberries',
    'api_key',
    '{"api_key": "test-key-for-development"}'::jsonb
);
EOF

# 4. Запустите dry-run интеграцию
WB_DRY_RUN=true python run_wildberries_integration.py

# 5. Выйдите из контейнера
exit
```

### Из хост-системы (без входа в контейнер):

```bash
# Тест регистрации
docker exec backend_dbcv python run_wildberries_test.py

# Dry-run интеграция
docker exec -e WB_DRY_RUN=true backend_dbcv python run_wildberries_integration.py
```

---

## 🐛 Troubleshooting

### Проблема: PostgreSQL не стартует

```bash
# Проверьте логи
docker logs postgres_dbcv --tail 50

# Проверьте переменные окружения
docker exec postgres_dbcv env | grep POSTGRES

# Если нужно - пересоздайте volume
docker-compose down -v
docker-compose up -d
```

### Проблема: Backend не может подключиться к БД

```bash
# Проверьте что PostgreSQL здоров
docker exec postgres_dbcv pg_isready -U dbcv_prod -h localhost -p 5433

# Проверьте DATABASE_URL в backend
docker exec backend_dbcv env | grep DATABASE_URL

# Проверьте логи backend
docker logs backend_dbcv --tail 100
```

### Проблема: Cache Redis unhealthy

```bash
# Проверьте статус
docker exec cache_redis_dbcv redis-cli -p 6389 ping
# Должен вернуть: PONG

# Проверьте логи
docker logs cache_redis_dbcv

# Перезапустите если нужно
docker-compose restart cache-redis
```

### Проблема: MinIO не доступен

```bash
# Проверьте что контейнер запущен
docker ps | grep s3_dbcv

# Проверьте health
docker exec s3_dbcv curl -f http://localhost:9000/minio/health/live

# Проверьте что bucket создан
docker exec s3_dbcv mc ls local/dbcv-media
```

---

## 📊 Мониторинг

### Полезные команды:

```bash
# Статус всех контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend

# Последние N строк логов
docker-compose logs --tail=100 backend
```

### Health checks:

```bash
# Все health checks
docker inspect backend_dbcv | grep -A 10 Health
docker inspect postgres_dbcv | grep -A 10 Health
docker inspect redis_dbcv | grep -A 10 Health
```

---

## 🔄 Обновление и рестарт

### Рестарт одного сервиса:

```bash
docker-compose restart backend
```

### Рестарт всех сервисов:

```bash
docker-compose restart
```

### Пересборка после изменений кода:

```bash
# Пересобрать и перезапустить
docker-compose up -d --build

# Только конкретный сервис
docker-compose up -d --build backend
```

### Полная перезагрузка:

```bash
# Остановить
docker-compose down

# Пересобрать
docker-compose build --no-cache

# Запустить
docker-compose up -d
```

---

## 📝 Следующие шаги после успешного запуска

1. ✅ **Создайте администратора:**
   - Логин: `admin`
   - Пароль: из PRODUCTION_CREDENTIALS.txt

2. ✅ **Настройте Wildberries интеграцию:**
   - См. `backend/README_WILDBERRIES.md`
   - Добавьте реальные credentials
   - Протестируйте dry-run

3. ✅ **Настройте мониторинг:**
   - Prometheus (опционально)
   - Grafana (опционально)
   - Логирование в файлы

4. ✅ **Настройте бэкапы:**
   - PostgreSQL
   - MinIO/S3 данные
   - Конфигурация

5. ✅ **Документируйте:**
   - Ваши специфические настройки
   - Процедуры деплоя
   - Контакты команды

---

## 🎯 Чек-лист готовности к production

### Инфраструктура:

- [ ] Все контейнеры healthy
- [ ] PostgreSQL доступен
- [ ] Redis работает
- [ ] MinIO/S3 работает
- [ ] Backend отвечает на /health
- [ ] MCP Server отвечает на /health

### Безопасность:

- [ ] Все пароли изменены
- [ ] env.prod не в git
- [ ] PRODUCTION_CREDENTIALS.txt удален
- [ ] Пароли в password manager
- [ ] HTTPS настроен (если production)

### Wildberries Integration:

- [ ] Mock библиотека работает
- [ ] Тесты проходят
- [ ] Credentials в БД
- [ ] Dry-run работает
- [ ] Документация изучена

### Мониторинг:

- [ ] Логи настроены
- [ ] Health checks работают
- [ ] Алерты настроены (опционально)
- [ ] Метрики собираются (опционально)

---

**Версия:** 1.0.0  
**Дата:** 2024  
**Статус:** ✅ Ready to use

**Успешного запуска! 🚀**
