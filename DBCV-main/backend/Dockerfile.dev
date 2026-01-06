FROM python:3.12.7-alpine
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN mkdir -p /backend
RUN apk add --no-cache git
# Проверяем версию git
RUN git --version

# Добавляем git в PATH
ENV PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
WORKDIR /backend
COPY requirements.txt /backend/
RUN pip install -r requirements.txt

COPY . .
WORKDIR /backend/app
ENV PYTHONPATH /backend
EXPOSE 8003
