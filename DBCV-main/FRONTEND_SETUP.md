# Инструкция по установке и запуску Frontend (DBCV_Builder)

## Клонирование репозитория

```bash
git clone https://github.com/carbonfay/DBCV_Builder.git
cd DBCV_Builder
git checkout dev_build
```

---

## Вариант 1: Запуск через Docker (рекомендуется)

### Установка Docker

Если Docker еще не установлен:

1. **Скачайте Docker Desktop** с официального сайта: https://www.docker.com/products/docker-desktop/
2. Выберите версию для вашей ОС (Windows, macOS или Linux)
3. Установите Docker Desktop
4. Запустите Docker Desktop
5. Проверьте установку:

```bash
docker --version
docker-compose --version
```

**Важно:** Docker Desktop должен быть запущен перед использованием команд `docker-compose`.

### Запуск

```bash
docker-compose -f docker-compose.dev.yml up --build
```

После запуска фронтенд будет доступен по адресу: http://localhost:5173

### Остановка

Нажмите `Ctrl+C` в терминале или выполните:

```bash
docker-compose -f docker-compose.dev.yml down
```

### Запуск в фоновом режиме

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

Просмотр логов:

```bash
docker-compose -f docker-compose.dev.yml logs -f
```

---

## Вариант 2: Запуск без Docker

### Требования

- **Node.js 18 или выше** (npm устанавливается автоматически вместе с Node.js)
- **npm 9 или выше** (или yarn)

### Установка Node.js

Если Node.js еще не установлен:

1. Скачайте Node.js с официального сайта: https://nodejs.org/
2. Выберите LTS версию (рекомендуется)
3. Установите Node.js (npm установится автоматически)
4. Проверьте установку:

```bash
node --version
npm --version
```

### Установка зависимостей

```bash
npm install
```

или

```bash
yarn install
```

### Запуск

```bash
npm run dev
```

или

```bash
yarn dev
```

После запуска фронтенд будет доступен по адресу: http://localhost:3000

### Остановка

Нажмите `Ctrl+C` в терминале.

