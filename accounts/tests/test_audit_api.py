from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from accounts.tests.constants import REST_FRAMEWORK_NO_THROTTLE
from accounts.views import LoginView, RegisterView

User = get_user_model()


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_NO_THROTTLE)
class AuditEventLoggingTests(APITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._register_throttle_classes = RegisterView.throttle_classes
        cls._login_throttle_classes = LoginView.throttle_classes
        RegisterView.throttle_classes = []
        LoginView.throttle_classes = []

    @classmethod
    def tearDownClass(cls) -> None:
        RegisterView.throttle_classes = cls._register_throttle_classes
        LoginView.throttle_classes = cls._login_throttle_classes
        super().tearDownClass()

    def _csrf(self) -> str:
        r = self.client.get("/api/auth/csrf")
        return str(r.data["csrfToken"])

    def test_register_emits_audit_json(self) -> None:
        csrf = self._csrf()
        with self.assertLogs("accounts.audit", level="INFO") as captured:
            self.client.post(
                "/api/auth/register",
                {"email": "audit1@example.com", "password": "StrongPass123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        events = [getattr(r, "audit", {}).get("event") for r in captured.records]
        self.assertIn("auth.register_success", events)
        reg = next(r.audit for r in captured.records if getattr(r, "audit", {}).get("event") == "auth.register_success")
        self.assertIn("correlation_id", reg)

    def test_login_success_and_failure_emit_audit(self) -> None:
        User.objects.create_user(email="audit2@example.com", password="StrongPass123!")
        csrf = self._csrf()

        with self.assertLogs("accounts.audit", level="INFO") as captured:
            self.client.post(
                "/api/auth/login",
                {"email": "audit2@example.com", "password": "WrongPass123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        fail_events = [getattr(r, "audit", {}).get("event") for r in captured.records]
        self.assertIn("auth.login_failure", fail_events)

        with self.assertLogs("accounts.audit", level="INFO") as captured:
            self.client.post(
                "/api/auth/login",
                {"email": "audit2@example.com", "password": "StrongPass123!"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        ok_events = [getattr(r, "audit", {}).get("event") for r in captured.records]
        self.assertIn("auth.login_success", ok_events)
