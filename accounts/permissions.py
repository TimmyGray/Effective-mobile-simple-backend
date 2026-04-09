from rest_framework.permissions import BasePermission

from accounts.policy import is_allowed


class PolicyPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "policy_action", None)
        if not resource or not action:
            return False
        return is_allowed(request.user, resource, action)
