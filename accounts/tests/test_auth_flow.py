from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.tests.constants import REST_FRAMEWORK_NO_THROTTLE
from accounts.views import LoginView, RegisterView

User = get_user_model()


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_NO_THROTTLE)
class AuthFlowTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._register_throttle_classes = RegisterView.throttle_classes
        cls._login_throttle_classes = LoginView.throttle_classes
        RegisterView.throttle_classes = []
        LoginView.throttle_classes = []

    @classmethod
    def tearDownClass(cls):
        RegisterView.throttle_classes = cls._register_throttle_classes
        LoginView.throttle_classes = cls._login_throttle_classes
        super().tearDownClass()

    def _get_csrf_token(self) -> str:
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data.get("csrfToken")
        self.assertIsNotNone(token)
        return str(token)

    def _registration_payload(self, email: str, password: str = "StrongPass123!") -> dict[str, str]:
        return {
            "email": email,
            "first_name": "Ivan",
            "last_name": "Petrov",
            "middle_name": "Sergeevich",
            "password": password,
            "password_confirm": password,
        }

    def test_register_login_me_logout_happy_path(self) -> None:
        csrf_token = self._get_csrf_token()
        register_response = self.client.post(
            "/api/auth/register",
            self._registration_payload("user@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register_response.data["email"], "user@example.com")
        self.assertEqual(register_response.data["first_name"], "Ivan")
        self.assertEqual(register_response.data["last_name"], "Petrov")
        self.assertEqual(register_response.data["middle_name"], "Sergeevich")

        created_user = User.objects.get(email="user@example.com")
        self.assertTrue(created_user.check_password("StrongPass123!"))

        login_response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        me_response = self.client.get("/api/auth/me")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "user@example.com")

        logout_response = self.client.post("/api/auth/logout", HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        me_after_logout = self.client.get("/api/auth/me")
        self.assertEqual(me_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_invalid_credentials(self) -> None:
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        csrf_token = self._get_csrf_token()

        response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "WrongPassword123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_register_rejects_mismatched_password_confirmation(self) -> None:
        csrf_token = self._get_csrf_token()
        payload = self._registration_payload("mismatch@example.com")
        payload["password_confirm"] = "DifferentStrongPass123!"
        response = self.client.post(
            "/api/auth/register",
            payload,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_me_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_unauthenticated_returns_401(self) -> None:
        csrf_token = self._get_csrf_token()
        response = self.client.post("/api/auth/logout", HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_forbidden_path_returns_403(self) -> None:
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        csrf_token = self._get_csrf_token()
        self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        response = self.client.get("/api/auth/admin-probe")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_disabled_user_returns_401_with_generic_message(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="StrongPass123!")
        user.is_active = False
        user.save(update_fields=["is_active"])
        csrf_token = self._get_csrf_token()

        response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(response.data.get("detail")), "Invalid credentials.")

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "rest_framework.authentication.SessionAuthentication",
            ],
            "DEFAULT_PERMISSION_CLASSES": [
                "accounts.permissions.EnforcedAuthzPermission",
            ],
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.ScopedRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "auth_login": "3/min",
                "auth_register": "5/min",
            },
        }
    )
    def test_login_scope_uses_auth_login_rate_configuration(self) -> None:
        from accounts.views import LoginView

        self.assertEqual(LoginView.throttle_scope, "auth_login")

    def test_login_repeated_invalid_attempts_stay_unauthorized(self) -> None:
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        csrf_token = self._get_csrf_token()
        for _ in range(3):
            response = self.client.post(
                "/api/auth/login",
                {"email": "user@example.com", "password": "WrongPassword123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        final_response = self.client.post(
            "/api/auth/login",
            {"email": "user@example.com", "password": "WrongPassword123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(final_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_updates_email(self) -> None:
        csrf_token = self._get_csrf_token()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("old@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "old@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        patch = self.client.patch(
            "/api/auth/me",
            {"email": "new@example.com"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data["email"], "new@example.com")
        user = User.objects.get(pk=patch.data["id"])
        self.assertEqual(user.email, "new@example.com")

    def test_patch_password_requires_current_password(self) -> None:
        csrf_token = self._get_csrf_token()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("pw@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "pw@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        bad = self.client.patch(
            "/api/auth/me",
            {"password": "NewStrongPass456!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self.client.patch(
            "/api/auth/me",
            {
                "password": "NewStrongPass456!",
                "current_password": "StrongPass123!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.client.post("/api/auth/logout", HTTP_X_CSRFTOKEN=csrf_token)
        login_new = self.client.post(
            "/api/auth/login",
            {"email": "pw@example.com", "password": "NewStrongPass456!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_new.status_code, status.HTTP_200_OK)

    def test_delete_account_soft_deletes_and_ends_session(self) -> None:
        csrf_token = self._get_csrf_token()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("del@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "del@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        deleted = self.client.delete("/api/auth/me", HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        me_after = self.client.get("/api/auth/me")
        self.assertEqual(me_after.status_code, status.HTTP_401_UNAUTHORIZED)
        user = User.objects.get(email="del@example.com")
        self.assertFalse(user.is_active)
        re_login = self.client.post(
            "/api/auth/login",
            {"email": "del@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(re_login.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_after_deactivation_without_request_returns_401(self) -> None:
        csrf_token = self._get_csrf_token()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("stale@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "stale@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        user = User.objects.get(email="stale@example.com")
        user.is_active = False
        user.save(update_fields=["is_active"])
        stale = self.client.get("/api/auth/me")
        self.assertEqual(stale.status_code, status.HTTP_401_UNAUTHORIZED)
