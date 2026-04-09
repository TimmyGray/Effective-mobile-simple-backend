from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import AuthPolicyRule
from accounts.policy import PolicyDecision, decide, is_allowed


User = get_user_model()


class PolicyDecideTests(TestCase):
    def test_anonymous_user_is_denied_without_db_lookup(self) -> None:
        decision = decide(AnonymousUser(), "auth", "me")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "unauthenticated_or_inactive")

    def test_invalid_resource_or_action_returns_reason(self) -> None:
        user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        self.assertEqual(decide(user, "", "me").reason, "invalid_resource_action")
        self.assertEqual(decide(user, "auth", "").reason, "invalid_resource_action")

    def test_inactive_user_is_denied(self) -> None:
        user = User.objects.create_user(email="inactive@example.com", password="StrongPass123!")
        user.is_active = False
        user.save(update_fields=["is_active"])
        decision = decide(user, "auth", "me")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "unauthenticated_or_inactive")

    def test_default_deny_when_no_matching_rules(self) -> None:
        user = User.objects.create_user(email="solo@example.com", password="StrongPass123!")
        decision = decide(user, "unknown", "action")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "default_deny")

    def test_explicit_allow_any_rule_grants_access(self) -> None:
        user = User.objects.create_user(email="member@example.com", password="StrongPass123!")
        AuthPolicyRule.objects.create(
            resource="widgets",
            action="read",
            subject_type=AuthPolicyRule.SUBJECT_ANY,
            subject_value="",
            is_allowed=True,
        )
        decision = decide(user, "widgets", "read")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "explicit_allow")

    def test_explicit_user_deny_overrides_global_allow(self) -> None:
        user = User.objects.create_user(email="blocked@example.com", password="StrongPass123!")
        AuthPolicyRule.objects.create(
            resource="demo",
            action="ping",
            subject_type=AuthPolicyRule.SUBJECT_ANY,
            subject_value="",
            is_allowed=True,
        )
        AuthPolicyRule.objects.create(
            resource="demo",
            action="ping",
            subject_type=AuthPolicyRule.SUBJECT_USER,
            subject_value="blocked@example.com",
            is_allowed=False,
        )
        decision = decide(user, "demo", "ping")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "explicit_deny")

    def test_subject_any_deny_blocks_all_authenticated_users(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="StrongPass123!")
        AuthPolicyRule.objects.create(
            resource="gate",
            action="enter",
            subject_type=AuthPolicyRule.SUBJECT_ANY,
            subject_value="",
            is_allowed=False,
        )
        decision = decide(user, "gate", "enter")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "explicit_deny")

    def test_non_matching_user_rule_falls_through_to_any_allow(self) -> None:
        user = User.objects.create_user(email="current@example.com", password="StrongPass123!")
        AuthPolicyRule.objects.create(
            resource="mix",
            action="read",
            subject_type=AuthPolicyRule.SUBJECT_ANY,
            subject_value="",
            is_allowed=True,
        )
        AuthPolicyRule.objects.create(
            resource="mix",
            action="read",
            subject_type=AuthPolicyRule.SUBJECT_USER,
            subject_value="other@example.com",
            is_allowed=False,
        )
        decision = decide(user, "mix", "read")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "explicit_allow")

    def test_role_allow_matches_staff(self) -> None:
        user = User.objects.create_user(email="staff@example.com", password="StrongPass123!")
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        AuthPolicyRule.objects.create(
            resource="admin",
            action="peek",
            subject_type=AuthPolicyRule.SUBJECT_ROLE,
            subject_value="staff",
            is_allowed=True,
        )
        decision = decide(user, "admin", "peek")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "explicit_allow")

    def test_is_allowed_matches_decide(self) -> None:
        user = User.objects.create_user(email="match@example.com", password="StrongPass123!")
        AuthPolicyRule.objects.create(
            resource="x",
            action="y",
            subject_type=AuthPolicyRule.SUBJECT_ANY,
            subject_value="",
            is_allowed=True,
        )
        decision = decide(user, "x", "y")
        self.assertEqual(is_allowed(user, "x", "y"), decision.allowed)
        self.assertIsInstance(decision, PolicyDecision)


class AuthFlowTests(APITestCase):
    def _get_csrf_token(self) -> str:
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data.get("csrfToken")
        self.assertIsNotNone(token)
        return str(token)

    def test_register_login_me_logout_happy_path(self) -> None:
        csrf_token = self._get_csrf_token()
        register_response = self.client.post(
            "/api/auth/register",
            {"email": "user@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register_response.data["email"], "user@example.com")

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
