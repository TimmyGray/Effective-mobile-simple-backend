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
            if raw:
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = raw
            else:
                parsed = None
            return ResponseData(status=resp.status, body=parsed)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.length != 0 else ""
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw
        else:
            parsed = None
        return ResponseData(status=exc.code, body=parsed)


def assert_status(step: str, got: int, expected: int) -> None:
    if got != expected:
        raise RuntimeError(f"{step}: expected {expected}, got {got}")


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    base_url = base_url.rstrip("/")
    auth_base = f"{base_url}/api/auth"
    unique_id = uuid.uuid4().hex[:12]
    email = f"smoke-{unique_id}@example.com"
    password = "StrongPass123!"

    cookie_jar = CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookie_jar))

    print(f"Smoke test target: {base_url}")
    print(f"Using generated user: {email}")

    csrf = api_call(opener, "GET", f"{auth_base}/csrf")
    assert_status("csrf", csrf.status, 200)
    csrf_token = (csrf.body or {}).get("csrfToken")
    if not csrf_token:
        raise RuntimeError("csrf: missing token")
    csrf_headers = {"X-CSRFToken": str(csrf_token)}
    print("OK csrf -> 200")

    register = api_call(
        opener,
        "POST",
        f"{auth_base}/register",
        {
            "email": email,
            "first_name": "Smoke",
            "last_name": "Tester",
            "middle_name": "Runner",
            "password": password,
            "password_confirm": password,
        },
        headers=csrf_headers,
    )
    assert_status("register", register.status, 201)
    print("OK register -> 201")

    login = api_call(
        opener,
        "POST",
        f"{auth_base}/login",
        {"email": email, "password": password},
        headers=csrf_headers,
    )
    assert_status("login", login.status, 200)
    print("OK login -> 200")

    # Django rotates CSRF token on login; fetch fresh token for unsafe authenticated requests.
    csrf_after_login = api_call(opener, "GET", f"{auth_base}/csrf")
    assert_status("csrf (after login)", csrf_after_login.status, 200)
    csrf_token_after_login = (csrf_after_login.body or {}).get("csrfToken")
    if not csrf_token_after_login:
        raise RuntimeError("csrf (after login): missing token")
    csrf_headers = {"X-CSRFToken": str(csrf_token_after_login)}
    print("OK csrf (after login) -> 200")

    me = api_call(opener, "GET", f"{auth_base}/me")
    assert_status("me (authenticated)", me.status, 200)
    print("OK me (authenticated) -> 200")

    logout = api_call(opener, "POST", f"{auth_base}/logout", headers=csrf_headers)
    assert_status("logout", logout.status, 204)
    print("OK logout -> 204")

    me_after_logout = api_call(opener, "GET", f"{auth_base}/me")
    assert_status("me (after logout)", me_after_logout.status, 401)
    print("OK me (after logout) -> 401")

    print("Auth smoke test passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Auth smoke test failed: {exc}")
        raise SystemExit(1)
