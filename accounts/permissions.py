from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission

from accounts.policy import is_allowed


class IsStaffUser(BasePermission):
    """
    AI Annotation:
    - Purpose: Restrict endpoints to Django staff/superuser accounts (operational admin boundary).
    - Inputs: `request.user` from session or auth.
    - Outputs: True when user is authenticated and staff or superuser.
    - Security notes: Composed with `EnforcedAuthzPermission` so policy must also allow access.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)),
        )


class PolicyPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        """
        AI Annotation:
        - Purpose: Apply policy-based authorization for views that expose resource/action metadata.
        - Inputs: Expects request.user and view attributes `policy_resource` and `policy_action`.
        - Outputs: Returns True when allowed; otherwise raises DRF auth exceptions (401/403).
        - Failure modes: Missing policy metadata raises PermissionDenied (403).
        - Security notes: Unauthenticated callers raise NotAuthenticated (401) before policy checks.
        """
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "policy_action", None)
        if not resource or not action:
            raise PermissionDenied()
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        if not is_allowed(request.user, resource, action):
            raise PermissionDenied()
        return True


class EnforcedAuthzPermission(BasePermission):
    """
    Global deny-by-default permission.
    Public endpoints must opt in via `auth_public = True`.
    Protected endpoints must define `policy_resource` and `policy_action`.
    """

    def has_permission(self, request, view) -> bool:
        """
        AI Annotation:
        - Purpose: Enforce global deny-by-default access control for all API views.
        - Inputs: Uses optional `auth_public` plus required `policy_resource`/`policy_action`.
        - Outputs: Returns True for public or allowed requests; raises DRF exceptions otherwise.
        - Failure modes: Missing view policy metadata raises PermissionDenied (misconfiguration).
        - Security notes: Unauthenticated access raises NotAuthenticated (401); failed policy raises
          PermissionDenied (403). Explicit exceptions avoid relying on DRF `permission_denied` heuristics.
        """
        if getattr(view, "auth_public", False):
            return True
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "policy_action", None)
        if not resource or not action:
            raise PermissionDenied()
        if not is_allowed(request.user, resource, action):
            raise PermissionDenied()
        return True
