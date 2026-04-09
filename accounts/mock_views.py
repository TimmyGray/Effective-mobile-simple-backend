from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import EnforcedAuthzPermission


class WidgetsListView(APIView):
    """
    AI Annotation:
    - Purpose: Provide a mock business resource list protected by the custom authz system.
    - Inputs: Authenticated request evaluated against `widgets:list` policy.
    - Outputs: Static list payload suitable for demoing 200/401/403 behavior.
    - Security notes: Uses global EnforcedAuthzPermission with explicit policy metadata.
    """

    permission_classes = [EnforcedAuthzPermission]
    policy_resource = "widgets"
    policy_action = "list"

    def get(self, request: Request) -> Response:
        """
        AI Annotation:
        - Purpose: Return a deterministic list of mock business objects.
        - Outputs: JSON array of placeholder widgets with stable IDs/names for demos.
        """
        return Response(
            {
                "items": [
                    {"id": "w-100", "name": "Acme Widget"},
                    {"id": "w-200", "name": "Turbo Widget"},
                    {"id": "w-300", "name": "Nano Widget"},
                ]
            },
            status=status.HTTP_200_OK,
        )
