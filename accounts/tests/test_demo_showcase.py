from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import UserRole
from accounts.policy import decide

User = get_user_model()


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
