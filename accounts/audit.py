from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from django.http import HttpRequest

AUDIT_LOGGER_NAME = "accounts.audit"

logger = logging.getLogger(AUDIT_LOGGER_NAME)

_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


def normalize_correlation_id(raw: str) -> str | None:
    """
    AI Annotation:
    - Purpose: Accept only safe client-supplied correlation ids for request tracing.
    - Inputs: Raw header value; empty or invalid shapes return None.
    - Outputs: Normalized string or None so middleware can generate a UUID.
    """
    s = (raw or "").strip()
    if not s:
        return None
    if _CORRELATION_ID_PATTERN.fullmatch(s):
        return s
    return None


def get_correlation_id(request: HttpRequest) -> str:
    """Return the correlation id bound by CorrelationIdMiddleware, or empty string."""
    return getattr(request, "correlation_id", None) or ""


def emit_audit_event(request: HttpRequest, event: str, **fields: Any) -> None:
    """
    AI Annotation:
    - Purpose: Emit one structured audit record for authentication or policy-admin actions.
    - Inputs: Django request (correlation + actor); event name; optional scalar metadata.
    - Outputs: Writes JSON via the `accounts.audit` logger (no return value).
    - Side effects: Emits one INFO log line; safe for request/response path.
    - Security notes: Never pass passwords, tokens, or secret headers; prefer opaque ids.
    """
    actor_id: int | None = None
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        actor_id = user.pk

    payload: dict[str, Any] = {
        "event": event,
        "correlation_id": get_correlation_id(request),
        "actor_id": actor_id,
        **fields,
    }
    logger.info("audit", extra={"audit": payload})


def new_correlation_id() -> str:
    """Generate a new correlation id when the client does not supply a valid one."""
    return str(uuid.uuid4())
