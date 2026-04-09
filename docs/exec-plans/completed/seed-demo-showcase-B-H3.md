# Execution Plan: B-H3 Demo DB Seed (Showcase)

## Task Description

Seed the database with demo users, role bindings, and documented credentials so recruitment/showcase flows work without manual setup.

## Acceptance Criteria

- [x] Fixed demo accounts after `migrate` with hashed password.
- [x] Member-bound user exercises RBAC matrix (`widgets:list`).
- [x] Staff user exercises `admin:manage` policy.
- [x] Plain user illustrates deny-by-default without matrix grant.
- [x] Credentials documented for local/recruitment only (not production).

## Delivered

- `accounts/migrations/0008_seed_demo_showcase_users.py`
- `ARCHITECTURE.md` — demo showcase accounts section
- `accounts/tests.py` — `DemoShowcaseSeedTests`

## Merge

- PR #7 (`feat/seed-demo-db-showcase`)
