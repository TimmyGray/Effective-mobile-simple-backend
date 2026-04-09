"""
Kubernetes-style liveness and readiness probes for operations.

AI Annotation (module):
- Purpose: Expose unauthenticated HTTP endpoints for orchestrator health checks.
- Security notes: Intentionally public; return only non-sensitive status metadata.
"""

from __future__ import annotations

import logging

from django.db import connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


def health_live(request: HttpRequest) -> JsonResponse:
    """
    AI Annotation:
    - Purpose: Report that the process accepts HTTP (liveness).
    - Outputs: JSON with status ok and HTTP 200.
    - Side effects: None.
    - Failure modes: None under normal WSGI/ASGI operation.
    """
    _ = request
    return JsonResponse({"status": "ok"})


def health_ready(request: HttpRequest) -> JsonResponse:
    """
    AI Annotation:
    - Purpose: Verify the default database connection is usable (readiness).
    - Inputs: Uses Django's configured DATABASES['default'].
    - Outputs: JSON with status ok and 200, or 503 if the DB is unreachable.
    - Side effects: Opens/uses a DB connection (may hit connection pool).
    - Failure modes: Returns 503 when ensure_connection raises (network, auth, etc.).
    """
    _ = request
    try:
        connection.ensure_connection()
    except Exception:
        logger.exception("health_ready: database connection failed")
        return JsonResponse(
            {"status": "unavailable", "detail": "database_unavailable"},
            status=503,
        )
    return JsonResponse({"status": "ok"})
