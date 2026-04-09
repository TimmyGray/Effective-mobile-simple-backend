import json
import logging

from django.test import TestCase

from accounts.logging_formatters import AuditJsonFormatter


class AuditJsonFormatterUnitTests(TestCase):
    def test_formatter_outputs_json_with_audit_extra(self) -> None:
        fmt = AuditJsonFormatter()
        record = logging.LogRecord(
            name="accounts.audit",
            level=logging.INFO,
            pathname="x",
            lineno=1,
            msg="audit",
            args=(),
            exc_info=None,
        )
        record.audit = {"event": "test.event", "correlation_id": "cid", "actor_id": None}
        line = fmt.format(record)
        data = json.loads(line)
        self.assertEqual(data["event"], "test.event")
        self.assertEqual(data["correlation_id"], "cid")
        self.assertIn("timestamp", data)
