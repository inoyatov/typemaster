# Solo on Keyboard - Implementation Plan

## Context
Building a touch typing tutor web application (backend API). The project is a Django REST API with JWT auth and a User model already in place. We need to implement: Telegram bot OTP sign-in, payment integration (Via gateway), and a voucher/subscription system.

---

## Phase 1: Telegram Bot OTP Authentication

**Goal:** Users sign in by requesting an OTP code from a Telegram bot, then entering it in the app.

### 1.1 Create Telegram Bot & Dependencies
- Register a bot via @BotFather, store token in env vars
- Add `python-telegram-bot` to `requirements/base.txt`

### 1.2 OTP Model (`src/accounts/models.py`)
- Add `OTPCode` model:
  - `user` (FK to User)
  - `code` (6-digit string)
  - `created_at` (auto timestamp)
  - `expires_at` (created_at + 5 min)
  - `is_used` (boolean)
- Add `telegram_chat_id` and `telegram_username` fields to User model

### 1.3 Auth Flow API Endpoints (`src/accounts/views.py`)
1. **`POST /api/auth/telegram/request-otp/`** - User sends their Telegram username or phone
   - Looks up user (or creates one)
   - Generates OTP code, saves to DB
   - Sends OTP to user via Telegram bot
   - Returns success response
2. **`POST /api/auth/telegram/verify-otp/`** - User submits OTP code
   - Validates code (exists, not expired, not used)
   - Marks code as used
   - Returns JWT access + refresh tokens

### 1.4 Telegram Bot Script (`src/accounts/telegram_bot.py`)
- Bot listens for `/start` command - links user's `chat_id` to their account
- Bot is used as a sending mechanism (called from Django views to send OTP)
- Can run as a Django management command or separate process

### 1.5 Files to modify/create
- `src/accounts/models.py` - Add OTPCode model, telegram fields on User
- `src/accounts/serializers.py` - OTP request/verify serializers
- `src/accounts/views.py` - OTP endpoints
- `src/accounts/urls.py` - Wire up URLs
- `src/accounts/telegram_bot.py` - Bot logic
- `src/accounts/management/commands/run_telegram_bot.py` - Management command
- `src/config/urls/base.py` - Include accounts URLs
- `requirements/base.txt` - Add python-telegram-bot
- `deployments/development/env` - Add TELEGRAM_BOT_TOKEN

---

## Phase 2: Voucher & Subscription System

**Goal:** Users purchase vouchers (1, 3, or 12 months). Vouchers appear in billing page. User can activate for themselves or share the code with others.

### 2.1 Models (`src/payments/models.py`)

**VoucherPlan:**
- `name` (e.g., "1 Month", "3 Months", "1 Year")
- `duration_days` (30, 90, 365)
- `price` (DecimalField)
- `is_active` (boolean)

**Voucher:**
- `code` (unique, auto-generated, e.g., "SOK-XXXX-XXXX")
- `plan` (FK to VoucherPlan)
- `purchased_by` (FK to User)
- `activated_by` (FK to User, nullable)
- `purchased_at` (timestamp)
- `activated_at` (timestamp, nullable)
- `status` (choices: purchased, activated, expired)

**Subscription:**
- `user` (FK to User)
- `voucher` (OneToOne to Voucher)
- `starts_at` (timestamp)
- `expires_at` (timestamp)
- `is_active` (boolean/property)

### 2.2 API Endpoints (`src/payments/views.py`)
1. **`GET /api/payments/plans/`** - List available voucher plans (public)
2. **`POST /api/payments/vouchers/purchase/`** - Initiate voucher purchase (creates payment via Via)
3. **`GET /api/payments/vouchers/`** - List user's vouchers (billing page)
4. **`POST /api/payments/vouchers/activate/`** - Activate a voucher (own or by entering a code)
5. **`GET /api/payments/subscription/`** - Get current subscription status

### 2.3 Voucher Code Generation
- Format: `SOK-XXXX-XXXX` (uppercase alphanumeric, easy to share)
- Generated upon successful payment confirmation

### 2.4 Files to modify/create
- `src/payments/models.py` - VoucherPlan, Voucher, Subscription models
- `src/payments/serializers.py` - Serializers for all endpoints
- `src/payments/views.py` - ViewSets/APIViews
- `src/payments/urls.py` - URL routing
- `src/payments/admin.py` - Admin panel for managing plans/vouchers
- `src/config/urls/base.py` - Include payments URLs

---

## Phase 3: Via Payment Gateway Integration

**Goal:** Integrate Via payment gateway so users can pay for vouchers. Architecture is gateway-agnostic since docs aren't available yet.

### 3.1 Payment Model (`src/payments/models.py`)

**Payment:**
- `user` (FK to User)
- `voucher` (FK to Voucher, nullable until confirmed)
- `amount` (DecimalField)
- `status` (choices: pending, completed, failed, refunded)
- `gateway_transaction_id` (CharField, from Via)
- `gateway_response` (JSONField, store raw response)
- `created_at` / `updated_at`

### 3.2 Payment Flow
1. User selects plan → `POST /api/payments/vouchers/purchase/`
2. Backend creates Payment (status=pending), returns Via payment URL/params
3. User completes payment on Via
4. Via sends callback → `POST /api/payments/via/callback/` (webhook)
5. Backend verifies callback, marks Payment as completed
6. Backend generates Voucher with unique code
7. Voucher appears in user's billing page

### 3.3 API Endpoints
1. **`POST /api/payments/via/callback/`** - Webhook for Via payment notifications (no auth, verify by signature)
2. Purchase initiation is handled via the voucher purchase endpoint (Phase 2)

### 3.4 Files to modify/create
- `src/payments/models.py` - Add Payment model
- `src/payments/services.py` - Via gateway service class (abstracted, easy to swap)
- `src/payments/views.py` - Add callback webhook view
- `src/payments/urls.py` - Add callback URL
- `deployments/development/env` - Add VIA_* env vars

---

## Phase 4: KeyPro - Lessons & Sections

**Goal:** Set up lessons with keyboard layout variants, each containing 100 sections of text to type. First 10 sections are free, rest require active subscription.

### 4.1 Models (`src/keypro/models.py`)

**KeyboardLayout:**
- `name` (e.g., "US QWERTY", "Cyrillic ЙЦУКЕН", "German QWERTZ")
- `code` (unique slug, e.g., "us-qwerty", "ru-cyrillic")
- `is_active` (boolean)

**Lesson:**
- `layout` (FK to KeyboardLayout)
- `title` (e.g., "Home Row Basics")
- `description` (text)
- `order` (integer, for sequencing lessons within a layout)
- `is_active` (boolean)
- `total_sections` = 100 (constant/default)
- `free_sections` = 10 (constant/default)

**Section:**
- `lesson` (FK to Lesson)
- `order` (integer, 1-100)
- `text_content` (TextField - the text passage the user must type)
- `is_free` (boolean, True for sections 1-10)

### 4.2 Access Control Logic
- Sections with `order <= 10` (or `is_free=True`) → accessible to all authenticated users
- Sections with `order > 10` → require active subscription (check `Subscription.expires_at > now`)

### 4.3 Files to modify/create
- `src/keypro/models.py` - KeyboardLayout, Lesson, Section models
- `src/keypro/serializers.py` - Serializers
- `src/keypro/views.py` - ViewSets
- `src/keypro/urls.py` - URL routing
- `src/keypro/admin.py` - Admin for managing lessons/sections
- `src/keypro/permissions.py` - Custom permission for subscription check
- `src/config/urls/base.py` - Include keypro URLs

---

## Phase 5: KeyPro - Progress & Stats Tracking

**Goal:** Track user progress through lessons and record typing session statistics (WPM, accuracy, error keys).

### 5.1 Models (`src/keypro/models.py`)

**UserProgress:**
- `user` (FK to User)
- `lesson` (FK to Lesson)
- `last_completed_section` (integer)
- `completed_at` (nullable timestamp, when all 100 sections done)
- Unique constraint on (user, lesson)

**TypingSession:**
- `user` (FK to User)
- `section` (FK to Section)
- `wpm` (FloatField - words per minute)
- `accuracy` (FloatField - percentage 0-100)
- `error_keys` (JSONField - dict of {character: error_count})
- `duration_seconds` (integer)
- `completed_at` (timestamp)

### 5.2 API Endpoints
1. **`GET /api/keypro/layouts/`** - List keyboard layouts
2. **`GET /api/keypro/lessons/?layout=<code>`** - List lessons for a layout
3. **`GET /api/keypro/lessons/<id>/sections/`** - List sections (free ones always, paid if subscribed)
4. **`GET /api/keypro/sections/<id>/`** - Get section text content (with permission check)
5. **`POST /api/keypro/sessions/`** - Submit typing session result (WPM, accuracy, errors)
6. **`GET /api/keypro/progress/`** - Get user's progress across all lessons
7. **`GET /api/keypro/stats/`** - Get user's overall stats (avg WPM, accuracy, most error-prone keys)

### 5.3 Files to modify/create
- `src/keypro/models.py` - Add UserProgress, TypingSession
- `src/keypro/serializers.py` - Add session/progress serializers
- `src/keypro/views.py` - Add endpoints
- `src/keypro/urls.py` - Wire up URLs

---

## Implementation Order

| Step | What | Depends On |
|------|------|------------|
| 1 | Telegram OTP Auth (Phase 1) | Nothing - start here |
| 2 | Voucher & Subscription Models (Phase 2) | Phase 1 (need auth) |
| 3 | Via Payment Integration (Phase 3) | Phase 2 (need voucher models) |
| 4 | KeyPro Lessons & Sections (Phase 4) | Phase 1 (need auth) |
| 5 | KeyPro Progress & Stats (Phase 5) | Phase 4 (need lesson models) |

---

## Verification

1. **Telegram Auth:** Start bot, send `/start`, request OTP via API, verify OTP, receive JWT tokens
2. **Vouchers:** Create plan in admin, purchase voucher via API, verify code generated, activate voucher, check subscription active
3. **Payments:** Mock Via callback, verify payment status updates and voucher creation
4. **KeyPro:** Create layout + lesson + sections via admin, fetch sections (verify free access), try accessing section 11 without subscription (should fail), activate subscription, try again (should succeed)
5. **Stats:** Submit typing session, check progress updates, verify error key tracking
6. **Run tests:** `make test` after each phase
