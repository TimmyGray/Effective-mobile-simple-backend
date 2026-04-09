from django.contrib.auth import logout
from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """
    Return a WWW-Authenticate header so DRF uses 401 (not 403)
    for unauthenticated requests on protected endpoints.
    """

    def authenticate_header(self, request) -> str:
        return "Session"

    def authenticate(self, request):
        """
        AI Annotation:
        - Purpose: Resolve session user and treat inactive accounts as unauthenticated.
        - Inputs: Django request with optional session user.
        - Outputs: User tuple or None; inactive users trigger logout and None.
        - Side effects: Calls `logout` to flush session when stored user is soft-deactivated.
        - Security notes: Prevents API access with a stale session after `is_active=False`.
        """
        result = super().authenticate(request)
        if result is None:
            return None
        user, _auth = result
        if not user.is_active:
            logout(request)
            return None
        return result
