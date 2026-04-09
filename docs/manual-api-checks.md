# Manual API checks (curl and HTTPie)

Use this guide when you want to exercise the API from a terminal without pytest. It complements automated tests in `accounts/tests/` and the smoke script `scripts/smoke_auth.py`.

## Prerequisites

- Django dev server running (for example `python manage.py runserver 127.0.0.1:8000`).
- Base URL examples below use `http://127.0.0.1:8000`; substitute your host and port.

## Auth semantics (quick reference)

| Situation | Typical status |
| --------- | -------------- |
| No session on a protected endpoint | `401 Unauthorized` |
| Session present but policy denies the action | `403 Forbidden` |
| Staff-only admin API as non-staff | `403 Forbidden` |

Protected endpoints use DRF `SessionAuthentication401` so missing identity returns **401**, not 403.

## CSRF for unsafe methods

State-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`) require:

1. A CSRF token from `GET /api/auth/csrf` (JSON body includes `csrfToken`).
2. Header `X-CSRFToken: <token>` on the unsafe request.
3. The client must send the **session cookie** returned by the server (`sessionid`) on subsequent requests.

**After login**, Django may rotate the CSRF secret. For another `POST` (for example `logout`), call `GET /api/auth/csrf` again and send the new token — same pattern as `scripts/smoke_auth.py`.

## curl: cookie jar and probes

Initialize a cookie jar and fetch CSRF:

```bash
BASE=http://127.0.0.1:8000
curl -s -c cookies.txt -b cookies.txt "$BASE/api/auth/csrf"
```

Parse `csrfToken` from the JSON (or copy it from the response). Export it (bash):

```bash
CSRF=$(curl -s -c cookies.txt -b cookies.txt "$BASE/api/auth/csrf" | python -c "import sys,json; print(json.load(sys.stdin)['csrfToken'])")
```

Register and log in (replace email/password):

```bash
curl -s -c cookies.txt -b cookies.txt -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" \
  -d '{"email":"you@example.com","first_name":"Ivan","last_name":"Petrov","middle_name":"Sergeevich","password":"StrongPass123!","password_confirm":"StrongPass123!"}'

CSRF=$(curl -s -c cookies.txt -b cookies.txt "$BASE/api/auth/csrf" | python -c "import sys,json; print(json.load(sys.stdin)['csrfToken'])")

curl -s -c cookies.txt -b cookies.txt -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" \
  -d '{"email":"you@example.com","password":"StrongPass123!"}'
```

### 401 probe (no session)

Print status on its own line after the response body (works in Git Bash, macOS, Linux):

```bash
curl -s -w "\n%{http_code}\n" "$BASE/api/auth/me"
```

Expect `401` on the last line. On Windows **cmd**, you can use the same `curl` if available, or rely on `python scripts/probe_auth_semantics.py`.

### 403 probe (authenticated, not allowed)

Easiest path: register and log in as above (non-staff user), then call a staff-only admin route:

```bash
curl -s -w "\n%{http_code}\n" -b cookies.txt "$BASE/api/auth/admin/roles"
```

Expect `403` on the last line.

### Seeded demo users (after `migrate`)

See `ARCHITECTURE.md` (Demo showcase accounts). You can log in with a fixed demo email/password and repeat the admin list call to observe `403` for `demo.member@example.com` or `200` for `demo.staff@example.com` without registering a new user.

## HTTPie: session file

HTTPie can persist cookies in a session:

```bash
set BASE=http://127.0.0.1:8000
http --session=./api-session.json GET "$BASE/api/auth/csrf"
```

Read `csrfToken` from the output, then:

```bash
http --session=./api-session.json POST "$BASE/api/auth/login" \
  email=demo.member@example.com password=DemoShowcase2026! \
  X-CSRFToken:<paste-token>
```

Use `GET "$BASE/api/auth/me"` with the same `--session` to verify `200` when logged in, and without `--session` for a `401` check on protected routes.

## Helper scripts

| Script | Purpose |
| ------ | ------- |
| `scripts/smoke_auth.py` | End-to-end register → login → me → logout; asserts status codes. |
| `scripts/probe_auth_semantics.py` | Prints labeled `401` / `403` probes for quick manual verification. |

Run probes (server must be up):

```bash
python scripts/probe_auth_semantics.py http://127.0.0.1:8000
```

## Health checks (no auth)

```bash
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8000/health/live
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8000/health/ready
```

These are plain Django views (not DRF); they do not use the session auth flow above.
