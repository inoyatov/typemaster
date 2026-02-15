import logging
from datetime import timedelta

import requests
from django.db import transaction
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.clients.via import VIAClient
from payments.models import PaymentAttempt, Subscription, SubscriptionPlan
from payments.serializers import (
    InitiatePaymentSerializer,
    ResendCodeSerializer,
    SubscriptionPlanSerializer,
    VerifyPaymentSerializer,
)

logger = logging.getLogger(__name__)


class SubscriptionPlanListView(ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class InitiatePaymentView(APIView):
    """Step 1: User submits card details, Via sends SMS code."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data["plan_id"]
        card_pan = serializer.validated_data["card_pan"]
        expiry_month = serializer.validated_data["expiry_month"]
        expiry_year = serializer.validated_data["expiry_year"]
        card_expiry = f"{expiry_month:02d}{expiry_year:02d}"

        amount_tiyins = int(plan.price * 100)

        payment_attempt = PaymentAttempt.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            status=PaymentAttempt.INITIATED,
        )

        client = VIAClient()
        try:
            response = client.initiate_payment(
                amount_tiyins=amount_tiyins,
                card_pan=card_pan,
                card_expiry=card_expiry,
                external_id=payment_attempt.guid,
            )
        except requests.HTTPError:
            payment_attempt.status = PaymentAttempt.FAILED
            payment_attempt.save(update_fields=["status"])
            logger.exception("Via API HTTP error during payment initiation")
            return Response(
                {"error": "Payment service unavailable."}, status=502
            )

        if response.is_error:
            payment_attempt.status = PaymentAttempt.FAILED
            payment_attempt.save(update_fields=["status"])
            return Response({"error": response.get_error_message()}, status=400)

        payment_attempt.verification_id = response.data["verifyId"]
        payment_attempt.status = PaymentAttempt.PENDING
        payment_attempt.save(update_fields=["verification_id", "status"])

        return Response(
            {
                "payment_attempt_id": payment_attempt.guid,
                "phone": response.data.get("phone", ""),
            }
        )


class VerifyPaymentView(APIView):
    """Step 2: User submits SMS code, payment confirmed, subscription created."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment_attempt = PaymentAttempt.objects.get(
                guid=serializer.validated_data["payment_attempt_id"],
                user=request.user,
                status=PaymentAttempt.PENDING,
            )
        except PaymentAttempt.DoesNotExist:
            return Response({"error": "Payment attempt not found."}, status=404)

        client = VIAClient()
        try:
            response = client.verify_payment(
                verify_id=payment_attempt.verification_id,
                verify_code=serializer.validated_data["verification_code"],
            )
        except requests.HTTPError:
            logger.exception("Via API HTTP error during payment verification")
            return Response(
                {"error": "Payment service unavailable."}, status=502
            )

        if response.is_error:
            return Response({"error": response.get_error_message()}, status=400)

        try:
            with transaction.atomic():
                now = timezone.now()
                Subscription.objects.create(
                    user=request.user,
                    plan=payment_attempt.plan,
                    starts_at=now,
                    expires_at=now
                    + timedelta(days=payment_attempt.plan.duration_days),
                )
                payment_attempt.status = PaymentAttempt.SUCCESS
                payment_attempt.save(update_fields=["status"])
        except Exception:
            payment_attempt.status = PaymentAttempt.FAILED
            payment_attempt.save(update_fields=["status"])
            logger.exception(
                "Subscription creation failed after successful payment. "
                "PaymentAttempt guid=%s",
                payment_attempt.guid,
            )
            return Response(
                {
                    "error": "Payment was successful but subscription "
                    "creation failed. Please contact support."
                },
                status=500,
            )

        return Response({"status": "success"})


class ResendCodeView(APIView):
    """Resend SMS verification code."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment_attempt = PaymentAttempt.objects.get(
                guid=serializer.validated_data["payment_attempt_id"],
                user=request.user,
                status=PaymentAttempt.PENDING,
            )
        except PaymentAttempt.DoesNotExist:
            return Response({"error": "Payment attempt not found."}, status=404)

        client = VIAClient()
        try:
            client.resend_code(payment_attempt.verification_id)
        except requests.HTTPError:
            logger.exception("Via API HTTP error during code resend")
            return Response(
                {"error": "Payment service unavailable."}, status=502
            )

        return Response({"status": "ok"})
