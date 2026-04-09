from __future__ import annotations

from rest_framework import serializers

from accounts.models import AccessPermission, AuthPolicyRule, Role


class RoleSerializer(serializers.ModelSerializer[Role]):
    class Meta:
        model = Role
        fields = ("id", "name", "description")


class AccessPermissionSerializer(serializers.ModelSerializer[AccessPermission]):
    class Meta:
        model = AccessPermission
        fields = ("id", "resource", "action")


class AuthPolicyRuleSerializer(serializers.ModelSerializer[AuthPolicyRule]):
    class Meta:
        model = AuthPolicyRule
        fields = (
            "id",
            "resource",
            "action",
            "subject_type",
            "subject_value",
            "is_allowed",
        )

    def validate(self, attrs: dict) -> dict:
        """
        AI Annotation:
        - Purpose: Enforce subject_value presence for subject-specific rule types.
        - Failure modes: ValidationError when user/role selectors are empty.
        """
        subject_type = attrs.get("subject_type", getattr(self.instance, "subject_type", None))
        subject_value = attrs.get("subject_value", getattr(self.instance, "subject_value", ""))
        if subject_type in (AuthPolicyRule.SUBJECT_USER, AuthPolicyRule.SUBJECT_ROLE):
            if not (subject_value or "").strip():
                raise serializers.ValidationError(
                    {"subject_value": "Required for user- and role-scoped rules."},
                )
        return attrs


class GrantAccessPermissionToRoleSerializer(serializers.Serializer):
    access_permission_id = serializers.IntegerField(min_value=1)

    def validate_access_permission_id(self, value: int) -> int:
        if not AccessPermission.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Access permission does not exist.")
        return value


class GrantRoleToUserSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(min_value=1)

    def validate_role_id(self, value: int) -> int:
        if not Role.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Role does not exist.")
        return value
