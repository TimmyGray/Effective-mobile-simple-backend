from unittest.mock import patch

from django.test import Client, TestCase


class HealthEndpointTests(TestCase):
    """HTTP contract for ops probes (no auth required)."""

    def setUp(self) -> None:
        self.client = Client()

    def test_live_returns_200_json(self) -> None:
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ready_returns_200_when_db_available(self) -> None:
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ready_returns_503_when_db_unavailable(self) -> None:
        with patch(
            "config.health.connection.ensure_connection",
            side_effect=RuntimeError("boom"),
        ):
            response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "unavailable", "detail": "database_unavailable"},
        )
