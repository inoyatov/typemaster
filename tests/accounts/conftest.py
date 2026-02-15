from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import AuthCode


@pytest.fixture
def auth_code(user):
    return AuthCode.objects.create(
        user=user,
        code="123456789012",
        expires_at=timezone.now() + timedelta(minutes=5),
    )


@pytest.fixture
def expired_auth_code(user):
    return AuthCode.objects.create(
        user=user,
        code="999999999999",
        expires_at=timezone.now() - timedelta(minutes=1),
    )
