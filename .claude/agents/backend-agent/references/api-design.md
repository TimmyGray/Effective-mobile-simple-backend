# Design Backend API

## Outcome

Provide a clear API design for authentication, authorization, and admin policy management endpoints,
including expected status codes and validation boundaries.

## Context

Architecture goals in `ARCHITECTURE.md` require custom auth/authz design with persisted policy tables.
Security expectations in `docs/SECURITY.md` require least privilege and deny-by-default behavior.

## Scope

In scope: endpoint shape, request/response model, status semantics, and permission requirements.
Out of scope: UI contracts and deployment-specific tuning.
