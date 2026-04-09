from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_login_me_logout_happy_path(self) -> None:
        register_response = self.client.post(
            "/api/auth/register",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register_response.data["email"], "user@example.com")

        created_user = User.objects.get(email="user@example.com")
        self.assertTrue(created_user.check_password("StrongPass123!"))

        login_response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        me_response = self.client.get("/api/auth/me")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "user@example.com")

        logout_response = self.client.post("/api/auth/logout")
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        me_after_logout = self.client.get("/api/auth/me")
        self.assertEqual(me_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_invalid_credentials(self) -> None:
        User.objects.create_user(email="user@example.com", password="StrongPass123!")

        response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "WrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_me_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_unauthenticated_returns_401(self) -> None:
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_forbidden_path_returns_403(self) -> None:
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        response = self.client.get("/api/auth/admin-probe")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_disabled_user_returns_401_with_generic_message(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="StrongPass123!")
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data.get("detail")), "Invalid credentials.")

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "rest_framework.authentication.SessionAuthentication",
            ],
            "DEFAULT_PERMISSION_CLASSES": [
                "rest_framework.permissions.IsAuthenticated",
            ],
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "3/min",
                "user": "100/min",
                "auth_login": "3/min",
                "auth_register": "5/min",
            },
        }
    )
    def test_login_repeated_invalid_attempts_stay_unauthorized(self) -> None:
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        for _ in range(3):
            response = self.client.post(
                "/api/auth/login",
                {"email": "user@example.com", "password": "WrongPassword123!"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        final_response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "WrongPassword123!"},
            format="json",
        )
        self.assertEqual(final_response.status_code, status.HTTP_401_UNAUTHORIZED)
