import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class VIAResponse:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code
        self.is_error = "error" in data

    def get_error_message(self, language="uz"):
        try:
            return self.data["error"]["message"][language]
        except (KeyError, TypeError):
            return "Unknown error"


class VIAClient:
    def __init__(self):
        self.base_url = settings.VIA_API_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "client-id": settings.VIA_API_CLIENT_ID,
            "client-secret": settings.VIA_API_CLIENT_SECRET,
        }

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        response = requests.request(
            method, url, headers=self.headers, timeout=30, **kwargs
        )
        response.raise_for_status()
        return VIAResponse(response.json(), response.status_code)

    def initiate_payment(
        self, amount_tiyins, card_pan, card_expiry, external_id, note=""
    ):
        """Initiate card payment. Returns verifyId for SMS verification."""
        return self._request(
            "POST",
            "/partner/merchant/confirm/pay",
            json={
                "amount": amount_tiyins,
                "merchantId": settings.VIA_MERCHANT_ID,
                "card": {"pan": card_pan, "expiry": card_expiry},
                "externalId": str(external_id),
                "accounts": {},
                "currency": "UZS",
                "note": note,
            },
        )

    def verify_payment(self, verify_id, verify_code):
        """Verify payment with SMS code. Returns transaction details."""
        return self._request(
            "POST",
            "/partner/merchant/confirm/pay/verify",
            json={
                "verifyId": verify_id,
                "verifyCode": verify_code,
            },
        )

    def resend_code(self, verify_id):
        """Resend SMS verification code."""
        return self._request(
            "POST",
            "/partner/merchant/pay/resend",
            json={
                "verifyId": verify_id,
            },
        )
