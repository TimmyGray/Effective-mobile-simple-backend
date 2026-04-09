from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import AuthPolicyRule
from accounts.policy import decide
from accounts.tests.constants import REST_FRAMEWORK_NO_THROTTLE
from accounts.views import LoginView, RegisterView

User = get_user_model()


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_NO_THROTTLE)
class AuthzDecisionMatrixApiTests(APITestCase):
    """
    B-M1: HTTP-level matrix for auth policy actions — explicit deny vs seeded allows.

    AI Annotation:
    - Purpose: Lock 401/403 behavior and `decide()` reason codes for `auth:*` view wiring.
    - Inputs: Seeded migrations plus per-test `AuthPolicyRule` rows; session + CSRF like other API tests.
    - Security notes: Asserts explicit per-user denies override global allows; no credential secrets in tests.
    """

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

    def _csrf(self) -> str:
        r = self.client.get("/api/auth/csrf")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        return str(r.data["csrfToken"])

    def _registration_payload(self, email: str) -> dict[str, str]:
        return {
            "email": email,
            "first_name": "Nikolay",
            "last_name": "Sidorov",
            "middle_name": "Ivanovich",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

    def test_patch_me_403_when_explicit_user_deny_on_profile_update(self) -> None:
        csrf = self._csrf()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("nopatch@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        AuthPolicyRule.objects.create(
            resource="auth",
            action="profile_update",
            subject_type=AuthPolicyRule.SUBJECT_USER,
            subject_value="nopatch@example.com",
            is_allowed=False,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "nopatch@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        response = self.client.patch(
            "/api/auth/me",
            {"email": "still@example.com"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_403_when_explicit_user_deny_on_logout(self) -> None:
        csrf = self._csrf()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("nologout@example.com"),
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        AuthPolicyRule.objects.create(
            resource="auth",
            action="logout",
            subject_type=AuthPolicyRule.SUBJECT_USER,
            subject_value="nologout@example.com",
            is_allowed=False,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "nologout@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        response = self.client.post("/api/auth/logout", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_decide_matrix_reason_codes_for_auth_resource(self) -> None:
        """
        Documents stable `decide()` reasons for the `auth` resource actions used by API views.
        """
        u = User.objects.create_user(email="doc@example.com", password="StrongPass123!")
        self.assertEqual(decide(u, "auth", "me").reason, "explicit_allow")
        self.assertEqual(decide(u, "auth", "logout").reason, "explicit_allow")
        self.assertEqual(decide(u, "auth", "profile_update").reason, "explicit_allow")
        self.assertEqual(decide(u, "auth", "account_deactivate").reason, "explicit_allow")
        self.assertEqual(decide(u, "auth", "admin_probe").reason, "default_deny")
