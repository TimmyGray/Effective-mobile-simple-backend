from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.audit import emit_audit_event
from accounts.permissions import EnforcedAuthzPermission
from accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    auth_public = True
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Register a new user account through validated serializer input.
        - Inputs: Accepts request payload with registration fields expected by RegisterSerializer.
        - Outputs: Returns serialized user identity and HTTP 201 on successful creation.
        - Side effects: Creates a persisted user record with hashed credentials.
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        emit_audit_event(request, "auth.register_success", user_id=user.pk)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    auth_public = True
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Authenticate a user and start a server-side session.
        - Inputs: Requires login credentials validated by LoginSerializer.
        - Outputs: Returns authenticated user payload and HTTP 200.
        - Security notes: Session state is established only after credential validation passes.
        """
        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            emit_audit_event(request, "auth.login_failure", reason="invalid_credentials")
            raise
        user = serializer.validated_data["user"]
        login(request, user)
        emit_audit_event(request, "auth.login_success", user_id=user.pk)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    policy_resource = "auth"
    policy_action = "logout"

    def post(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Terminate the current authenticated session.
        - Inputs: Requires an authenticated request authorized for `auth:logout`.
        - Outputs: Returns HTTP 204 with empty body on successful logout.
        - Side effects: Invalidates session authentication artifacts for the current request.
        """
        emit_audit_event(request, "auth.logout")
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    policy_resource = "auth"

    @property
    def policy_action(self) -> str:
        """
        AI Annotation:
        - Purpose: Map HTTP method to distinct auth policy actions on the same URL.
        - Inputs: `self.request.method` set before permission checks.
        - Outputs: Policy action key for `auth` resource.
        - Security notes: Separates read, update, and account-deactivation permissions.
        """
        method = self.request.method.upper()
        if method == "PATCH":
            return "profile_update"
        if method == "DELETE":
            return "account_deactivate"
        return "me"

    def get(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Return the current authenticated user's profile projection.
        - Inputs: Uses request.user resolved by authentication middleware.
        - Outputs: Serialized user identity data with HTTP 200.
        - Security notes: Access depends on centralized authz permission with explicit policy action.
        """
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Update the authenticated user's profile fields and optional password.
        - Inputs: JSON body validated by UserProfileUpdateSerializer (partial).
        - Outputs: Updated user JSON with HTTP 200.
        - Side effects: Writes user row; may re-hash password.
        - Security notes: Requires `auth:profile_update` policy; password change needs current password.
        """
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        emit_audit_event(request, "auth.profile_update", user_id=user.pk)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Soft-delete the current account and end the session immediately.
        - Inputs: Authenticated DELETE; no body required.
        - Outputs: HTTP 204 empty body.
        - Side effects: Sets `is_active=False`, saves user, calls `logout` to revoke session.
        - Security notes: Requires `auth:account_deactivate`; user cannot authenticate afterward.
        """
        user = request.user
        emit_audit_event(request, "auth.account_deactivate", user_id=user.pk)
        user.is_active = False
        user.save(update_fields=["is_active"])
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProbeView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    policy_resource = "auth"
    policy_action = "admin_probe"

    def get(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Provide a minimal protected endpoint for admin-policy probing.
        - Inputs: Requires an authenticated request authorized for `auth:admin_probe`.
        - Outputs: Returns static OK payload when authorization passes.
        - Security notes: Useful to verify 401/403 semantics and policy wiring.
        """
        return Response({"ok": True}, status=status.HTTP_200_OK)


class CsrfTokenView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    auth_public = True

    def get(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Issue CSRF token for clients before state-changing requests.
        - Inputs: Public GET request; relies on Django CSRF middleware internals.
        - Outputs: Returns CSRF token value in JSON response with HTTP 200.
        - Security notes: Supports CSRF protection flow without exposing sensitive session data.
        """
        token = get_token(request)
        return Response({"csrfToken": token}, status=status.HTTP_200_OK)
