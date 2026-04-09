from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.tests.constants import REST_FRAMEWORK_NO_THROTTLE


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_NO_THROTTLE)
class MockResourceAccessTests(APITestCase):
    """
    AI Annotation:
    - Purpose: Verify HTTP-level access control behavior for mock business resources.
    - Inputs: Seeded demo users from migrations and session-authenticated API client.
    - Outputs: Asserts expected 401/403/200 semantics for `/api/resources/widgets`.
    - Security notes: Confirms policy boundary on business routes, not only auth/admin routes.
    """

    def _get_csrf_token(self) -> str:
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data.get("csrfToken")
        self.assertIsNotNone(token)
        return str(token)

    def _login(self, email: str, password: str, csrf_token: str) -> None:
        response = self.client.post(
            "/api/auth/login",
            {"email": email, "password": password},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_widgets_list_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/resources/widgets")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_widgets_list_plain_user_returns_403(self) -> None:
        csrf_token = self._get_csrf_token()
        self._login("demo.plain@example.com", "DemoShowcase2026!", csrf_token)
        response = self.client.get("/api/resources/widgets")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_widgets_list_member_returns_200_with_items(self) -> None:
        csrf_token = self._get_csrf_token()
        self._login("demo.member@example.com", "DemoShowcase2026!", csrf_token)
        response = self.client.get("/api/resources/widgets")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertGreaterEqual(len(response.data["items"]), 1)
