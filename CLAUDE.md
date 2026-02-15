# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Solo on Keyboard — a touch typing tutor backend API built with Django 6.0.2 and Django REST Framework. Features Telegram bot OTP authentication, JWT sessions, subscription-based lesson access, and Via payment gateway integration.

## Development Commands

All commands use the Makefile. Environment variables must be set first (see Environment Setup below).

```bash
# Start PostgreSQL (Docker)
make up-d

# Install dev dependencies (creates .venv automatically)
make install-dev

# Run migrations and start server
make migrate && make runserver

# Run tests (uses pytest with config.settings.test)
pytest tests/

# Run a single test file or test
pytest tests/keypro/test_views.py
pytest tests/keypro/test_views.py::TestLessonDetailView::test_free_lesson_accessible

# Linting and formatting
make lint          # check
make lint-fix      # auto-fix
make format        # format
make format-check  # check only

# Generate migrations after model changes
make makemigrations
```

## Environment Setup

Source the env file before running any make commands:

```bash
source deployments/development/env
```

**Caveat:** The `ENV_DJANGO_SECRET_KEY` line in that file uses a Django subshell that fails outside the venv. If it errors, set it manually:

```bash
export ENV_DJANGO_SECRET_KEY="test-secret-key"
```

## Architecture

### Django Apps (all under `src/`)

- **accounts** — Custom `User` model (email-based, Telegram-linked), `AuthCode` for OTP, JWT token endpoints, user profile
- **keypro** — `Course`, `Lesson`, `CourseEnrollment`, `CompletedLesson`. Lessons have `is_free` flag; paid lessons require active subscription
- **payments** — `SubscriptionPlan`, `Subscription`, `PaymentAttempt` (state machine: INITIATED → PENDING → SUCCESS/FAILED). Via payment gateway client at `payments/clients/via/client.py`
- **config** — Settings (base/development/staging/production/test), URL routing, WSGI/ASGI

### URL Structure

```
/admin/                          → Django admin
/api/auth/token/                 → OTP → JWT exchange
/api/auth/token/refresh/         → Refresh JWT
/api/auth/my/profile/            → User profile (GET, PATCH)
/api/auth/my/subscription/       → Active subscription
/api/auth/my/enrolled-courses/   → Enrolled courses
/api/courses/                    → List courses
/api/courses/<slug>/lessons/     → List lessons
/api/courses/<slug>/lessons/<id>/ → Lesson detail (permission-gated)
/api/subscription-plans/         → List plans
/api/subscription/pay/initiate/  → Start card payment
/api/subscription/pay/verify/    → Verify SMS code
/api/subscription/pay/resend-code/ → Resend SMS
```

### Authentication Flow

1. User interacts with Telegram bot → system generates 12-digit OTP (`AuthCode`)
2. Client sends OTP to `POST /api/auth/token/` → receives JWT access (5h) + refresh (1d) tokens
3. `HasLessonAccess` permission: free lessons are public, paid lessons require valid `Subscription`

### Settings Hierarchy

`config.settings.base` → extended by `development` / `staging` / `production` / `test`. Each environment has its own requirements file in `requirements/`.

## Code Style

- **Ruff** for linting + formatting (configured in `pyproject.toml`)
- Line length: 80 chars, double quotes, space indent
- Lint rules: E, W, F, I, B, UP, SIM, C4, DJ
- Pre-commit hooks enforce Ruff on every commit
- First-party imports: `accounts`, `payments`, `keypro`, `config`

## Testing

- pytest with `pytest-django`, settings: `config.settings.test`, pythonpath: `src`, testpaths: `tests`
- Shared fixtures in `tests/conftest.py`: `api_client`, `user`, `auth_client` (authenticated)
- Per-app fixtures in `tests/<app>/conftest.py`
- CI runs lint + test jobs on all non-main branches (GitHub Actions)

## Deployment

- **Heroku** for staging/production (Procfile: gunicorn, collectstatic + migrate on release)
- Staging: WhiteNoise static files, Sentry, Swagger enabled
- Production: AWS S3 for static/media, Sentry, CORS restricted to skillup.uz
