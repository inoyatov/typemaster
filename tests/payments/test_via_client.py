from unittest.mock import MagicMock, patch

import pytest
import requests

from payments.clients.via.client import VIAClient, VIAResponse


class TestVIAResponse:
    def test_success_response(self):
        data = {"verifyId": "abc", "phone": "998*******18"}
        response = VIAResponse(data, 200)

        assert response.data == data
        assert response.status_code == 200
        assert response.is_error is False

    def test_error_response(self):
        data = {
            "error": {
                "message": {
                    "uz": "Karta topilmadi",
                    "ru": "Карта не найдена",
                    "en": "Card not found",
                }
            }
        }
        response = VIAResponse(data, 400)

        assert response.is_error is True
        assert response.get_error_message("uz") == "Karta topilmadi"
        assert response.get_error_message("en") == "Card not found"

    def test_error_message_default_language(self):
        data = {"error": {"message": {"uz": "Xatolik"}}}
        response = VIAResponse(data, 400)

        assert response.get_error_message() == "Xatolik"

    def test_error_message_missing_language_returns_unknown(self):
        data = {"error": {"message": {"uz": "Xatolik"}}}
        response = VIAResponse(data, 400)

        assert response.get_error_message("fr") == "Unknown error"

    def test_error_message_malformed_error_returns_unknown(self):
        data = {"error": "unexpected format"}
        response = VIAResponse(data, 400)

        assert response.get_error_message() == "Unknown error"

    def test_error_message_none_message_returns_unknown(self):
        data = {"error": {"message": None}}
        response = VIAResponse(data, 400)

        assert response.get_error_message() == "Unknown error"


@pytest.mark.django_db
class TestVIAClient:
    @patch("payments.clients.via.client.requests.request")
    def test_initiate_payment_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "verifyId": "verify-123",
            "phone": "998*******18",
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        client = VIAClient()
        result = client.initiate_payment(
            amount_tiyins=4990000,
            card_pan="8600123456789012",
            card_expiry="1225",
            external_id="ext-001",
        )

        assert result.is_error is False
        assert result.data["verifyId"] == "verify-123"

        call_kwargs = mock_request.call_args
        assert call_kwargs[1]["json"]["amount"] == 4990000
        assert call_kwargs[1]["json"]["card"]["pan"] == "8600123456789012"
        assert call_kwargs[1]["json"]["card"]["expiry"] == "1225"
        assert call_kwargs[1]["json"]["externalId"] == "ext-001"
        assert call_kwargs[1]["json"]["currency"] == "UZS"

    @patch("payments.clients.via.client.requests.request")
    def test_verify_payment_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transactionId": "txn-001",
            "status": "SUCCESS",
        }
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        client = VIAClient()
        result = client.verify_payment("verify-123", "654321")

        assert result.is_error is False
        assert result.data["status"] == "SUCCESS"

        call_kwargs = mock_request.call_args
        assert call_kwargs[1]["json"]["verifyId"] == "verify-123"
        assert call_kwargs[1]["json"]["verifyCode"] == "654321"

    @patch("payments.clients.via.client.requests.request")
    def test_resend_code(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        client = VIAClient()
        result = client.resend_code("verify-123")

        assert result.is_error is False
        call_kwargs = mock_request.call_args
        assert call_kwargs[1]["json"]["verifyId"] == "verify-123"

    @patch("payments.clients.via.client.requests.request")
    def test_http_error_propagates(self, mock_request):
        mock_request.side_effect = requests.HTTPError("500 Server Error")

        client = VIAClient()
        with pytest.raises(requests.HTTPError):
            client.initiate_payment(
                amount_tiyins=100,
                card_pan="8600000000000000",
                card_expiry="1225",
                external_id="ext-001",
            )

    @patch("payments.clients.via.client.requests.request")
    def test_request_includes_auth_headers(self, mock_request, settings):
        settings.VIA_API_BASE_URL = "https://api.test.via.uz"
        settings.VIA_API_CLIENT_ID = "test-client-id"
        settings.VIA_API_CLIENT_SECRET = "test-client-secret"
        settings.VIA_MERCHANT_ID = "test-merchant"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"verifyId": "v1"}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        client = VIAClient()
        client.initiate_payment(100, "8600000000000000", "1225", "ext-001")

        call_args = mock_request.call_args
        headers = call_args[1]["headers"]
        assert headers["client-id"] == "test-client-id"
        assert headers["client-secret"] == "test-client-secret"
        assert headers["Content-Type"] == "application/json"

        url = call_args[0][1]
        assert url.startswith("https://api.test.via.uz")

    @patch("payments.clients.via.client.requests.request")
    def test_request_timeout_is_set(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_request.return_value = mock_response

        client = VIAClient()
        client.resend_code("v1")

        call_kwargs = mock_request.call_args
        assert call_kwargs[1]["timeout"] == 30
