from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import AuthPolicyRule
from accounts.tests.constants import REST_FRAMEWORK_NO_THROTTLE

User = get_user_model()


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_NO_THROTTLE)
class AdminApiTests(APITestCase):
    """
    B-H2: staff-only management APIs with `admin:manage` policy enforcement.
    """

    def _csrf(self) -> str:
        token = self.client.get("/api/auth/csrf").data["csrfToken"]
        return str(token)

    def _registration_payload(self, email: str) -> dict[str, str]:
        return {
            "email": email,
            "first_name": "Plain",
            "last_name": "User",
            "middle_name": "Member",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

    def test_admin_roles_unauthenticated_returns_401(self) -> None:
        response = self.client.get("/api/auth/admin/roles")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_roles_non_staff_returns_403(self) -> None:
        csrf = self._csrf()
        self.client.post(
            "/api/auth/register",
            self._registration_payload("plain@example.com"),
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
