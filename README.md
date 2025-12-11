# Quick start (local development)

This repository contains the backend API for the Cupid project (Django + DRF + Channels). The instructions below will get the project running locally for development.

## Prerequisites
- Python 3.8+ installed
- Poetry (dependency and virtual environment manager)
- (Optional) Docker for running Redis or PostgreSQL locally

Install Poetry (recommended):
```bash
# via official installer
curl -sSL https://install.python-poetry.org | python3 -
# or via pipx
pipx install poetry
```

Verify Poetry is available:
```bash
poetry --version
```

## Setup
1. Copy or create environment file and set required variables (.env recommended):
   - `DATABASE_URL` (Postgres URL for local or remote DB)
   - `SECRET_KEY`
   - `DEBUG=true` (for local dev)
   - `REDIS_URL` (e.g. `redis://127.0.0.1:6379/0`) — do not include surrounding quotes

2. Install dependencies:
```bash
poetry install
```

3. (Optional) Activate the Poetry virtual environment:
```bash
poetry shell
```
If you prefer not to spawn a shell, prefix commands with `poetry run`.

4. Apply database migrations:
```bash
poetry run python manage.py migrate
```

5. (Optional) Create a superuser for admin access:
```bash
poetry run python manage.py createsuperuser
```

## Running the project
- Run the Django development server (sync):
```bash
poetry run python manage.py runserver
```

- Run the ASGI app (recommended for Channels support) with Uvicorn if you want to enable chatting func:
```bash
poetry run uvicorn config.asgi:application --host 127.0.0.1 --port 8000 --reload --log-level debug
```

- Run with Daphne (alternative ASGI server):
```bash
poetry run daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

- If you use Redis for channels locally (recommended), start it with Docker (now I comment this function in settings.py):
```bash
docker run -d --name cupid-redis -p 6379:6379 redis:7-alpine
export REDIS_URL=redis://127.0.0.1:6379/0
```

## Developer utilities
- OpenAPI / docs:
  - OpenAPI JSON: http://127.0.0.1:8000/api/schema/
  - Swagger UI:     http://127.0.0.1:8000/api/docs/swagger/
  - Redoc:          http://127.0.0.1:8000/api/docs/redoc/

- WebSocket test UI: http://127.0.0.1:8000/api/chat_ws_test.html

## Notes
- Use `poetry run <command>` to execute project commands without activating the virtualenv.
- Make sure `.env` values do not include extra quotes (e.g. REDIS_URL should be redis://127.0.0.1:6379/0).
- For local development you can set `DEBUG=true` and optionally fall back to an in-memory channel layer.

---

Developer comments

1. Ensure the `users/migrations/` chain is consistent before running `migrate` — if the DB already contains tables you may need `--fake` or to reset the dev DB.
2. When testing Channels locally, either run Redis or enable the DEBUG in-memory channel layer to avoid connection issues.
3. Dockerfile is prepared for Postgres builds (psycopg2) — the image installs libpq headers; verify the production image uses multi-stage builds and pins dependencies.
4. Registration supports attaching preferences; review `users/serializers_auth.py` and `users/views_auth.py` when changing registration fields.
5. Use the API docs endpoints (drf-spectacular) to validate serializers and view schema annotations after making model or serializer changes.