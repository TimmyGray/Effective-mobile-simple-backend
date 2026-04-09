from django.contrib.auth import get_user_model

from accounts.models import AuthPolicyRule


User = get_user_model()


def is_allowed(user: User, resource: str, action: str) -> bool:
    if not user.is_authenticated or not user.is_active:
        return False
    rule = AuthPolicyRule.objects.filter(
        resource=resource,
        action=action,
        is_allowed=True,
    ).first()
    return rule is not None
