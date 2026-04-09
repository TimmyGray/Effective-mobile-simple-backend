from django.contrib.auth import get_user_model


User = get_user_model()

POLICY_RULES: dict[str, set[str]] = {
    "auth": {"logout", "me"},
}


def is_allowed(user: User, resource: str, action: str) -> bool:
    if not user.is_authenticated or not user.is_active:
        return False
    allowed_actions = POLICY_RULES.get(resource, set())
    return action in allowed_actions
