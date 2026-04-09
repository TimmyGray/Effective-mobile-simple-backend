from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.admin_serializers import (
    AccessPermissionSerializer,
    AuthPolicyRuleSerializer,
    GrantAccessPermissionToRoleSerializer,
    GrantRoleToUserSerializer,
    RoleSerializer,
)
from accounts.audit import emit_audit_event
from accounts.models import AccessPermission, AuthPolicyRule, Role, RolePermission, UserRole
from accounts.permissions import EnforcedAuthzPermission, IsStaffUser

User = get_user_model()


class AdminAPIMixin:
    """
    AI Annotation:
    - Purpose: Shared authz wiring for privileged admin management endpoints.
    - Security notes: Requires session-authenticated staff plus explicit `admin:manage` policy.
    """

    permission_classes = [EnforcedAuthzPermission, IsStaffUser]
    policy_resource = "admin"
    policy_action = "manage"


class AdminRoleListCreateView(AdminAPIMixin, APIView):
    def get(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: List persisted security roles for admin consoles and policy tooling.
        - Outputs: Ordered list of role records.
        """
        roles = Role.objects.order_by("name")
        return Response(RoleSerializer(roles, many=True).data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Create a named role for later user bindings and matrix grants.
        - Side effects: Inserts a `Role` row when validation passes.
        """
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        emit_audit_event(
            request,
            "admin.role_create",
            role_id=role.id,
            role_name=role.name,
        )
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class AdminRoleDetailView(AdminAPIMixin, APIView):
    def get(self, request: Request, pk: int) -> Response:
        role = get_object_or_404(Role, pk=pk)
        return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pk: int) -> Response:
        role = get_object_or_404(Role, pk=pk)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        emit_audit_event(request, "admin.role_update", role_id=role.id)
        return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pk: int) -> Response:
        """
        AI Annotation:
        - Purpose: Remove a role and dependent grants via cascading deletes.
        - Failure modes: Returns 400 when dependent policy rows still reference the role name.
        """
        role = get_object_or_404(Role, pk=pk)
        if AuthPolicyRule.objects.filter(
            subject_type=AuthPolicyRule.SUBJECT_ROLE,
            subject_value=role.name,
        ).exists():
            return Response(
                {"detail": "Cannot delete role while AuthPolicyRule rows reference this role name."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emit_audit_event(request, "admin.role_delete", role_id=role.id, role_name=role.name)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminAccessPermissionListCreateView(AdminAPIMixin, APIView):
    def get(self, request: Request) -> Response:
        perms = AccessPermission.objects.order_by("resource", "action")
        return Response(AccessPermissionSerializer(perms, many=True).data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = AccessPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perm = serializer.save()
        emit_audit_event(
            request,
            "admin.access_permission_create",
            access_permission_id=perm.id,
            resource=perm.resource,
            action=perm.action,
        )
        return Response(AccessPermissionSerializer(perm).data, status=status.HTTP_201_CREATED)


class AdminAccessPermissionDetailView(AdminAPIMixin, APIView):
    def get(self, request: Request, pk: int) -> Response:
        perm = get_object_or_404(AccessPermission, pk=pk)
        return Response(AccessPermissionSerializer(perm).data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pk: int) -> Response:
        perm = get_object_or_404(AccessPermission, pk=pk)
        serializer = AccessPermissionSerializer(perm, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        emit_audit_event(request, "admin.access_permission_update", access_permission_id=perm.id)
        return Response(AccessPermissionSerializer(perm).data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pk: int) -> Response:
        perm = get_object_or_404(AccessPermission, pk=pk)
        emit_audit_event(request, "admin.access_permission_delete", access_permission_id=perm.id)
        perm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminRolePermissionGrantView(AdminAPIMixin, APIView):
    def post(self, request: Request, role_id: int) -> Response:
        """
        AI Annotation:
        - Purpose: Grant an access permission to a role (idempotent when already granted).
        - Side effects: Creates `RolePermission` row when missing.
        """
        role = get_object_or_404(Role, pk=role_id)
        grant_serializer = GrantAccessPermissionToRoleSerializer(data=request.data)
        grant_serializer.is_valid(raise_exception=True)
        ap_id = grant_serializer.validated_data["access_permission_id"]
        access_permission = get_object_or_404(AccessPermission, pk=ap_id)
        _, created = RolePermission.objects.get_or_create(
            role=role,
            access_permission=access_permission,
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        emit_audit_event(
            request,
            "admin.role_permission_grant",
            role_id=role.id,
            access_permission_id=access_permission.id,
            created=created,
        )
        return Response(
            {
                "role_id": role.id,
                "access_permission_id": access_permission.id,
                "created": created,
            },
            status=status_code,
        )

    def delete(self, request: Request, role_id: int, permission_id: int) -> Response:
        role = get_object_or_404(Role, pk=role_id)
        access_permission = get_object_or_404(AccessPermission, pk=permission_id)
        deleted, _ = RolePermission.objects.filter(
            role=role,
            access_permission=access_permission,
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        emit_audit_event(
            request,
            "admin.role_permission_revoke",
            role_id=role.id,
            access_permission_id=access_permission.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserRoleGrantView(AdminAPIMixin, APIView):
    def post(self, request: Request, user_id: int) -> Response:
        """
        AI Annotation:
        - Purpose: Bind a user to a named role for policy evaluation.
        - Side effects: Creates `UserRole` when missing; idempotent grant returns 200.
        """
        target = get_object_or_404(User, pk=user_id)
        grant_serializer = GrantRoleToUserSerializer(data=request.data)
        grant_serializer.is_valid(raise_exception=True)
        role = get_object_or_404(Role, pk=grant_serializer.validated_data["role_id"])
        with transaction.atomic():
            _, created = UserRole.objects.get_or_create(user=target, role=role)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        emit_audit_event(
            request,
            "admin.user_role_grant",
            target_user_id=target.id,
            role_id=role.id,
            created=created,
        )
        return Response(
            {"user_id": target.id, "role_id": role.id, "created": created},
            status=status_code,
        )

    def delete(self, request: Request, user_id: int, role_id: int) -> Response:
        target = get_object_or_404(User, pk=user_id)
        role = get_object_or_404(Role, pk=role_id)
        deleted, _ = UserRole.objects.filter(user=target, role=role).delete()
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        emit_audit_event(
            request,
            "admin.user_role_revoke",
            target_user_id=target.id,
            role_id=role.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminPolicyRuleListCreateView(AdminAPIMixin, APIView):
    def get(self, request: Request) -> Response:
        rules = AuthPolicyRule.objects.order_by("resource", "action", "pk")
        return Response(AuthPolicyRuleSerializer(rules, many=True).data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = AuthPolicyRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        emit_audit_event(request, "admin.policy_rule_create", policy_rule_id=rule.id)
        return Response(AuthPolicyRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class AdminPolicyRuleDetailView(AdminAPIMixin, APIView):
    def get(self, request: Request, pk: int) -> Response:
        rule = get_object_or_404(AuthPolicyRule, pk=pk)
        return Response(AuthPolicyRuleSerializer(rule).data, status=status.HTTP_200_OK)

    def patch(self, request: Request, pk: int) -> Response:
        rule = get_object_or_404(AuthPolicyRule, pk=pk)
        serializer = AuthPolicyRuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        emit_audit_event(request, "admin.policy_rule_update", policy_rule_id=rule.id)
        return Response(AuthPolicyRuleSerializer(rule).data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pk: int) -> Response:
        rule = get_object_or_404(AuthPolicyRule, pk=pk)
        emit_audit_event(request, "admin.policy_rule_delete", policy_rule_id=rule.id)
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
