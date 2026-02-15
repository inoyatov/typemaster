import uuid
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.urls import reverse

from payments.models import PaymentAttempt, Subscription

INITIATE_URL = reverse("payment-initiate")
VERIFY_URL = reverse("payment-verify")
RESEND_URL = reverse("payment-resend-code")


# =============================================================================
# InitiatePaymentView
# =============================================================================


@pytest.mark.django_db
class TestInitiatePaymentUnauthenticated:
    def test_returns_401(self, api_client, valid_initiate_data):
        response = api_client.post(INITIATE_URL, valid_initiate_data)
        assert response.status_code == 401


@pytest.mark.django_db
class TestInitiatePaymentValidation:
    def test_missing_fields(self, auth_client):
        response = auth_client.post(INITIATE_URL, {})
        assert response.status_code == 400
        assert "plan_id" in response.data
        assert "card_pan" in response.data
        assert "expiry_month" in response.data
        assert "expiry_year" in response.data

    def test_invalid_card_pan_too_short(self, auth_client, plan):
        data = {
            "plan_id": plan.id,
            "card_pan": "860012345",
            "expiry_month": 12,
            "expiry_year": 25,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "card_pan" in response.data

    def test_invalid_card_pan_non_numeric(self, auth_client, plan):
        data = {
            "plan_id": plan.id,
            "card_pan": "860012345678ABCD",
            "expiry_month": 12,
            "expiry_year": 25,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "card_pan" in response.data

    def test_expiry_month_out_of_range(self, auth_client, plan):
        data = {
            "plan_id": plan.id,
            "card_pan": "8600123456789012",
            "expiry_month": 13,
            "expiry_year": 25,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "expiry_month" in response.data

    def test_expiry_month_zero(self, auth_client, plan):
        data = {
            "plan_id": plan.id,
            "card_pan": "8600123456789012",
            "expiry_month": 0,
            "expiry_year": 25,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "expiry_month" in response.data

    def test_expiry_year_out_of_range(self, auth_client, plan):
        data = {
            "plan_id": plan.id,
            "card_pan": "8600123456789012",
            "expiry_month": 12,
            "expiry_year": 100,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "expiry_year" in response.data

    def test_nonexistent_plan(self, auth_client):
        data = {
            "plan_id": 99999,
            "card_pan": "8600123456789012",
            "expiry_month": 12,
            "expiry_year": 25,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "plan_id" in response.data

    def test_inactive_plan_rejected(self, auth_client, inactive_plan):
        data = {
            "plan_id": inactive_plan.id,
            "card_pan": "8600123456789012",
            "expiry_month": 12,
            "expiry_year": 25,
        }
        response = auth_client.post(INITIATE_URL, data)
        assert response.status_code == 400
        assert "plan_id" in response.data


@pytest.mark.django_db
class TestInitiatePaymentSuccess:
    @patch("payments.views.VIAClient")
    def test_returns_payment_attempt_id_and_phone(
        self,
        mock_client_cls,
        auth_client,
        valid_initiate_data,
        via_initiate_success,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_initiate_success
        mock_client.initiate_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        response = auth_client.post(INITIATE_URL, valid_initiate_data)

        assert response.status_code == 200
        assert "payment_attempt_id" in response.data
        assert response.data["phone"] == "998*******18"

    @patch("payments.views.VIAClient")
    def test_creates_payment_attempt_with_pending_status(
        self,
        mock_client_cls,
        auth_client,
        valid_initiate_data,
        via_initiate_success,
        user,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_initiate_success
        mock_client.initiate_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        response = auth_client.post(INITIATE_URL, valid_initiate_data)

        attempt = PaymentAttempt.objects.get(
            guid=response.data["payment_attempt_id"]
        )
        assert attempt.status == PaymentAttempt.PENDING
        assert attempt.user == user
        assert attempt.verification_id == "test-verify-id-123"

    @patch("payments.views.VIAClient")
    def test_sends_correct_amount_in_tiyins(
        self,
        mock_client_cls,
        auth_client,
        valid_initiate_data,
        via_initiate_success,
        plan,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_initiate_success
        mock_client.initiate_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        auth_client.post(INITIATE_URL, valid_initiate_data)

        call_kwargs = mock_client.initiate_payment.call_args[1]
        assert call_kwargs["amount_tiyins"] == int(plan.price * 100)

    @patch("payments.views.VIAClient")
    def test_formats_card_expiry_as_mmyy(
        self, mock_client_cls, auth_client, plan, via_initiate_success
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_initiate_success
        mock_client.initiate_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        data = {
            "plan_id": plan.id,
            "card_pan": "8600123456789012",
            "expiry_month": 3,
            "expiry_year": 5,
        }
        auth_client.post(INITIATE_URL, data)

        call_kwargs = mock_client.initiate_payment.call_args[1]
        assert call_kwargs["card_expiry"] == "0305"


@pytest.mark.django_db
class TestInitiatePaymentViaError:
    @patch("payments.views.VIAClient")
    def test_via_validation_error_returns_400(
        self,
        mock_client_cls,
        auth_client,
        valid_initiate_data,
        via_error_response,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = True
        mock_response.data = via_error_response
        mock_response.get_error_message.return_value = "Karta topilmadi"
        mock_client.initiate_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        response = auth_client.post(INITIATE_URL, valid_initiate_data)

        assert response.status_code == 400
        assert response.data["error"] == "Karta topilmadi"

    @patch("payments.views.VIAClient")
    def test_via_validation_error_marks_attempt_failed(
        self,
        mock_client_cls,
        auth_client,
        valid_initiate_data,
        via_error_response,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = True
        mock_response.data = via_error_response
        mock_response.get_error_message.return_value = "Karta topilmadi"
        mock_client.initiate_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        auth_client.post(INITIATE_URL, valid_initiate_data)

        attempt = PaymentAttempt.objects.first()
        assert attempt.status == PaymentAttempt.FAILED

    @patch("payments.views.VIAClient")
    def test_via_http_error_returns_502(
        self, mock_client_cls, auth_client, valid_initiate_data
    ):
        mock_client = MagicMock()
        mock_client.initiate_payment.side_effect = requests.HTTPError("500")
        mock_client_cls.return_value = mock_client

        response = auth_client.post(INITIATE_URL, valid_initiate_data)

        assert response.status_code == 502
        assert "unavailable" in response.data["error"].lower()

    @patch("payments.views.VIAClient")
    def test_via_http_error_marks_attempt_failed(
        self, mock_client_cls, auth_client, valid_initiate_data
    ):
        mock_client = MagicMock()
        mock_client.initiate_payment.side_effect = requests.HTTPError("500")
        mock_client_cls.return_value = mock_client

        auth_client.post(INITIATE_URL, valid_initiate_data)

        attempt = PaymentAttempt.objects.first()
        assert attempt.status == PaymentAttempt.FAILED


# =============================================================================
# VerifyPaymentView
# =============================================================================


@pytest.mark.django_db
class TestVerifyPaymentUnauthenticated:
    def test_returns_401(self, api_client, valid_verify_data):
        response = api_client.post(VERIFY_URL, valid_verify_data)
        assert response.status_code == 401


@pytest.mark.django_db
class TestVerifyPaymentValidation:
    def test_missing_fields(self, auth_client):
        response = auth_client.post(VERIFY_URL, {})
        assert response.status_code == 400
        assert "payment_attempt_id" in response.data
        assert "verification_code" in response.data

    def test_invalid_verification_code_too_short(
        self, auth_client, payment_attempt
    ):
        data = {
            "payment_attempt_id": str(payment_attempt.guid),
            "verification_code": "123",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 400
        assert "verification_code" in response.data

    def test_invalid_verification_code_non_numeric(
        self, auth_client, payment_attempt
    ):
        data = {
            "payment_attempt_id": str(payment_attempt.guid),
            "verification_code": "12AB56",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 400
        assert "verification_code" in response.data

    def test_invalid_uuid(self, auth_client):
        data = {
            "payment_attempt_id": "not-a-uuid",
            "verification_code": "123456",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 400


@pytest.mark.django_db
class TestVerifyPaymentNotFound:
    def test_nonexistent_attempt_returns_404(self, auth_client):
        data = {
            "payment_attempt_id": str(uuid.uuid4()),
            "verification_code": "123456",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 404

    def test_attempt_belonging_to_other_user_returns_404(
        self, auth_client, plan, db
    ):
        from accounts.models import User

        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        attempt = PaymentAttempt.objects.create(
            user=other_user,
            plan=plan,
            amount=plan.price,
            status=PaymentAttempt.PENDING,
            verification_id="verify-other",
        )
        data = {
            "payment_attempt_id": str(attempt.guid),
            "verification_code": "123456",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 404

    def test_non_pending_attempt_returns_404(self, auth_client, user, plan):
        attempt = PaymentAttempt.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            status=PaymentAttempt.INITIATED,
            verification_id="verify-init",
        )
        data = {
            "payment_attempt_id": str(attempt.guid),
            "verification_code": "123456",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 404

    def test_already_successful_attempt_returns_404(
        self, auth_client, user, plan
    ):
        attempt = PaymentAttempt.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            status=PaymentAttempt.SUCCESS,
            verification_id="verify-done",
        )
        data = {
            "payment_attempt_id": str(attempt.guid),
            "verification_code": "123456",
        }
        response = auth_client.post(VERIFY_URL, data)
        assert response.status_code == 404


@pytest.mark.django_db
class TestVerifyPaymentSuccess:
    @patch("payments.views.VIAClient")
    def test_creates_subscription(
        self,
        mock_client_cls,
        auth_client,
        valid_verify_data,
        via_verify_success,
        user,
        plan,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_verify_success
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        response = auth_client.post(VERIFY_URL, valid_verify_data)

        assert response.status_code == 200
        assert response.data["status"] == "success"

        subscription = Subscription.objects.get(user=user)
        assert subscription.plan == plan
        assert subscription.is_active

    @patch("payments.views.VIAClient")
    def test_marks_attempt_as_success(
        self,
        mock_client_cls,
        auth_client,
        valid_verify_data,
        via_verify_success,
        payment_attempt,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_verify_success
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        auth_client.post(VERIFY_URL, valid_verify_data)

        payment_attempt.refresh_from_db()
        assert payment_attempt.status == PaymentAttempt.SUCCESS

    @patch("payments.views.VIAClient")
    def test_subscription_duration_matches_plan(
        self,
        mock_client_cls,
        auth_client,
        valid_verify_data,
        via_verify_success,
        user,
        plan,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_verify_success
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        auth_client.post(VERIFY_URL, valid_verify_data)

        subscription = Subscription.objects.get(user=user)
        duration = subscription.expires_at - subscription.starts_at
        assert duration.days == plan.duration_days


@pytest.mark.django_db
class TestVerifyPaymentViaError:
    @patch("payments.views.VIAClient")
    def test_via_error_returns_400(
        self, mock_client_cls, auth_client, valid_verify_data
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = True
        mock_response.get_error_message.return_value = "Kod noto'g'ri"
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        response = auth_client.post(VERIFY_URL, valid_verify_data)

        assert response.status_code == 400
        assert response.data["error"] == "Kod noto'g'ri"

    @patch("payments.views.VIAClient")
    def test_via_http_error_returns_502(
        self, mock_client_cls, auth_client, valid_verify_data
    ):
        mock_client = MagicMock()
        mock_client.verify_payment.side_effect = requests.HTTPError("500")
        mock_client_cls.return_value = mock_client

        response = auth_client.post(VERIFY_URL, valid_verify_data)

        assert response.status_code == 502

    @patch("payments.views.VIAClient")
    def test_via_error_does_not_create_subscription(
        self, mock_client_cls, auth_client, valid_verify_data
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = True
        mock_response.get_error_message.return_value = "Error"
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        auth_client.post(VERIFY_URL, valid_verify_data)

        assert Subscription.objects.count() == 0


@pytest.mark.django_db
class TestVerifyPaymentSubscriptionCreationFailure:
    @patch("payments.views.Subscription.objects")
    @patch("payments.views.VIAClient")
    def test_returns_500_on_db_error(
        self,
        mock_client_cls,
        mock_sub_objects,
        auth_client,
        valid_verify_data,
        via_verify_success,
        payment_attempt,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_verify_success
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        mock_sub_objects.create.side_effect = Exception("DB error")

        response = auth_client.post(VERIFY_URL, valid_verify_data)

        assert response.status_code == 500
        assert "contact support" in response.data["error"].lower()

    @patch("payments.views.Subscription.objects")
    @patch("payments.views.VIAClient")
    def test_marks_attempt_failed_on_db_error(
        self,
        mock_client_cls,
        mock_sub_objects,
        auth_client,
        valid_verify_data,
        via_verify_success,
        payment_attempt,
    ):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.is_error = False
        mock_response.data = via_verify_success
        mock_client.verify_payment.return_value = mock_response
        mock_client_cls.return_value = mock_client

        mock_sub_objects.create.side_effect = Exception("DB error")

        auth_client.post(VERIFY_URL, valid_verify_data)

        payment_attempt.refresh_from_db()
        assert payment_attempt.status == PaymentAttempt.FAILED


# =============================================================================
# ResendCodeView
# =============================================================================


@pytest.mark.django_db
class TestResendCodeUnauthenticated:
    def test_returns_401(self, api_client):
        data = {"payment_attempt_id": str(uuid.uuid4())}
        response = api_client.post(RESEND_URL, data)
        assert response.status_code == 401


@pytest.mark.django_db
class TestResendCodeValidation:
    def test_missing_payment_attempt_id(self, auth_client):
        response = auth_client.post(RESEND_URL, {})
        assert response.status_code == 400

    def test_invalid_uuid(self, auth_client):
        response = auth_client.post(
            RESEND_URL, {"payment_attempt_id": "not-a-uuid"}
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestResendCodeNotFound:
    def test_nonexistent_attempt_returns_404(self, auth_client):
        data = {"payment_attempt_id": str(uuid.uuid4())}
        response = auth_client.post(RESEND_URL, data)
        assert response.status_code == 404

    def test_non_pending_attempt_returns_404(self, auth_client, user, plan):
        attempt = PaymentAttempt.objects.create(
            user=user,
            plan=plan,
            amount=plan.price,
            status=PaymentAttempt.SUCCESS,
            verification_id="verify-done",
        )
        data = {"payment_attempt_id": str(attempt.guid)}
        response = auth_client.post(RESEND_URL, data)
        assert response.status_code == 404


@pytest.mark.django_db
class TestResendCodeSuccess:
    @patch("payments.views.VIAClient")
    def test_returns_ok(self, mock_client_cls, auth_client, payment_attempt):
        mock_client = MagicMock()
        mock_client.resend_code.return_value = MagicMock()
        mock_client_cls.return_value = mock_client

        data = {"payment_attempt_id": str(payment_attempt.guid)}
        response = auth_client.post(RESEND_URL, data)

        assert response.status_code == 200
        assert response.data["status"] == "ok"

    @patch("payments.views.VIAClient")
    def test_calls_via_with_correct_verify_id(
        self, mock_client_cls, auth_client, payment_attempt
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        data = {"payment_attempt_id": str(payment_attempt.guid)}
        auth_client.post(RESEND_URL, data)

        mock_client.resend_code.assert_called_once_with(
            payment_attempt.verification_id
        )


@pytest.mark.django_db
class TestResendCodeViaError:
    @patch("payments.views.VIAClient")
    def test_via_http_error_returns_502(
        self, mock_client_cls, auth_client, payment_attempt
    ):
        mock_client = MagicMock()
        mock_client.resend_code.side_effect = requests.HTTPError("500")
        mock_client_cls.return_value = mock_client

        data = {"payment_attempt_id": str(payment_attempt.guid)}
        response = auth_client.post(RESEND_URL, data)

        assert response.status_code == 502
