import json
import logging
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import AuthPolicyRule, AccessPermission, Role, RolePermission, UserRole
from accounts.logging_formatters import AuditJsonFormatter
from accounts.policy import PolicyDecision, decide, is_allowed
from accounts.views import LoginView, RegisterView


User = get_user_model()

# ScopedRateThrottle reads DRF settings cached at import time; clear view throttles in AuthFlowTests.
_REST_FRAMEWORK_NO_THROTTLE = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.SessionAuthentication401",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "accounts.permissions.EnforcedAuthzPermission",
    ],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


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

    def test_role_allow_matches_persisted_user_role_binding(self) -> None:
        user = User.objects.create_user(email="bound@example.com", password="StrongPass123!")
        role = Role.objects.create(name="analyst")
        UserRole.objects.create(user=user, role=role)
        AuthPolicyRule.objects.create(
            resource="reports",
            action="export",
            subject_type=AuthPolicyRule.SUBJECT_ROLE,
            subject_value="analyst",
            is_allowed=True,
        )
        decision = decide(user, "reports", "export")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "explicit_allow")

    def test_matrix_allow_matches_role_permission_grants(self) -> None:
        user = User.objects.create_user(email="matrix@example.com", password="StrongPass123!")
        role = Role.objects.create(name="seller")
        ap = AccessPermission.objects.create(resource="orders", action="view")
        RolePermission.objects.create(role=role, access_permission=ap)
        UserRole.objects.create(user=user, role=role)
        decision = decide(user, "orders", "view")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "matrix_allow")

    def test_explicit_deny_overrides_matrix_grant(self) -> None:
        user = User.objects.create_user(email="blockedm@example.com", password="StrongPass123!")
        role = Role.objects.create(name="seller2")
        ap = AccessPermission.objects.create(resource="orders", action="cancel")
        RolePermission.objects.create(role=role, access_permission=ap)
        UserRole.objects.create(user=user, role=role)
        AuthPolicyRule.objects.create(
            resource="orders",
            action="cancel",
            subject_type=AuthPolicyRule.SUBJECT_USER,
            subject_value="blockedm@example.com",
            is_allowed=False,
        )
        decision = decide(user, "orders", "cancel")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "explicit_deny")

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

    def test_superuser_subject_role_rule_matches_via_user_roles(self) -> None:
        user = User.objects.create_user(email="su@example.com", password="StrongPass123!")
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
        AuthPolicyRule.objects.create(
            resource="vault",
            action="open",
            subject_type=AuthPolicyRule.SUBJECT_ROLE,
            subject_value="superuser",
            is_allowed=True,
        )
        decision = decide(user, "vault", "open")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "explicit_allow")

    def test_matrix_default_deny_when_action_not_granted_to_role(self) -> None:
        user = User.objects.create_user(email="partial@example.com", password="StrongPass123!")
        role = Role.objects.create(name="shipper")
        ap = AccessPermission.objects.create(resource="parcels", action="track")
        RolePermission.objects.create(role=role, access_permission=ap)
        UserRole.objects.create(user=user, role=role)
        decision = decide(user, "parcels", "reroute")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "default_deny")


@override_settings(REST_FRAMEWORK=_REST_FRAMEWORK_NO_THROTTLE)
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

    def test_patch_profile_updates_email(self) -> None:
        csrf_token = self._get_csrf_token()
        self.client.post(
            "/api/auth/register",
            {"email": "old@example.com", "password": "StrongPass123!"},
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
            {"email": "pw@example.com", "password": "StrongPass123!"},
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
            {"email": "del@example.com", "password": "StrongPass123!"},
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
            {"email": "stale@example.com", "password": "StrongPass123!"},
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


@override_settings(REST_FRAMEWORK=_REST_FRAMEWORK_NO_THROTTLE)
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
            {"email": "newuser@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=str(csrf),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_probe_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/admin-probe")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(REST_FRAMEWORK=_REST_FRAMEWORK_NO_THROTTLE)
class AdminApiTests(APITestCase):
    """
    B-H2: staff-only management APIs with `admin:manage` policy enforcement.
    """

    def _csrf(self) -> str:
        token = self.client.get("/api/auth/csrf").data["csrfToken"]
        return str(token)

    def test_admin_roles_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/admin/roles")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_roles_non_staff_returns_403(self) -> None:
        csrf = self._csrf()
        self.client.post(
            "/api/auth/register",
            {"email": "plain@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.client.post(
            "/api/auth/login",
            {"email": "plain@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        response = self.client.get("/api/auth/admin/roles")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_roles_staff_crud_and_grants(self) -> None:
        csrf = self._csrf()
        staff = User.objects.create_user(email="admin@example.com", password="StrongPass123!")
        staff.is_staff = True
        staff.save(update_fields=["is_staff"])
        self.client.post(
            "/api/auth/login",
            {"email": "admin@example.com", "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )

        existing_roles = self.client.get("/api/auth/admin/roles")
        self.assertEqual(existing_roles.status_code, status.HTTP_200_OK)
        self.assertIsInstance(existing_roles.data, list)

        created = self.client.post(
            "/api/auth/admin/roles",
            {"name": "support", "description": "Helpdesk"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        role_id = created.data["id"]

        perm = self.client.post(
            "/api/auth/admin/access-permissions",
            {"resource": "tickets", "action": "close"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(perm.status_code, status.HTTP_201_CREATED)
        perm_id = perm.data["id"]

        grant = self.client.post(
            f"/api/auth/admin/roles/{role_id}/permissions",
            {"access_permission_id": perm_id},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(grant.status_code, status.HTTP_201_CREATED)

        grant_again = self.client.post(
            f"/api/auth/admin/roles/{role_id}/permissions",
            {"access_permission_id": perm_id},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(grant_again.status_code, status.HTTP_200_OK)

        user_grant = self.client.post(
            f"/api/auth/admin/users/{staff.id}/roles",
            {"role_id": role_id},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(user_grant.status_code, status.HTTP_201_CREATED)

        revoke_perm = self.client.delete(
            f"/api/auth/admin/roles/{role_id}/permissions/{perm_id}",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(revoke_perm.status_code, status.HTTP_204_NO_CONTENT)

        revoke_user_role = self.client.delete(
            f"/api/auth/admin/users/{staff.id}/roles/{role_id}",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(revoke_user_role.status_code, status.HTTP_204_NO_CONTENT)

        policy_bad = self.client.post(
            "/api/auth/admin/policy-rules",
            {
                "resource": "demo",
                "action": "ping",
                "subject_type": AuthPolicyRule.SUBJECT_ROLE,
                "subject_value": "",
                "is_allowed": True,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(policy_bad.status_code, status.HTTP_400_BAD_REQUEST)

        policy_ok = self.client.post(
            "/api/auth/admin/policy-rules",
            {
                "resource": "demo",
                "action": "ping",
                "subject_type": AuthPolicyRule.SUBJECT_ANY,
                "subject_value": "",
                "is_allowed": True,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(policy_ok.status_code, status.HTTP_201_CREATED)


@override_settings(REST_FRAMEWORK=_REST_FRAMEWORK_NO_THROTTLE)
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

    def test_patch_me_403_when_explicit_user_deny_on_profile_update(self) -> None:
        csrf = self._csrf()
        self.client.post(
            "/api/auth/register",
            {"email": "nopatch@example.com", "password": "StrongPass123!"},
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
            {"email": "nologout@example.com", "password": "StrongPass123!"},
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


class DemoShowcaseSeedTests(TestCase):
    """
    AI Annotation:
    - Purpose: Lock in B-H3 migration seed — demo users, member binding, and policy outcomes.
    - Inputs: Test DB after migrations (includes `0008_seed_demo_showcase_users`).
    - Security notes: Asserts stable demo emails and policy behavior; password hashing is covered by migration + Django.
    """

    def test_demo_users_exist_with_expected_flags(self) -> None:
        member = User.objects.get(email="demo.member@example.com")
        self.assertTrue(member.is_active)
        self.assertFalse(member.is_staff)
        self.assertTrue(UserRole.objects.filter(user=member, role__name="member").exists())

        staff = User.objects.get(email="demo.staff@example.com")
        self.assertTrue(staff.is_staff)
        self.assertFalse(UserRole.objects.filter(user=staff).exists())

        plain = User.objects.get(email="demo.plain@example.com")
        self.assertFalse(plain.is_staff)
        self.assertFalse(UserRole.objects.filter(user=plain).exists())

    def test_demo_member_gets_widgets_list_via_matrix(self) -> None:
        user = User.objects.get(email="demo.member@example.com")
        decision = decide(user, "widgets", "list")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "matrix_allow")

    def test_demo_plain_denied_widgets_list(self) -> None:
        user = User.objects.get(email="demo.plain@example.com")
        decision = decide(user, "widgets", "list")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "default_deny")

    def test_demo_staff_allowed_admin_manage(self) -> None:
        user = User.objects.get(email="demo.staff@example.com")
        decision = decide(user, "admin", "manage")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "explicit_allow")


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


@override_settings(REST_FRAMEWORK=_REST_FRAMEWORK_NO_THROTTLE)
class AuditEventLoggingTests(APITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._register_throttle_classes = RegisterView.throttle_classes
        cls._login_throttle_classes = LoginView.throttle_classes
        RegisterView.throttle_classes = []
        LoginView.throttle_classes = []

    @classmethod
    def tearDownClass(cls) -> None:
        RegisterView.throttle_classes = cls._register_throttle_classes
        LoginView.throttle_classes = cls._login_throttle_classes
        super().tearDownClass()

    def _csrf(self) -> str:
        r = self.client.get("/api/auth/csrf")
        return str(r.data["csrfToken"])

    def test_register_emits_audit_json(self) -> None:
        csrf = self._csrf()
        with self.assertLogs("accounts.audit", level="INFO") as captured:
            self.client.post(
                "/api/auth/register",
                {"email": "audit1@example.com", "password": "StrongPass123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        events = [getattr(r, "audit", {}).get("event") for r in captured.records]
        self.assertIn("auth.register_success", events)
        reg = next(r.audit for r in captured.records if getattr(r, "audit", {}).get("event") == "auth.register_success")
        self.assertIn("correlation_id", reg)

    def test_login_success_and_failure_emit_audit(self) -> None:
        User.objects.create_user(email="audit2@example.com", password="StrongPass123!")
        csrf = self._csrf()

        with self.assertLogs("accounts.audit", level="INFO") as captured:
            self.client.post(
                "/api/auth/login",
                {"email": "audit2@example.com", "password": "WrongPass123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        fail_events = [getattr(r, "audit", {}).get("event") for r in captured.records]
        self.assertIn("auth.login_failure", fail_events)

        with self.assertLogs("accounts.audit", level="INFO") as captured:
            self.client.post(
                "/api/auth/login",
                {"email": "audit2@example.com", "password": "StrongPass123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        ok_events = [getattr(r, "audit", {}).get("event") for r in captured.records]
        self.assertIn("auth.login_success", ok_events)


class AuditJsonFormatterUnitTests(TestCase):
    def test_formatter_outputs_json_with_audit_extra(self) -> None:
        fmt = AuditJsonFormatter()
        record = logging.LogRecord(
            name="accounts.audit",
            level=logging.INFO,
            pathname="x",
            lineno=1,
            msg="audit",
            args=(),
            exc_info=None,
        )
        record.audit = {"event": "test.event", "correlation_id": "cid", "actor_id": None}
        line = fmt.format(record)
        data = json.loads(line)
        self.assertEqual(data["event"], "test.event")
        self.assertEqual(data["correlation_id"], "cid")
        self.assertIn("timestamp", data)
