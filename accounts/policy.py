from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model

from accounts.models import AuthPolicyRule


User = get_user_model()


@dataclass(frozen=True)
class PolicyDecision:
    """
    AI Annotation:
    - Purpose: Capture the outcome of a centralized (user, resource, action) policy evaluation.
    - Inputs: Built by `decide()`; `reason` is a stable diagnostic code for tests and logs.
    - Outputs: Immutable record consumed by permissions and optional auditing.
    - Security notes: Does not embed secrets; safe to log at info level when debugging authz.
    """

    allowed: bool
    reason: str


def _user_roles(user: User) -> list[str]:
    """
    AI Annotation:
    - Purpose: Map Django user privilege flags to policy role keys used in `AuthPolicyRule`.
    - Inputs: Authenticated user instance.
    - Outputs: List of role strings evaluated by role-scoped rules.
    """

    roles: list[str] = []
    if user.is_staff:
        roles.append("staff")
    if user.is_superuser:
        roles.append("superuser")
    return roles


def _rule_applies(rule: AuthPolicyRule, user: User) -> bool:
    """
    AI Annotation:
    - Purpose: Determine whether a single policy row applies to the given user.
    - Inputs: Persisted rule row and authenticated user.
    - Outputs: True when the rule's subject selector matches the user.
    - Failure modes: Returns False for unknown subject types to avoid accidental allow.
    """

    if rule.subject_type == AuthPolicyRule.SUBJECT_ANY:
        return True
    if rule.subject_type == AuthPolicyRule.SUBJECT_USER:
        return bool(user.email) and user.email == rule.subject_value
    if rule.subject_type == AuthPolicyRule.SUBJECT_ROLE:
        return rule.subject_value in _user_roles(user)
    return False


def decide(user: User, resource: str, action: str) -> PolicyDecision:
    """
    AI Annotation:
    - Purpose: Central policy decision point for `(user, resource, action)` checks.
    - Inputs: Authenticated user plus non-empty resource/action keys matching view metadata.
    - Outputs: `PolicyDecision` with allow/deny outcome and a stable reason code.
    - Side effects: Reads policy rows from the database (no writes).
    - Failure modes: Inactive or anonymous users are denied without consulting allow rules.
    - Security notes: Explicit deny rules are evaluated before allow rules; default is deny.
    """

    if not user.is_authenticated or not user.is_active:
        return PolicyDecision(False, "unauthenticated_or_inactive")
    if not resource or not action:
        return PolicyDecision(False, "invalid_resource_action")

    rules = list(AuthPolicyRule.objects.filter(resource=resource, action=action))
    denies = [r for r in rules if not r.is_allowed]
    allows = [r for r in rules if r.is_allowed]

    for rule in denies:
        if _rule_applies(rule, user):
            return PolicyDecision(False, "explicit_deny")

    for rule in allows:
        if _rule_applies(rule, user):
            return PolicyDecision(True, "explicit_allow")

    return PolicyDecision(False, "default_deny")


def is_allowed(user: User, resource: str, action: str) -> bool:
    """
    AI Annotation:
    - Purpose: Boolean facade for permissions classes and legacy call sites.
    - Inputs: Same as `decide()`; requires authenticated active user for True.
    - Outputs: True only when `decide()` returns an allowed outcome.
    - Security notes: Delegates to `decide()` so deny/allow precedence stays centralized.
    """

    return decide(user, resource, action).allowed
