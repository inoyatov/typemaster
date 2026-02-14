import json
import logging
from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import AuthCode, AuthCodeExistsException, User
from accounts.serializers import AuthCodeSerializer
from accounts.services import (
    send_contact_request,
    send_message,
    send_remove_keyboard,
)

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    def post(self, request):
        if settings.TELEGRAM_WEBHOOK_SECRET:
            token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if token != settings.TELEGRAM_WEBHOOK_SECRET:
                return JsonResponse({"error": "Forbidden"}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        message = data.get("message")
        if not message:
            return JsonResponse({"ok": True})

        chat_id = message["chat"]["id"]
        from_user = message.get("from", {})
        username = from_user.get("username")

        contact = message.get("contact")
        if contact:
            self._handle_contact(chat_id, contact, username)
            return JsonResponse({"ok": True})

        text = message.get("text", "")
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
        phone_number = phone_number.lstrip("+")
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
