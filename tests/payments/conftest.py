import pytest

from payments.models import PaymentAttempt, SubscriptionPlan


@pytest.fixture
def plan(db):
    return SubscriptionPlan.objects.create(
        name="Monthly",
        duration_days=30,
        price=49900.00,
    )


@pytest.fixture
def inactive_plan(db):
    return SubscriptionPlan.objects.create(
        name="Archived Plan",
        duration_days=30,
        price=29900.00,
        is_active=False,
    )


@pytest.fixture
def payment_attempt(user, plan):
    return PaymentAttempt.objects.create(
        user=user,
        plan=plan,
        amount=plan.price,
        status=PaymentAttempt.PENDING,
        verification_id="test-verify-id-123",
    )


@pytest.fixture
def valid_initiate_data(plan):
    return {
        "plan_id": plan.id,
        "card_pan": "8600123456789012",
        "expiry_month": 12,
        "expiry_year": 25,
    }


@pytest.fixture
def valid_verify_data(payment_attempt):
    return {
        "payment_attempt_id": str(payment_attempt.guid),
        "verification_code": "123456",
    }


@pytest.fixture
def via_initiate_success():
    return {
        "verifyId": "test-verify-id-123",
        "phone": "998*******18",
    }


@pytest.fixture
def via_verify_success():
    return {
        "transactionId": "txn-001",
        "amount": 4990000,
        "status": "SUCCESS",
        "fee": 74850,
        "feePercent": 1.5,
        "currency": "UZS",
    }


@pytest.fixture
def via_error_response():
    return {
        "error": {
            "message": {
                "uz": "Karta topilmadi",
                "ru": "\u0411\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0430\u044f \u043a\u0430\u0440\u0442\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430",
                "en": "Bank card not found",
            }
        }
    }
