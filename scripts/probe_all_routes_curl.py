"""
Probe every URL route registered under config/urls.py using curl.exe (CSRF + sessions).

AI Annotation:
- Purpose: Exercise health, Django /admin/ entry, /api/auth/* (all handlers), and /api/resources/*.
- Side effects: Creates disposable roles/permissions/policy rows and deletes them; registers a disposable user
  and runs PATCH + DELETE /api/auth/me; registers another throwaway user; mutates matrix then restores.
- Failure modes: Exits non-zero when an HTTP status is outside the allowed set for that probe.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

BASE = os.environ.get("PROBE_BASE_URL", "http://127.0.0.1:8000")

# (method, path) -> allowed status code(s)
Expected = int | tuple[int, ...]


def curl_req(
    method: str,
    path: str,
    *,
    cookie_jar: str,
    json_body: dict | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    url = BASE.rstrip("/") + path
    args = [
        "curl.exe",
        "-s",
        "-S",
        "-w",
        "\n__HTTPSTATUS__:%{http_code}",
        "-c",
        cookie_jar,
        "-b",
        cookie_jar,
    ]
    if method.upper() != "GET":
        args.extend(["-X", method.upper()])
    if json_body is not None:
        args.extend(["-H", "Content-Type: application/json", "-d", json.dumps(json_body)])
    if extra_headers:
        for k, v in extra_headers.items():
            args.extend(["-H", f"{k}: {v}"])
    args.append(url)
    r = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return -1, r.stderr or "curl failed"
    out = r.stdout
    m = re.search(r"\n__HTTPSTATUS__:(\d+)$", out)
    code = int(m.group(1)) if m else -1
    body = re.sub(r"\n__HTTPSTATUS__:\d+$", "", out)
    return code, body


def fetch_csrf(cookie_jar: str) -> str:
    code, body = curl_req("GET", "/api/auth/csrf", cookie_jar=cookie_jar)
    if code != 200:
        raise RuntimeError(f"CSRF GET failed: {code} {body[:200]}")
    return json.loads(body)["csrfToken"]


def login(cookie_jar: str, email: str, password: str) -> None:
    csrf = fetch_csrf(cookie_jar)
    code, body = curl_req(
        "POST",
        "/api/auth/login",
        cookie_jar=cookie_jar,
        json_body={"email": email, "password": password},
        extra_headers={"X-CSRFToken": csrf},
    )
    if code != 200:
        raise RuntimeError(f"login failed for {email}: {code} {body[:300]}")


def ok(got: int, want: Expected) -> bool:
    if isinstance(want, tuple):
        return got in want
    return got == want


def main() -> int:
    results: list[tuple[str, str, int, Expected | None]] = []

    def record(label: str, method: str, path: str, got: int, want: Expected | None) -> None:
        passed = want is None or ok(got, want)
        results.append((label, f"{method} {path}", got, want))
        status = "OK" if passed else "FAIL"
        exp = ""
        if want is not None:
            exp = f" (expected {want})"
        print(f"[{status}] {label}: {method} {path} -> {got}{exp}")

    # --- Anonymous: health, csrf, Django admin entry, protected GETs ---
    no_cookie = tempfile.NamedTemporaryFile(delete=False, suffix="_cookies.txt")
    no_cookie_path = no_cookie.name
    no_cookie.close()
    try:
        for path, want in [
            ("/health/live", 200),
            ("/health/ready", 200),
            ("/api/auth/csrf", 200),
        ]:
            code, _ = curl_req("GET", path, cookie_jar=no_cookie_path)
            record("anon", "GET", path, code, want)

        for path, want in [
            ("/api/auth/me", 401),
            ("/api/resources/widgets", 401),
            ("/api/auth/admin/roles", 401),
            ("/api/auth/admin-probe", 401),
        ]:
            code, _ = curl_req("GET", path, cookie_jar=no_cookie_path)
            record("anon", "GET", path, code, want)

        code, _ = curl_req("GET", "/admin/", cookie_jar=no_cookie_path)
        record("anon", "GET", "/admin/", code, (200, 301, 302))
    finally:
        os.unlink(no_cookie_path)

    # --- Member ---
    member_jar = tempfile.NamedTemporaryFile(delete=False, suffix="_member.txt")
    member_jar.close()
    try:
        login(member_jar.name, "demo.member@example.com", "DemoShowcase2026!")
        for path, want in [
            ("/api/auth/me", 200),
            ("/api/resources/widgets", 200),
            ("/api/auth/admin/roles", 403),
            ("/api/auth/admin-probe", 403),
        ]:
            code, _ = curl_req("GET", path, cookie_jar=member_jar.name)
            record("member", "GET", path, code, want)
        # Staff also lacks auth:admin_probe in seed data.
        code, _ = curl_req("POST", "/api/auth/logout", cookie_jar=member_jar.name, extra_headers={"X-CSRFToken": fetch_csrf(member_jar.name)})
        record("member", "POST", "/api/auth/logout", code, 204)
    finally:
        os.unlink(member_jar.name)

    # --- Staff: full admin API surface + matrix restore + disposable user lifecycle ---
    staff_jar = tempfile.NamedTemporaryFile(delete=False, suffix="_staff.txt")
    staff_jar.close()
    try:
        login(staff_jar.name, "demo.staff@example.com", "DemoShowcase2026!")

        code, _ = curl_req("GET", "/api/auth/admin-probe", cookie_jar=staff_jar.name)
        record("staff", "GET", "/api/auth/admin-probe", code, 403)

        code, body = curl_req("GET", "/api/auth/admin/roles", cookie_jar=staff_jar.name)
        record("staff", "GET", "/api/auth/admin/roles", code, 200)
        if code != 200:
            raise RuntimeError("roles list required")
        roles = json.loads(body)
        rid0 = roles[0]["id"]
        code, _ = curl_req("GET", f"/api/auth/admin/roles/{rid0}", cookie_jar=staff_jar.name)
        record("staff", "GET", f"/api/auth/admin/roles/{rid0}", code, 200)

        code, body = curl_req("GET", "/api/auth/admin/access-permissions", cookie_jar=staff_jar.name)
        record("staff", "GET", "/api/auth/admin/access-permissions", code, 200)
        perms = json.loads(body)
        pid0 = perms[0]["id"]
        code, _ = curl_req("GET", f"/api/auth/admin/access-permissions/{pid0}", cookie_jar=staff_jar.name)
        record("staff", "GET", f"/api/auth/admin/access-permissions/{pid0}", code, 200)

        code, body = curl_req("GET", "/api/auth/admin/policy-rules", cookie_jar=staff_jar.name)
        record("staff", "GET", "/api/auth/admin/policy-rules", code, 200)
        rules = json.loads(body)
        prid0 = rules[0]["id"]
        code, _ = curl_req("GET", f"/api/auth/admin/policy-rules/{prid0}", cookie_jar=staff_jar.name)
        record("staff", "GET", f"/api/auth/admin/policy-rules/{prid0}", code, 200)

        suffix = uuid.uuid4().hex[:8]
        probe_role_name = f"probe_role_{suffix}"
        csrf = fetch_csrf(staff_jar.name)
        code, body = curl_req(
            "POST",
            "/api/auth/admin/roles",
            cookie_jar=staff_jar.name,
            json_body={"name": probe_role_name, "description": "curl probe"},
            extra_headers={"X-CSRFToken": csrf},
        )
        record("staff", "POST", "/api/auth/admin/roles", code, 201)
        probe_role_id = json.loads(body)["id"] if code == 201 else None
        if probe_role_id:
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "PATCH",
                f"/api/auth/admin/roles/{probe_role_id}",
                cookie_jar=staff_jar.name,
                json_body={"description": "patched"},
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "PATCH", f"/api/auth/admin/roles/{probe_role_id}", code, 200)
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "DELETE",
                f"/api/auth/admin/roles/{probe_role_id}",
                cookie_jar=staff_jar.name,
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "DELETE", f"/api/auth/admin/roles/{probe_role_id}", code, 204)

        res_name = f"probe_res_{suffix}"
        act_name = f"probe_act_{suffix}"
        csrf = fetch_csrf(staff_jar.name)
        code, body = curl_req(
            "POST",
            "/api/auth/admin/access-permissions",
            cookie_jar=staff_jar.name,
            json_body={"resource": res_name, "action": act_name},
            extra_headers={"X-CSRFToken": csrf},
        )
        record("staff", "POST", "/api/auth/admin/access-permissions", code, 201)
        probe_perm_id = json.loads(body)["id"] if code == 201 else None
        if probe_perm_id:
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "PATCH",
                f"/api/auth/admin/access-permissions/{probe_perm_id}",
                cookie_jar=staff_jar.name,
                json_body={"resource": res_name, "action": act_name + "_p"},
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "PATCH", f"/api/auth/admin/access-permissions/{probe_perm_id}", code, 200)
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "DELETE",
                f"/api/auth/admin/access-permissions/{probe_perm_id}",
                cookie_jar=staff_jar.name,
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "DELETE", f"/api/auth/admin/access-permissions/{probe_perm_id}", code, 204)

        csrf = fetch_csrf(staff_jar.name)
        code, body = curl_req(
            "POST",
            "/api/auth/admin/policy-rules",
            cookie_jar=staff_jar.name,
            json_body={
                "resource": f"probe_rule_res_{suffix}",
                "action": f"probe_rule_act_{suffix}",
                "subject_type": "any",
                "subject_value": "",
                "is_allowed": True,
            },
            extra_headers={"X-CSRFToken": csrf},
        )
        record("staff", "POST", "/api/auth/admin/policy-rules", code, 201)
        probe_rule_id = json.loads(body)["id"] if code == 201 else None
        if probe_rule_id:
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "PATCH",
                f"/api/auth/admin/policy-rules/{probe_rule_id}",
                cookie_jar=staff_jar.name,
                json_body={"is_allowed": False},
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "PATCH", f"/api/auth/admin/policy-rules/{probe_rule_id}", code, 200)
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "DELETE",
                f"/api/auth/admin/policy-rules/{probe_rule_id}",
                cookie_jar=staff_jar.name,
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "DELETE", f"/api/auth/admin/policy-rules/{probe_rule_id}", code, 204)

        member_role = next((r for r in roles if r["name"] == "member"), None)
        widgets_list = next(
            (p for p in perms if p.get("resource") == "widgets" and p.get("action") == "list"),
            None,
        )
        if member_role and widgets_list:
            mrid, apid = member_role["id"], widgets_list["id"]
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "POST",
                f"/api/auth/admin/roles/{mrid}/permissions",
                cookie_jar=staff_jar.name,
                json_body={"access_permission_id": apid},
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "POST", f"/api/auth/admin/roles/{mrid}/permissions", code, (200, 201))
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "DELETE",
                f"/api/auth/admin/roles/{mrid}/permissions/{apid}",
                cookie_jar=staff_jar.name,
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "DELETE", f"/api/auth/admin/roles/{mrid}/permissions/{apid}", code, 204)
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "POST",
                f"/api/auth/admin/roles/{mrid}/permissions",
                cookie_jar=staff_jar.name,
                json_body={"access_permission_id": apid},
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "POST(restore matrix)", f"/api/auth/admin/roles/{mrid}/permissions", code, (200, 201))

        plain_jar = tempfile.NamedTemporaryFile(delete=False, suffix="_plain.txt")
        plain_jar.close()
        try:
            login(plain_jar.name, "demo.plain@example.com", "DemoShowcase2026!")
            code, body = curl_req("GET", "/api/auth/me", cookie_jar=plain_jar.name)
            record("plain", "GET", "/api/auth/me", code, 200)
            plain_uid = json.loads(body)["id"]
        finally:
            os.unlink(plain_jar.name)

        if member_role:
            mid = member_role["id"]
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "POST",
                f"/api/auth/admin/users/{plain_uid}/roles",
                cookie_jar=staff_jar.name,
                json_body={"role_id": mid},
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "POST", f"/api/auth/admin/users/{plain_uid}/roles", code, (200, 201))
            csrf = fetch_csrf(staff_jar.name)
            code, _ = curl_req(
                "DELETE",
                f"/api/auth/admin/users/{plain_uid}/roles/{mid}",
                cookie_jar=staff_jar.name,
                extra_headers={"X-CSRFToken": csrf},
            )
            record("staff", "DELETE", f"/api/auth/admin/users/{plain_uid}/roles/{mid}", code, 204)

        # Disposable user: register → login → PATCH /me → DELETE /me
        life_jar = tempfile.NamedTemporaryFile(delete=False, suffix="_life.txt")
        life_jar.close()
        try:
            uemail = f"curl.lifecycle.{uuid.uuid4().hex[:10]}@example.com"
            csrf_l = fetch_csrf(life_jar.name)
            code, _ = curl_req(
                "POST",
                "/api/auth/register",
                cookie_jar=life_jar.name,
                json_body={
                    "email": uemail,
                    "first_name": "Life",
                    "last_name": "Cycle",
                    "middle_name": "Test",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                },
                extra_headers={"X-CSRFToken": csrf_l},
            )
            record("lifecycle", "POST", "/api/auth/register", code, 201)
            csrf_l = fetch_csrf(life_jar.name)
            code, _ = curl_req(
                "POST",
                "/api/auth/login",
                cookie_jar=life_jar.name,
                json_body={"email": uemail, "password": "StrongPass123!"},
                extra_headers={"X-CSRFToken": csrf_l},
            )
            record("lifecycle", "POST", "/api/auth/login", code, 200)
            code, _ = curl_req("GET", "/api/auth/me", cookie_jar=life_jar.name)
            record("lifecycle", "GET", "/api/auth/me", code, 200)
            csrf_l = fetch_csrf(life_jar.name)
            code, _ = curl_req(
                "PATCH",
                "/api/auth/me",
                cookie_jar=life_jar.name,
                json_body={"first_name": "LifePatched"},
                extra_headers={"X-CSRFToken": csrf_l},
            )
            record("lifecycle", "PATCH", "/api/auth/me", code, 200)
            csrf_l = fetch_csrf(life_jar.name)
            code, _ = curl_req(
                "DELETE",
                "/api/auth/me",
                cookie_jar=life_jar.name,
                extra_headers={"X-CSRFToken": csrf_l},
            )
            record("lifecycle", "DELETE", "/api/auth/me", code, 204)
        finally:
            os.unlink(life_jar.name)

        reg_jar = tempfile.NamedTemporaryFile(delete=False, suffix="_reg.txt")
        reg_jar.close()
        try:
            email = f"curl.probe.{uuid.uuid4().hex[:12]}@example.com"
            csrf_r = fetch_csrf(reg_jar.name)
            code, _ = curl_req(
                "POST",
                "/api/auth/register",
                cookie_jar=reg_jar.name,
                json_body={
                    "email": email,
                    "first_name": "Curl",
                    "last_name": "Probe",
                    "middle_name": "Test",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                },
                extra_headers={"X-CSRFToken": csrf_r},
            )
            record("register", "POST", "/api/auth/register", code, 201)
            time.sleep(0.15)
        finally:
            os.unlink(reg_jar.name)

        csrf = fetch_csrf(staff_jar.name)
        code, _ = curl_req(
            "POST",
            "/api/auth/logout",
            cookie_jar=staff_jar.name,
            extra_headers={"X-CSRFToken": csrf},
        )
        record("staff", "POST", "/api/auth/logout", code, 204)

    finally:
        os.unlink(staff_jar.name)

    failed = [r for r in results if r[3] is not None and not ok(r[2], r[3])]
    if failed:
        print("\nFailed probes:")
        for label, what, got, want in failed:
            print(f"  {label} {what} got={got} expected={want}")
        return 1
    print("\nAll route probes passed (allowed status sets).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
