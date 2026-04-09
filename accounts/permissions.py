from rest_framework.permissions import BasePermission

from accounts.policy import is_allowed


class PolicyPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        """
        AI Annotation:
        - Purpose: Apply policy-based authorization for views that expose resource/action metadata.
        - Inputs: Expects request.user and view attributes `policy_resource` and `policy_action`.
        - Outputs: Returns boolean authorization decision from centralized policy evaluator.
        - Failure modes: Missing policy metadata causes an immediate deny.
        """
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
        """
        AI Annotation:
        - Purpose: Enforce global deny-by-default access control for all API views.
        - Inputs: Uses optional `auth_public` plus required `policy_resource`/`policy_action`.
        - Outputs: Returns True only for explicit public access or positive policy decisions.
        - Security notes: Prevents accidental exposure by denying anonymous or unannotated views.
        """
        if getattr(view, "auth_public", False):
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "policy_action", None)
        if not resource or not action:
            return False
        return is_allowed(request.user, resource, action)
