from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class AuditJsonFormatter(logging.Formatter):
    """
    AI Annotation:
    - Purpose: Render audit LogRecords as single-line JSON for aggregation and search.
    - Inputs: LogRecord with an `audit` dict supplied via logging `extra`.
    - Outputs: JSON string with UTC ISO8601 timestamp; defers to base formatter otherwise.
    - Failure modes: Non-audit records fall back to the parent Formatter implementation.
    """

    def format(self, record: logging.LogRecord) -> str:
        audit = getattr(record, "audit", None)
        if isinstance(audit, dict):
            ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            payload = {"timestamp": ts, "level": record.levelname, **audit}
            return json.dumps(payload, default=str, sort_keys=True)
        return super().format(record)
