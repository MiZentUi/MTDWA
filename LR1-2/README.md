# Realty

Краткая процедура запуска проекта.

## Запуск через Docker

1. Скопируйте пример переменных окружения:

```bash
cp .env.example .env
```

2. При необходимости измените значения в `.env`.

3. Соберите и запустите контейнеры:

```bash
docker compose up --build
```

При старте приложение дождется PostgreSQL, применит миграции, загрузит демо-данные и запустит сервер. Сайт будет доступен по адресу `http://127.0.0.1/`.

Демо-пользователи после загрузки данных:

- `admin` / `Admin12345!`
- `agent1`, `agent2` / `Agent12345!`
- `client1`, `client2` / `Client12345!`

## Локальный запуск

1. Создайте и активируйте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Примените миграции и загрузите демо-данные:

```bash
python realty/manage.py migrate
python realty/manage.py seed_demo
```

4. Запустите сервер разработки:

```bash
python realty/manage.py runserver
```

Сайт будет доступен по адресу `http://127.0.0.1:8000/`.

## Проверка

```bash
python realty/manage.py test agency
```
