from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import EnforcedAuthzPermission
from accounts.serializers import LoginSerializer, RegisterSerializer, UserSerializer


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
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
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
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [EnforcedAuthzPermission]
    policy_resource = "auth"
    policy_action = "me"

    def get(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Return the current authenticated user's profile projection.
        - Inputs: Uses request.user resolved by authentication middleware.
        - Outputs: Serialized user identity data with HTTP 200.
        - Security notes: Access depends on centralized authz permission with explicit policy action.
        """
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


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
