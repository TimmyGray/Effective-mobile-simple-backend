from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.models import AccessPermission, AuthPolicyRule, Role, RolePermission, UserRole
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
