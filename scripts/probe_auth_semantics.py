"""
CLI probes for 401 vs 403 semantics against a running dev server.

AI Annotation:
- Purpose: Give operators a quick, labeled check that unauthenticated calls get 401 and
  authenticated-but-forbidden admin calls get 403, matching project auth conventions.
- Inputs: Optional base URL as argv[1]; defaults to http://127.0.0.1:8000.
- Outputs: Prints each step and expected status; exits 0 on match, 1 on mismatch or error.
- Side effects: HTTP requests only; registers a throwaway user when probing 403.
- Failure modes: Connection errors or unexpected status codes fail the run.
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass
from http.cookiejar import CookieJar
from urllib import error, request


@dataclass
class ResponseData:
    status: int
    body: dict | list | str | None


def api_call(
    opener: request.OpenerDirector,
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> ResponseData:
    """
    AI Annotation:
    - Purpose: Perform JSON HTTP calls with cookie handling via the given opener.
    - Outputs: Parsed JSON body when possible; raw string on decode failure.
    """
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=data, headers=request_headers, method=method)
    try:
        with opener.open(req) as resp:
            raw = resp.read().decode("utf-8") if resp.length != 0 else ""
            parsed = _parse_body(raw)
            return ResponseData(status=resp.status, body=parsed)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.length != 0 else ""
        parsed = _parse_body(raw)
        return ResponseData(status=exc.code, body=parsed)


def _parse_body(raw: str) -> dict | list | str | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    base_url = base_url.rstrip("/")
    auth_base = f"{base_url}/api/auth"

    # Fresh opener with no cookies — probe 401 on protected route.
    bare_opener = request.build_opener()
    me_bare = api_call(bare_opener, "GET", f"{auth_base}/me")
    print(f"GET /api/auth/me (no session) -> {me_bare.status} (expect 401)")
    if me_bare.status != 401:
        print("Mismatch: expected 401 Unauthorized for unauthenticated /me.", file=sys.stderr)
        return 1

    cookie_jar = CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookie_jar))
    unique_id = uuid.uuid4().hex[:12]
    email = f"probe-{unique_id}@example.com"
    password = "StrongPass123!"

    csrf = api_call(opener, "GET", f"{auth_base}/csrf")
    if csrf.status != 200:
        print(f"csrf failed: {csrf.status}", file=sys.stderr)
        return 1
    csrf_token = (csrf.body or {}).get("csrfToken") if isinstance(csrf.body, dict) else None
    if not csrf_token:
        print("csrf: missing csrfToken", file=sys.stderr)
        return 1
    csrf_headers = {"X-CSRFToken": str(csrf_token)}

    reg = api_call(
        opener,
        "POST",
        f"{auth_base}/register",
        {"email": email, "password": password},
        headers=csrf_headers,
    )
    if reg.status != 201:
        print(f"register failed: {reg.status} {reg.body}", file=sys.stderr)
        return 1

    csrf2 = api_call(opener, "GET", f"{auth_base}/csrf")
    if csrf2.status != 200:
        print(f"csrf (pre-login) failed: {csrf2.status}", file=sys.stderr)
        return 1
    csrf_token2 = (csrf2.body or {}).get("csrfToken") if isinstance(csrf2.body, dict) else None
    if not csrf_token2:
        print("csrf (pre-login): missing token", file=sys.stderr)
        return 1
    csrf_headers2 = {"X-CSRFToken": str(csrf_token2)}

    login = api_call(
        opener,
        "POST",
        f"{auth_base}/login",
        {"email": email, "password": password},
        headers=csrf_headers2,
    )
    if login.status != 200:
        print(f"login failed: {login.status} {login.body}", file=sys.stderr)
        return 1

    admin_roles = api_call(opener, "GET", f"{auth_base}/admin/roles")
    print(
        "GET /api/auth/admin/roles (authenticated, non-staff) -> "
        f"{admin_roles.status} (expect 403)"
    )
    if admin_roles.status != 403:
        print(
            "Mismatch: expected 403 Forbidden for non-staff admin list.",
            file=sys.stderr,
        )
        return 1

    print("Auth semantics probes passed (401 unauthenticated /me, 403 non-staff admin).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as exc:
        print(f"probe_auth_semantics failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
