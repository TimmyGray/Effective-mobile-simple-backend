from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """
    Return a WWW-Authenticate header so DRF uses 401 (not 403)
    for unauthenticated requests on protected endpoints.
    """

    def authenticate_header(self, request) -> str:
        return "Session"
