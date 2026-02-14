# Telegram Authentication

Passwordless authentication via Telegram bot using OTP (One-Time Password).

## Overview

Users authenticate by sharing their phone number through a Telegram bot. The system generates a 12-digit OTP code sent back via Telegram, which the client app exchanges for JWT tokens.

## Flow

```
User                    Telegram Bot                 API Server
 |                           |                           |
 |-- /start ---------------->|                           |
 |<-- "Share phone number" --|                           |
 |-- shares contact -------->|-- webhook POST ---------->|
 |                           |                           |-- create/find user
 |                           |                           |-- generate OTP
 |<-- "Here is your code" --|<-- send code --------------|
 |                           |                           |
 |-- POST /api/auth/token/ (auth_code) ----------------->|
 |<-- { access_token, refresh_token } -------------------|
```

## Setup

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ENV_TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `ENV_TELEGRAM_WEBHOOK_URL` | Public URL where Telegram sends updates |
| `ENV_TELEGRAM_WEBHOOK_SECRET` | Secret token for webhook verification (optional) |

### Register Webhook

```bash
python manage.py set_telegram_webhook
```

To remove the webhook:

```bash
python manage.py set_telegram_webhook --delete
```

## API Endpoints

### Exchange OTP for Tokens

```
POST /api/auth/token/
Content-Type: application/json

{
  "auth_code": "123456789012"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "is_new_user": true,
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "998901234567"
}
```

### Refresh Token

```
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Begin registration — bot asks for phone number |
| `/login` | Request a new OTP code (requires existing account) |

## OTP Rules

- Length: 12 digits
- Expires after: 1 minute
- Only one active code per user at a time
- Code is deleted after successful token exchange

## Token Lifetimes

- Access token: 5 hours
- Refresh token: 1 day

## User Account

When a user registers via Telegram, the following fields are populated:

- `phone_number` — from the shared contact
- `first_name`, `last_name` — from the Telegram profile
- `telegram_chat_id` — unique Telegram chat identifier
- `telegram_username` — Telegram username (if available)
- `email` — set to `{phone_number}@telegram.user`

## Development

Generate an auth code for testing without the Telegram bot:

```bash
python manage.py get_auth_code @telegram_username
```
