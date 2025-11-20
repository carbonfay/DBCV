#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Postgres еще не запущен..."

    # Проверяем доступность хоста и порта
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "Postgres запущен"
fi


echo "Making migrations and migrating the database. "

alembic revision --autogenerate
alembic upgrade head
python initial_data.py
python main.py

exec "$@"