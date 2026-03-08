# Solo on Keyboard — Project Documentation

## Overview

Solo on Keyboard is a **touch typing tutor backend API** built with **Django 6.0.2** and **Django REST Framework**. It provides course-based typing lessons with:

- **Telegram bot OTP authentication** (12-digit one-time passwords)
- **JWT sessions** (5-hour access / 1-day refresh tokens)
- **Subscription-based paid lesson access**
- **Via payment gateway integration** (card + SMS verification)

Production domain: **skillup.uz**

---

## Architecture

### Django Apps (all under `src/`)

| App | Purpose |
|-----|---------|
| **accounts** | Custom User model (email-based, Telegram-linked), OTP auth codes, JWT token endpoints, user profile |
| **keypro** | Courses, Lessons, Assignments, enrollment tracking, completed assignments |
| **payments** | Subscription plans, Subscriptions, PaymentAttempt state machine, Via payment gateway client |
| **config** | Settings (base/dev/staging/prod/test), URL routing, WSGI/ASGI |

---

## Data Models

### accounts.User
Custom user model (`AbstractBaseUser` + `PermissionsMixin`), email-based auth.

| Field | Type | Notes |
|-------|------|-------|
| `guid` | UUID | Unique, immutable |
| `email` | EmailField | Unique, used as USERNAME_FIELD |
| `first_name`, `last_name` | CharField | |
| `telegram_chat_id` | BigIntegerField | Nullable, unique |
| `telegram_username` | CharField | Nullable, unique |
| `phone_number` | PhoneNumberField | Via `django-phonenumber-field` |
| `nickname`, `display_name` | CharField | |
| `search_vector` | SearchVectorField | PostgreSQL full-text search, GIN indexed |
| `is_staff`, `is_active` | BooleanField | |
| `terms_and_service_signed_at` | DateTimeField | Nullable |
| `date_joined` | DateTimeField | auto_now_add |

### accounts.AuthCode
One-time password for Telegram-based login.

| Field | Type | Notes |
|-------|------|-------|
| `user` | OneToOneField → User | CASCADE |
| `code` | CharField | Unique, 12-digit OTP |
| `expires_at` | DateTimeField | Default: 1 minute from creation |
| `created_at` | DateTimeField | auto_now_add |

### keypro.Course

| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField | |
| `slug` | SlugField | Unique |
| `description` | TextField | Blank allowed |
| `cover_image` | ImageField | Uploads to `courses/` |
| `author` | ForeignKey → User | SET_NULL, nullable |
| `is_active` | BooleanField | Default True |
| `order` | PositiveIntegerField | Used for ordering |

### keypro.Lesson
Intermediate level between Course and Assignment.

| Field | Type | Notes |
|-------|------|-------|
| `course` | ForeignKey → Course | CASCADE, related_name="lessons" |
| `title` | CharField | |
| `description` | TextField | Blank allowed |
| `order` | PositiveIntegerField | Unique together with course |
| `is_free` | BooleanField | Default False — controls access |
| `is_active` | BooleanField | Default True |

### keypro.Assignment
Practice exercises within a lesson.

| Field | Type | Notes |
|-------|------|-------|
| `lesson` | ForeignKey → Lesson | CASCADE, related_name="assignments" |
| `title` | CharField | |
| `description` | TextField | |
| `order` | PositiveIntegerField | Unique together with lesson |
| `text_content` | TextField | The actual typing exercise text |
| `is_active` | BooleanField | Default True |

### keypro.CourseEnrollment
Status lifecycle: `active → paused → canceled` (with resume back to `active`), `completed` is terminal.

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey → User | CASCADE |
| `course` | ForeignKey → Course | CASCADE |
| `status` | CharField | `active` / `completed` / `paused` / `canceled`. Default: `active` |
| `enrolled_at` | DateTimeField | auto_now_add |
| `completed_at` | DateTimeField | Nullable, set when status becomes `completed` |
| `last_activity_at` | DateTimeField | Default: `timezone.now`, updated on enroll/resume |

Constraint: unique_together `(user, course)`. Ordered by `-enrolled_at`.

### keypro.CompletedAssignment
One completion per (user, assignment) pair — enforced by UniqueConstraint.

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey → User | CASCADE |
| `assignment` | ForeignKey → Assignment | CASCADE |
| `action_type` | CharField | Choices: `complete`. Default: `complete` |
| `average_speed` | PositiveIntegerField | Average typing speed (chars/min). Default 0 |
| `mistakes_count` | PositiveIntegerField | Default 0 |
| `completed_at` | DateTimeField | Default: `timezone.now` (updatable on re-submission) |

### payments.SubscriptionPlan

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField | e.g., "Monthly", "3-Month" |
| `duration_days` | PositiveIntegerField | |
| `price` | DecimalField(10,2) | |
| `is_active` | BooleanField | Default True |

### payments.Subscription

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey → User | CASCADE |
| `plan` | ForeignKey → SubscriptionPlan | PROTECT |
| `starts_at` | DateTimeField | |
| `expires_at` | DateTimeField | |
| Property: `is_active` | | `starts_at <= now <= expires_at` |

### payments.PaymentAttempt
State machine: `INITIATED → PENDING → SUCCESS / FAILED`

| Field | Type | Notes |
|-------|------|-------|
| `guid` | UUIDField | Unique, external payment reference |
| `user` | ForeignKey → User | CASCADE |
| `plan` | ForeignKey → SubscriptionPlan | PROTECT |
| `status` | CharField | initiated / pending / success / failed |
| `verification_id` | CharField | Via's verify ID for SMS step |
| `amount` | DecimalField(12,2) | |

---

## Entity Relationship Hierarchy

```
User
 ├── AuthCode (1:1)
 ├── CourseEnrollment → Course
 ├── CompletedAssignment → Assignment
 ├── Subscription → SubscriptionPlan
 └── PaymentAttempt → SubscriptionPlan

Course
 └── Lesson (ordered, is_free flag)
      └── Assignment (ordered, text_content)
```

---

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/token/` | Public | Exchange OTP for JWT tokens. Returns `access_token`, `refresh_token`, `is_new_user`, user info |
| `POST` | `/api/auth/token/refresh/` | Public | Refresh JWT access token |
| `GET` | `/api/auth/my/profile/` | JWT | Get current user profile |
| `PATCH` | `/api/auth/my/profile/` | JWT | Update profile (first_name, last_name, nickname, display_name) |
| `GET` | `/api/auth/my/subscription/` | JWT | Get active subscription or `null` |
| `GET` | `/api/auth/my/enrolled-courses/` | JWT | List enrolled courses with progress (paginated, 10/page) |

### Courses & Lessons (`/api/courses/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/courses/` | Public | List active courses with `total_lessons` count |
| `GET` | `/api/courses/<slug>/lessons/` | Public | List active lessons in a course |
| `GET` | `/api/courses/<slug>/lessons/<id>/` | Optional JWT | Lesson detail with embedded assignments. Free = public; paid = requires active subscription |

### Enrollments (`/api/enrollments/`, `/api/courses/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/enrollments/` | JWT | List user's enrollments with progress (paginated) |
| `GET` | `/api/enrollments/<id>/` | JWT | Enrollment detail with progress_percent, current_lesson_id |
| `POST` | `/api/courses/<slug>/enroll/` | JWT | Enroll in a course (idempotent — reactivates canceled/paused). 201 if new, 200 if existing |
| `GET` | `/api/courses/<slug>/enrollment/` | JWT | Get enrollment by course slug. 404 if not enrolled |
| `POST` | `/api/enrollments/<id>/cancel/` | JWT | Cancel enrollment (from active/paused). 400 if already canceled/completed |
| `POST` | `/api/enrollments/<id>/resume/` | JWT | Resume enrollment (from canceled/paused). 400 if already active/completed |

### Assignment Completion & Lesson Progress (`/api/courses/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/courses/<slug>/lessons/<id>/assignments/<id>/completion/` | JWT | Complete an assignment (idempotent). 201 if new, 200 if updated. Requires active enrollment + subscription for paid lessons. Returns completion data + lesson_progress |
| `GET` | `/api/courses/<slug>/lessons/<id>/assignments/<id>/completion/` | JWT | Get existing completion for an assignment. 404 if not completed |
| `GET` | `/api/courses/<slug>/lessons/<id>/progress/` | JWT | Get lesson progress (completed/total assignments, percent, status). Requires any enrollment |

### Subscription Plans (`/api/subscription-plans/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/subscription-plans/` | Public | List active subscription plans |

### Payment (`/api/subscription/pay/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/subscription/pay/initiate/` | JWT | Step 1: Submit card details (pan, expiry) + plan_id. Returns `verifyId` + masked phone |
| `POST` | `/api/subscription/pay/verify/` | JWT | Step 2: Submit SMS verification code. On success, creates Subscription |
| `POST` | `/api/subscription/pay/resend-code/` | JWT | Resend SMS verification code |

### Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `*` | `/admin/` | Staff | Django admin panel |

---

## Authentication Flow

```
┌─────────────┐    /start or /login    ┌─────────────────┐
│  Telegram    │ ──────────────────►   │  Telegram Bot    │
│  User        │                       │  Webhook         │
│              │ ◄──────────────────   │  (Django View)   │
│              │   "Share your phone"  │                  │
│              │                       └────────┬────────┘
│              │   Shares contact                │
│              │ ──────────────────►             │
│              │                       Creates/links User
│              │ ◄──────────────────   Generates 12-digit OTP
│              │   "Your code: XXXX"   (1 min expiry)
└──────┬──────┘
       │
       │  OTP code
       ▼
┌─────────────┐  POST /api/auth/token/  ┌─────────────────┐
│  Client App  │ ──────────────────►    │  TokenObtainView │
│              │                        │                  │
│              │ ◄──────────────────    │  Validates OTP   │
│              │  {access, refresh,     │  Deletes AuthCode│
│              │   is_new_user, ...}    │  Issues JWT      │
└─────────────┘                        └─────────────────┘
```

## Payment Flow

```
Step 1: Initiate
┌────────┐  POST /pay/initiate/   ┌───────────┐   initiate_payment()   ┌───────────┐
│ Client │ ────────────────────►  │  Django   │ ────────────────────►  │  Via API  │
│        │  {plan_id, card_pan,   │           │                        │           │
│        │   expiry_month/year}   │  Creates  │ ◄────────────────────  │  Returns  │
│        │                        │  Payment  │  {verifyId, phone}     │  verifyId │
│        │ ◄────────────────────  │  Attempt  │                        │           │
│        │  {verifyId, phone}     │ (PENDING) │                        │           │
└────────┘                        └───────────┘                        └───────────┘

Step 2: Verify SMS
┌────────┐  POST /pay/verify/     ┌───────────┐   verify_payment()     ┌───────────┐
│ Client │ ────────────────────►  │  Django   │ ────────────────────►  │  Via API  │
│        │  {payment_attempt_id,  │           │                        │           │
│        │   verification_code}   │  Updates  │ ◄────────────────────  │  Confirms │
│        │                        │  Payment  │   {success}            │           │
│        │ ◄────────────────────  │  (SUCCESS)│                        │           │
│        │  {subscription data}   │  Creates  │                        │           │
│        │                        │Subscription│                       │           │
└────────┘                        └───────────┘                        └───────────┘
```

---

## Permission System

| Permission | Applied To | Logic |
|------------|-----------|-------|
| `AllowAny` | Course list, Lesson list, Subscription plans | No auth needed |
| `IsAuthenticated` | Profile, Enrolled courses, Enrollment endpoints, Payment endpoints | JWT required |
| `HasLessonAccess` | Lesson detail (object-level) | `is_free=True` → allow all; `is_free=False` → require active Subscription (`starts_at <= now <= expires_at`) |

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| Language | Python 3.12 |
| Framework | Django 6.0.2, DRF |
| Database | PostgreSQL 18.2 |
| Auth | SimpleJWT (access: 5h, refresh: 1d) |
| OTP | Custom 12-digit codes, 1-min expiry |
| Payments | Via payment gateway (card + SMS) |
| Bot | python-telegram-bot 22.6 |
| Linting | Ruff 0.15.1 (80 char lines, double quotes) |
| Testing | pytest + pytest-django |
| CI | GitHub Actions (lint + test on non-main branches) |
| Hosting | Heroku (staging + production) |
| Static (prod) | AWS S3 |
| Static (staging) | WhiteNoise |
| Monitoring | Sentry |

---

## Development Commands

```bash
# Environment setup
source deployments/development/env
export ENV_DJANGO_SECRET_KEY="test-secret-key"   # if env fails

# Docker (PostgreSQL)
make up-d              # Start PostgreSQL
make down              # Stop

# Dependencies
make install-dev       # Create venv + install dev deps

# Database
make migrate           # Apply migrations
make makemigrations    # Generate migrations

# Server
make runserver         # Start dev server

# Testing
pytest tests/
pytest tests/keypro/test_views.py::TestClassName::test_method

# Code quality
make lint              # Check (ruff check)
make lint-fix          # Auto-fix
make format            # Format (ruff format)
make format-check      # Check formatting

# Utilities
make get-auth-code USERNAME=<telegram_username>
make set-webhook       # Register Telegram webhook
make delete-webhook    # Remove Telegram webhook
```

---

## Settings Hierarchy

```
config.settings.base          # Shared settings (JWT, REST, CORS, Telegram, Via)
  ├── config.settings.development   # DEBUG=True, local DB, debug toolbar, Swagger
  ├── config.settings.test          # DEBUG=False, test DB
  ├── config.settings.staging       # Heroku, WhiteNoise, Sentry, Swagger
  └── config.settings.production    # Heroku, AWS S3, Sentry, no Swagger
```

---

## CI/CD Pipeline

**CI** (`.github/workflows/ci.yaml`) — triggers on push to any non-main branch:
1. **Lint job**: `ruff check .` + `ruff format --check .`
2. **Test job** (depends on lint): PostgreSQL service → migrate → `pytest`

**Staging deploy** (manual): Heroku deploy via GitHub Actions

**Production deploy** (manual): Heroku deploy via GitHub Actions

**Heroku release phase** (`Procfile`):
```
release: collectstatic --no-input && migrate --no-input
web: gunicorn config.wsgi
```

---

## Git Workflow

- **Never push directly to main** — always use feature branches and PRs
- Branch naming: `kinoyatov/<feature-name>`
- Pre-commit hooks enforce Ruff linting and formatting on every commit

---

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Django | 6.0.2 | Web framework |
| djangorestframework-simplejwt | 5.5.1 | JWT authentication |
| django-cors-headers | 4.9.0 | CORS handling |
| psycopg2-binary | 2.9.11 | PostgreSQL driver |
| django-phonenumber-field | 8.4.0 | Phone number field |
| python-telegram-bot | 22.6 | Telegram bot API |
| Pillow | 11.1.0 | Image processing (cover images) |
| requests | 2.32.5 | HTTP client (Via API) |
| gunicorn | 23.0.0 | Production WSGI server |
| whitenoise | 6.9.0 | Static file serving (staging) |
| sentry-sdk | 2.22.0 | Error tracking |
| drf-yasg | 1.21.8 | Swagger/OpenAPI docs |
| ruff | 0.15.1 | Linting + formatting |
| pytest-django | 4.12.0 | Django test integration |
