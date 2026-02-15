import pytest
from django.conf import settings

from accounts.models import AuthCode
from accounts.serializers import AuthCodeSerializer


@pytest.mark.django_db
class TestAuthCodeSerializerValidCode:
    def test_valid_code_passes(self, auth_code):
        serializer = AuthCodeSerializer(data={"auth_code": auth_code.code})
        assert serializer.is_valid()

    def test_stores_auth_code_on_instance(self, auth_code):
        serializer = AuthCodeSerializer(data={"auth_code": auth_code.code})
        serializer.is_valid()
        assert serializer.auth_code == auth_code


@pytest.mark.django_db
class TestAuthCodeSerializerInvalidCode:
    def test_wrong_length_rejected(self):
        serializer = AuthCodeSerializer(data={"auth_code": "123"})
        assert not serializer.is_valid()
        assert "auth_code" in serializer.errors

    def test_nonexistent_code_rejected(self):
        code = "0" * settings.OTP_LENGTH
        serializer = AuthCodeSerializer(data={"auth_code": code})
        assert not serializer.is_valid()
        assert "auth_code" in serializer.errors


@pytest.mark.django_db
class TestAuthCodeSerializerExpiredCode:
    def test_expired_code_rejected(self, expired_auth_code):
        serializer = AuthCodeSerializer(
            data={"auth_code": expired_auth_code.code}
        )
        assert not serializer.is_valid()
        assert "auth_code" in serializer.errors

    def test_expired_code_deleted_from_db(self, expired_auth_code):
        code_value = expired_auth_code.code

        serializer = AuthCodeSerializer(data={"auth_code": code_value})
        serializer.is_valid()

        assert not AuthCode.objects.filter(code=code_value).exists()
