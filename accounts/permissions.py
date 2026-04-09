from rest_framework.permissions import BasePermission

from accounts.policy import is_allowed


class PolicyPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "policy_action", None)
        if not resource or not action:
            return False
        return is_allowed(request.user, resource, action)


class EnforcedAuthzPermission(BasePermission):
    """
    Global deny-by-default permission.
    Public endpoints must opt in via `auth_public = True`.
    Protected endpoints must define `policy_resource` and `policy_action`.
    """

    def has_permission(self, request, view) -> bool:
        if getattr(view, "auth_public", False):
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "policy_action", None)
        if not resource or not action:
            return False
        return is_allowed(request.user, resource, action)
