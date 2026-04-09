from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from accounts.audit import new_correlation_id, normalize_correlation_id

_HEADER_IN = "HTTP_X_CORRELATION_ID"
_HEADER_OUT = "X-Correlation-ID"


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    AI Annotation:
    - Purpose: Bind a per-request correlation id for audit logs and downstream tracing.
    - Inputs: Optional `X-Correlation-ID` header (validated); otherwise a new UUID.
    - Outputs: Sets `request.correlation_id` and echoes the id on every response.
    - Side effects: Mutates request/response only; no I/O beyond header handling.
    """

    def process_request(self, request: HttpRequest) -> None:
        raw = request.META.get(_HEADER_IN, "")
        cid = normalize_correlation_id(raw)
        if cid is None:
            cid = new_correlation_id()
        request.correlation_id = cid

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        cid = getattr(request, "correlation_id", None)
        if cid:
            response[_HEADER_OUT] = cid
        return response
