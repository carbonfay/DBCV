FROM python:3.12.7-alpine

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Установка системных зависимостей
RUN apk add --no-cache \
    git \
    build-base \
    libffi-dev \
    openssl-dev \
    curl

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt /app/

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . /app/

# Установка переменной окружения для Python path
ENV PYTHONPATH=/app

# Создание пользователя для безопасности
RUN adduser -D -s /bin/sh mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# Команда по умолчанию
CMD ["python", "run_server.py"]
