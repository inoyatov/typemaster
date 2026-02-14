import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    guid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)

    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)

    phone_number = PhoneNumberField(_("phone number"), blank=True)
    nickname = models.CharField(_("nickname"), max_length=150, blank=True)
    display_name = models.CharField(
        _("display name"), max_length=50, blank=True
    )
    date_joined = models.DateTimeField(default=timezone.now)

    search_vector = SearchVectorField(blank=True, null=True, editable=False)

    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    terms_and_service_signed_at = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = "user"
        ordering = ("pk",)
        indexes = [
            models.Index(fields=["email"]),
            GinIndex(fields=["search_vector"]),
        ]

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def username(self):
        return self.email

    @property
    def name(self):
        return f"{self.nickname} ({self.first_name}, {self.last_name})"

    @property
    def terms_and_service_signed(self):
        return bool(self.terms_and_service_signed_at)

    @property
    def phone_number_formatted(self):
        return self.phone_number.as_e164.replace("+", "")
