from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.services import delete_webhook, set_webhook


class Command(BaseCommand):
    help = "Register or remove the Telegram bot webhook"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the webhook instead of setting it",
        )

    def handle(self, *args, **options):
        if options["delete"]:
            result = delete_webhook()
            self.stdout.write(self.style.SUCCESS(f"deleteWebhook: {result}"))
            return

        if not settings.TELEGRAM_WEBHOOK_URL:
            self.stderr.write(
                self.style.ERROR("ENV_TELEGRAM_WEBHOOK_URL is not set.")
            )
            return

        result = set_webhook()
        self.stdout.write(
            self.style.SUCCESS(
                f"setWebhook → {settings.TELEGRAM_WEBHOOK_URL}: {result}"
            )
        )
