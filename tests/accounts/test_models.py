from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import IntegrityError
from django.utils import timezone

from accounts.models import AuthCode, AuthCodeExistsException, User


@pytest.mark.django_db(transaction=True)
class TestAuthCodeUniqueConstraint:
    def test_duplicate_code_raises_integrity_error(self, user):
        AuthCode.objects.create(
            user=user,
            code="111111111111",
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        with pytest.raises(IntegrityError):
            AuthCode.objects.create(
                user=other_user,
                code="111111111111",
                expires_at=timezone.now() + timedelta(minutes=5),
            )


@pytest.mark.django_db
class TestAuthCodeCreateForUser:
    def test_creates_auth_code(self, user):
        code = AuthCode.create_for_user(user)

        assert code is not None
        assert code.user == user
        assert len(code.code) > 0
        assert not code.is_expired

    def test_raises_if_valid_code_exists(self, auth_code):
        with pytest.raises(AuthCodeExistsException):
            AuthCode.create_for_user(auth_code.user)

    def test_replaces_expired_code(self, expired_auth_code):
        user = expired_auth_code.user
        old_code = expired_auth_code.code

        new_code = AuthCode.create_for_user(user)

        assert new_code.code != old_code
        assert not AuthCode.objects.filter(code=old_code).exists()

    def test_code_uses_only_digits(self, user):
        code = AuthCode.create_for_user(user)
        assert code.code.isdigit()


@pytest.mark.django_db(transaction=True)
class TestAuthCodeCreateForUserRetry:
    def test_retries_on_integrity_error(self, user):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        AuthCode.objects.create(
            user=other_user,
            code="111111111111",
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        call_count = 0

        def side_effect(digits):
            nonlocal call_count
            call_count += 1
            if call_count <= 12:
                return "1"  # First attempt: all 1s (collision)
            return "2"  # Second attempt: all 2s (no collision)

        with patch("accounts.models.secrets.choice", side_effect=side_effect):
            code = AuthCode.create_for_user(user)

        assert code.code == "222222222222"

    def test_raises_after_max_attempts_exhausted(self, user):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        AuthCode.objects.create(
            user=other_user,
            code="1" * 12,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        with (
            patch("accounts.models.secrets.choice", return_value="1"),
            pytest.raises(IntegrityError),
        ):
            AuthCode.create_for_user(user, max_attempts=3)
