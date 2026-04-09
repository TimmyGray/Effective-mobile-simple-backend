from django.contrib.auth import get_user_model
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_me_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
