# Solo on Keyboard

Touch typing tutor web application backend API.

## Tech Stack

- **Language & Framework:** Python 3.12, Django 6.0.2, Django REST Framework
- **Database:** PostgreSQL 18.2 (Docker)
- **Auth:** JWT via SimpleJWT
- **Sign-in:** Telegram Bot (OTP)
- **Payments:** Via payment gateway
- **Code Quality:** Ruff (linting & formatting)
- **API Docs:** Swagger (drf-yasg) in development

## Features (Planned)

- Multiple keyboard layouts (US QWERTY, Cyrillic, etc.)
- 100 sections per lesson, first 10 free
- WPM, accuracy, and error key tracking
- Voucher system (1 / 3 / 12 month plans)
- Telegram bot OTP authentication

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Make

## Getting Started

```bash
# Clone the repository
git clone <repo-url> && cd solo-on-keyboard

# Copy environment variables
cp deployments/development/env src/.env

# Start Docker services (PostgreSQL, Redis, etc.)
make up-d

# Create venv and install dev dependencies
make install-dev

# Run database migrations
make migrate

# (Optional) Load fixture data
make loaddata

# Start the dev server
make runserver
```

The API is available at `http://localhost:8000`.
Swagger docs at `http://localhost:8000/swagger/`, ReDoc at `http://localhost:8000/redoc/`.

## Makefile Commands

### Docker

| Command | Description |
|---------|-------------|
| `make up` | Start all Docker services (foreground) |
| `make up-d` | Start all Docker services (detached) |
| `make down` | Stop all Docker services |
| `make start SERVICE=<name>` | Start a specific service |
| `make stop SERVICE=<name>` | Stop a specific service |
| `make restart SERVICE=<name>` | Restart a specific service |
| `make logs SERVICE=<name>` | Tail logs for a service |
| `make exec SERVICE=<name> COMMAND=<cmd>` | Exec into a running service |
| `make build SERVICE=<name>` | Build/rebuild a service |
| `make shell` | Open Django `shell_plus` in the API container |

### Django

| Command | Description |
|---------|-------------|
| `make install-dev` | Create venv & install dev requirements |
| `make install` | Create venv & install base requirements |
| `make runserver` | Run the Django dev server |
| `make createsuperuser` | Create a Django superuser |
| `make makemigrations` | Generate new migrations |
| `make migrate` | Apply migrations |
| `make loaddata` | Load all JSON fixtures |
| `make seed` | Seed database with fake data |

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Lint all files |
| `make lint-fix` | Auto-fix lint errors |
| `make format` | Format code |
| `make format-check` | Check formatting (no changes) |
| `make pre-commit-install` | Install pre-commit git hooks |
| `make pre-commit-all` | Run all pre-commit hooks on every file |

## Code Quality Setup

The project uses **Ruff** for linting and formatting, enforced via **pre-commit** on every commit.

```bash
# One-time: install pre-commit hooks into your local repo
make pre-commit-install

# Run hooks on all files (useful after initial setup or CI)
make pre-commit-all

# Manual usage
make lint          # check for lint errors
make lint-fix      # auto-fix lint errors
make format        # format all files
make format-check  # check formatting without changes
```

Configuration lives in `pyproject.toml` (Ruff) and `.pre-commit-config.yaml` (hooks).

## Project Structure

```
solo-on-keyboard/
├── deployments/           # Docker Compose & env files per environment
│   └── development/
│       ├── docker-compose.yml
│       └── env
├── doc/                   # Documentation
│   └── implementation-plan.md
├── requirements/          # Pip requirements per environment
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   ├── staging.txt
│   └── test.txt
├── src/                   # Django project root
│   ├── config/            # Settings, URLs, WSGI/ASGI
│   │   ├── settings/
│   │   └── urls/
│   ├── accounts/          # User model, auth, serializers
│   ├── payments/          # Plans, vouchers, subscriptions
│   └── typemaster/        # Layouts, lessons, sections, sessions
├── tests/                 # Test suite
├── Makefile
└── requirements.txt
```

## API Endpoints (Planned)

### Auth — Telegram OTP

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/telegram/otp/request/` | Request OTP via Telegram |
| POST | `/auth/telegram/otp/verify/` | Verify OTP and get JWT |
| POST | `/auth/token/refresh/` | Refresh JWT access token |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plans/` | List subscription plans |
| POST | `/api/vouchers/apply/` | Apply a voucher code |
| GET | `/api/subscription/` | Current user subscription |

### Typemaster

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/layouts/` | List keyboard layouts |
| GET | `/api/lessons/` | List lessons for a layout |
| GET | `/api/sections/` | List sections in a lesson |
| POST | `/api/sessions/` | Start a typing session |
| PUT | `/api/sessions/:id/` | Submit session results |
| GET | `/api/progress/` | User progress per lesson |
| GET | `/api/stats/` | WPM, accuracy, error keys |

> Endpoints are planned and subject to change as views are implemented.

## Environment Variables

Defined in `deployments/development/env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SETTINGS_MODULE` | Settings module path | `config.settings.development` |
| `ENV_DJANGO_SECRET_KEY` | Django secret key | Auto-generated |
| `ENV_POSTGRES_DB_NAME` | Database name | `ttm` |
| `ENV_POSTGRES_DB_HOST` | Database host | `localhost` |
| `ENV_POSTGRES_DB_PORT` | Database port | `15432` |
| `ENV_POSTGRES_DB_USER` | Database user | `ttmadmin` |
| `ENV_POSTGRES_DB_PASSWORD` | Database password | `password` |
| `ENV_POSTGRES_DB_CONN_MAX_AGE` | DB connection max age | `0` |
| `ENV_REDIS_PORT` | Redis port | `6379` |
| `ENV_CELERY_BROKER_URL` | Celery broker URL | `redis://127.0.0.1:6379/0` |
| `ENV_EMAIL_HOST` | Email host | `127.0.0.1` |
| `ENV_EMAIL_SMTP_PORT` | SMTP port | `1025` |
| `ENV_EMAIL_WEBUI_PORT` | MailHog web UI port | `8025` |
