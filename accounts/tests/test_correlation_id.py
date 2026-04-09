import uuid

from rest_framework import status
from rest_framework.test import APITestCase


class CorrelationIdMiddlewareTests(APITestCase):
    def test_response_includes_correlation_id_header(self) -> None:
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("X-Correlation-ID", response)
        raw = response["X-Correlation-ID"]
        uuid.UUID(raw)

    def test_valid_incoming_correlation_id_is_echoed(self) -> None:
        cid = "client-req-0001"
        response = self.client.get("/api/auth/csrf", HTTP_X_CORRELATION_ID=cid)
        self.assertEqual(response["X-Correlation-ID"], cid)

    def test_invalid_incoming_correlation_id_is_replaced(self) -> None:
        response = self.client.get("/api/auth/csrf", HTTP_X_CORRELATION_ID="bad!")
        out = response["X-Correlation-ID"]
        self.assertNotEqual(out, "bad!")
        uuid.UUID(out)

    def test_short_correlation_id_is_replaced(self) -> None:
        response = self.client.get("/api/auth/csrf", HTTP_X_CORRELATION_ID="short")
        out = response["X-Correlation-ID"]
        self.assertNotEqual(out, "short")
        uuid.UUID(out)
