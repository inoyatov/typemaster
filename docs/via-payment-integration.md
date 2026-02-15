# Via Payment Integration

## Overview

Via payment gateway integration for subscription purchases via card payment.
Uses a **two-phase commit**: initiate payment (card details) -> verify payment (SMS code).

---

## Payment Flow

```
User                    Frontend              Backend                Via API
 |                         |                     |                     |
 |-- Select plan --------->|                     |                     |
 |-- Enter card details -->|                     |                     |
 |                         |-- POST /initiate -->|                     |
 |                         |                     |-- POST /pay ------->|
 |                         |                     |<-- verifyId --------|
 |                         |<-- payment_id ------|                     |
 |                         |                     |                Via sends SMS
 |<-- SMS code ------------|---------------------|---------------------|
 |-- Enter SMS code ------>|                     |                     |
 |                         |-- POST /verify ---->|                     |
 |                         |                     |-- POST /verify ---->|
 |                         |                     |<-- SUCCESS ---------|
 |                         |                     |-- create Subscription
 |                         |<-- success ---------|                     |
```

### PaymentAttempt State Machine

```
INITIATED --> PENDING --> SUCCESS
    |             |
    v             v
  FAILED       FAILED
```

- **INITIATED**: PaymentAttempt created, Via API call in progress
- **PENDING**: Via accepted the card, SMS sent, waiting for verification code
- **SUCCESS**: Payment verified, subscription created
- **FAILED**: Via rejected card, API error, or post-payment failure

---

## API Endpoints

All endpoints require JWT authentication unless noted.

### 1. `POST /api/subscription/pay/initiate/`

Initiates a card payment. Via sends an SMS code to the cardholder.

**Request:**
```json
{
    "plan_id": 1,
    "card_pan": "8600123456789012",
    "expiry_month": 12,
    "expiry_year": 25
}
```

**Success Response (200):**
```json
{
    "payment_attempt_id": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "998*******18"
}
```

**Validation:**
- `card_pan`: exactly 16 digits
- `expiry_month`: 1-12
- `expiry_year`: 0-99 (2-digit)
- `plan_id`: must reference an active `SubscriptionPlan`

### 2. `POST /api/subscription/pay/verify/`

Verifies the SMS code. On success, creates a `Subscription` atomically.

**Request:**
```json
{
    "payment_attempt_id": "550e8400-e29b-41d4-a716-446655440000",
    "verification_code": "123456"
}
```

**Success Response (200):**
```json
{
    "status": "success"
}
```

**Validation:**
- `verification_code`: exactly 6 digits
- `payment_attempt_id`: must exist, belong to the user, and be in `PENDING` status

### 3. `POST /api/subscription/pay/resend-code/`

Resends the SMS verification code.

**Request:**
```json
{
    "payment_attempt_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Success Response (200):**
```json
{
    "status": "ok"
}
```

---

## Error Handling

| Scenario | HTTP Status | Response |
|---|---|---|
| Invalid input (card, plan, code format) | 400 | DRF validation errors |
| Via rejects card (invalid card, insufficient funds) | 400 | `{"error": "<Via message in Uzbek>"}` |
| Wrong SMS verification code | 400 | `{"error": "<Via message>"}` |
| PaymentAttempt not found or wrong user | 404 | `{"error": "Payment attempt not found."}` |
| Via API unreachable / HTTP error | 502 | `{"error": "Payment service unavailable."}` |
| Subscription creation fails after payment | 500 | `{"error": "Payment was successful but subscription creation failed. Please contact support."}` |

The last case (500 after successful payment) logs the full exception with the PaymentAttempt GUID for manual resolution.

---

## Via API Reference

### Authentication
HTTP headers on every request:
- `client-id`: `VIA_API_CLIENT_ID`
- `client-secret`: `VIA_API_CLIENT_SECRET`
- `Content-Type`: `application/json`

### Via Endpoints Used

#### Initiate Payment
```
POST {VIA_API_BASE_URL}/partner/merchant/confirm/pay

{
    "amount": 1000000,                  // tiyins (1 SOM = 100 tiyins)
    "merchantId": "<VIA_MERCHANT_ID>",
    "card": {
        "pan": "8600123456789012",
        "expiry": "1225"                // MMYY
    },
    "externalId": "<PaymentAttempt.guid>",
    "accounts": {},
    "currency": "UZS",
    "note": ""
}

Success: {"verifyId": "abc123", "phone": "998*******18"}
Error:   {"error": {"message": {"uz": "...", "ru": "...", "en": "..."}}}
```

#### Verify Payment
```
POST {VIA_API_BASE_URL}/partner/merchant/confirm/pay/verify

{"verifyId": "abc123", "verifyCode": "123456"}

Success: {"transactionId": "...", "amount": 1000000, "status": "SUCCESS", ...}
```

#### Resend SMS Code
```
POST {VIA_API_BASE_URL}/partner/merchant/pay/resend

{"verifyId": "abc123"}
```

---

## Configuration

### Environment Variables

Add to deployment env files:

```bash
ENV_VIA_API_BASE_URL=https://api.viasandbox.uz    # sandbox for dev/staging
ENV_VIA_API_CLIENT_ID=your-client-id
ENV_VIA_API_CLIENT_SECRET=your-client-secret
ENV_VIA_MERCHANT_ID=your-merchant-id
```

Settings are loaded in `src/config/settings/base.py` with empty string defaults (won't crash on startup if unset, but API calls will fail).

---

## Files Changed

| File | Change |
|---|---|
| `src/payments/models.py` | Added `PaymentAttempt` model (guid, user, plan, status, verification_id, amount) |
| `src/payments/serializers.py` | Added `InitiatePaymentSerializer`, `VerifyPaymentSerializer`, `ResendCodeSerializer` |
| `src/payments/views.py` | Added `InitiatePaymentView`, `VerifyPaymentView`, `ResendCodeView` |
| `src/payments/urls.py` | Added 3 URL routes under `subscription/pay/` |
| `src/payments/admin.py` | Added `PaymentAttemptAdmin` |
| `src/payments/clients/__init__.py` | Created (empty package init) |
| `src/payments/clients/via/__init__.py` | Created (exports `VIAClient`) |
| `src/payments/clients/via/client.py` | Created (`VIAClient` with `initiate_payment`, `verify_payment`, `resend_code`) |
| `src/config/settings/base.py` | Added `VIA_API_BASE_URL`, `VIA_API_CLIENT_ID`, `VIA_API_CLIENT_SECRET`, `VIA_MERCHANT_ID` |
| `requirements/base.txt` | Added `requests==2.32.5` |
| `src/payments/migrations/0002_paymentattempt.py` | Auto-generated migration |

---

## Database Schema

### `payment_attempt` table

| Column | Type | Notes |
|---|---|---|
| `id` | BigAutoField | Primary key |
| `guid` | UUID | Unique, default uuid4, used as external reference |
| `user_id` | FK -> user | CASCADE on delete |
| `plan_id` | FK -> subscription_plan | PROTECT on delete |
| `status` | CharField(20) | initiated / pending / success / failed |
| `verification_id` | CharField(255) | Via's `verifyId`, blank until PENDING |
| `amount` | Decimal(12,2) | Plan price at time of attempt |
| `created_at` | DateTimeField | auto_now_add |
