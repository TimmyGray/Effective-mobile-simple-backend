from django.contrib.auth import get_user_model

from accounts.models import AuthPolicyRule


User = get_user_model()


def is_allowed(user: User, resource: str, action: str) -> bool:
    """
    AI Annotation:
    - Purpose: Evaluate centralized allow rules for a user/resource/action tuple.
    - Inputs: Requires an authenticated active user plus non-empty resource/action keys.
    - Outputs: Returns True on first matching allow rule; otherwise False (deny by default).
    - Security notes: Applies global, user, and role-based policy checks in precedence order.
    """
    if not user.is_authenticated or not user.is_active:
        return False
    if AuthPolicyRule.objects.filter(
        resource=resource,
        action=action,
        subject_type=AuthPolicyRule.SUBJECT_ANY,
        is_allowed=True,
    ).exists():
        return True
    if AuthPolicyRule.objects.filter(
        resource=resource,
        action=action,
        subject_type=AuthPolicyRule.SUBJECT_USER,
        subject_value=user.email,
        is_allowed=True,
    ).exists():
        return True
    roles: list[str] = []
    if user.is_staff:
        roles.append("staff")
    if user.is_superuser:
        roles.append("superuser")
    if roles and AuthPolicyRule.objects.filter(
        resource=resource,
        action=action,
        subject_type=AuthPolicyRule.SUBJECT_ROLE,
        subject_value__in=roles,
        is_allowed=True,
    ).exists():
        return True
    return False
