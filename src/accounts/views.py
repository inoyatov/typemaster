import json
import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Count, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import AuthCode, AuthCodeExistsException, User
from accounts.serializers import (
    AuthCodeSerializer,
    MyEnrolledCourseSerializer,
    MyProfileSerializer,
    MySubscriptionSerializer,
)
from accounts.services import (
    send_contact_request,
    send_message,
    send_remove_keyboard,
)
from keypro.models import (
    Assignment,
    CompletedAssignment,
    CourseEnrollment,
)
from payments.models import Subscription

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    def post(self, request):
        logger.info("Telegram webhook received request")

        if settings.TELEGRAM_WEBHOOK_SECRET:
            token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if token != settings.TELEGRAM_WEBHOOK_SECRET:
                logger.warning("Telegram webhook: invalid secret token")
                return JsonResponse({"error": "Forbidden"}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Telegram webhook: invalid JSON body")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        logger.info("Telegram webhook data: %s", data)

        message = data.get("message")
        if not message:
            logger.info("Telegram webhook: no message in payload")
            return JsonResponse({"ok": True})

        chat_id = message["chat"]["id"]
        from_user = message.get("from", {})
        username = from_user.get("username")

        contact = message.get("contact")
        if contact:
            logger.info(
                "Telegram webhook: contact received from chat_id=%s", chat_id
            )
            self._handle_contact(chat_id, contact, username)
            return JsonResponse({"ok": True})

        text = message.get("text", "")
        logger.info(
            "Telegram webhook: text=%s from chat_id=%s username=%s",
            text,
            chat_id,
            username,
        )

        if text.startswith("/start"):
            self._handle_start(chat_id, from_user, username)
        elif text.startswith("/login"):
            self._handle_login(chat_id)

        return JsonResponse({"ok": True})

    def _handle_start(self, chat_id, from_user, username):
        name = (
            from_user.get("first_name")
            or from_user.get("last_name")
            or username
            or "Anonymous"
        )
        send_contact_request(
            chat_id,
            f"Hi {name}, Please share your contact",
        )

    def _handle_contact(self, chat_id, contact, username):
        phone_number = contact.get("phone_number", "")
        phone_number = (
            f"+{phone_number}"
            if not phone_number.startswith("+")
            else phone_number
        )
        first_name = contact.get("first_name", username or "")
        last_name = contact.get("last_name", "")

        user, _ = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                "telegram_chat_id": chat_id,
                "telegram_username": username,
                "email": f"{phone_number}@telegram.user",
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        if not user.telegram_chat_id:
            user.telegram_chat_id = chat_id
            user.save(update_fields=["telegram_chat_id"])

        self._send_auth_code(chat_id, user)

    def _handle_login(self, chat_id):
        try:
            user = User.objects.get(telegram_chat_id=chat_id)
        except User.DoesNotExist:
            send_message(
                chat_id,
                "You don't have an account yet. "
                "Please use the /start command to start over",
            )
            return

        self._send_auth_code(chat_id, user)

    def _send_auth_code(self, chat_id, user):
        try:
            auth_code = AuthCode.create_for_user(user)
        except AuthCodeExistsException:
            send_remove_keyboard(chat_id, "You already have a valid code")
            return

        send_remove_keyboard(
            chat_id,
            f"Here is your code {auth_code.code}",
        )


class TokenObtainView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AuthCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_code = serializer.auth_code
        user = auth_code.user

        user_created_recently = user.date_joined > timezone.now() - timedelta(
            minutes=2
        )
        refresh = RefreshToken.for_user(user)

        auth_code.delete()

        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "is_new_user": user_created_recently,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": str(user.phone_number),
            }
        )


class MyProfileView(RetrieveUpdateAPIView):
    serializer_class = MyProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        subscription = (
            Subscription.objects.filter(
                user=request.user,
                starts_at__lte=now,
                expires_at__gte=now,
            )
            .select_related("plan")
            .first()
        )
        if not subscription:
            return Response({"subscription": None})
        serializer = MySubscriptionSerializer(subscription)
        return Response({"subscription": serializer.data})


class MyEnrolledCoursesView(ListAPIView):
    serializer_class = MyEnrolledCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        total_assignments_sq = (
            Assignment.objects.filter(
                lesson__course__pk=OuterRef("course_id"),
                lesson__is_active=True,
                is_active=True,
            )
            .order_by()
            .values("lesson__course")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        completed_assignments_sq = (
            CompletedAssignment.objects.filter(
                user=user,
                assignment__lesson__course__pk=OuterRef("course_id"),
                assignment__lesson__is_active=True,
                assignment__is_active=True,
            )
            .order_by()
            .values("assignment__lesson__course")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        return (
            CourseEnrollment.objects.filter(user=user)
            .select_related("course")
            .annotate(
                total_assignments=Coalesce(
                    Subquery(total_assignments_sq), Value(0)
                ),
                completed_assignments=Coalesce(
                    Subquery(completed_assignments_sq), Value(0)
                ),
            )
        )
