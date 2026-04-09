from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.tests.constants import REST_FRAMEWORK_NO_THROTTLE
from accounts.views import RegisterView


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_NO_THROTTLE)
class AuthHttpSemanticsTests(APITestCase):
    """
    B-C3 regression: unauthenticated clients must receive 401 (not 403) on protected routes;
    authenticated-but-forbidden clients receive 403.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._register_throttle_classes = RegisterView.throttle_classes
        RegisterView.throttle_classes = []

    @classmethod
    def tearDownClass(cls):
        RegisterView.throttle_classes = cls._register_throttle_classes
        super().tearDownClass()

    def test_csrf_unauthenticated_returns_200(self) -> None:
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrfToken", response.data)

    def test_register_unauthenticated_returns_201(self) -> None:
        csrf = self.client.get("/api/auth/csrf").data["csrfToken"]
        response = self.client.post(
            "/api/auth/register",
            {
                "email": "newuser@example.com",
                "first_name": "Alex",
                "last_name": "Ivanov",
                "middle_name": "Petrovich",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=str(csrf),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_probe_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/admin-probe")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
