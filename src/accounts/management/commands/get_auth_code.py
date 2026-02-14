from django.core.management.base import BaseCommand, CommandError

from accounts.models import AuthCode, AuthCodeExistsException, User


class Command(BaseCommand):
    help = "Generate an auth code for a user by telegram username (development only)"

    def add_arguments(self, parser):
        parser.add_argument("telegram_username", type=str)

    def handle(self, *args, **options):
        username = options["telegram_username"].lstrip("@")

        try:
            user = User.objects.get(telegram_username=username)
        except User.DoesNotExist:
            raise CommandError(
                f"User with telegram username '{username}' not found."
            ) from None

        try:
            auth_code = AuthCode.create_for_user(user)
        except AuthCodeExistsException:
            auth_code = user.authcode
            self.stdout.write(
                self.style.WARNING(f"Existing valid code: {auth_code.code}")
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Auth code: {auth_code.code}"))
