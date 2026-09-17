# Sanjeevani Architecture

## Design principles

- Shared domain model across all channels
- API-first contracts between apps and backend
- Deterministic triage and care matching before any ML augmentation
- Closed-loop referral tracking across the entire lifecycle
- Consent-aware interoperability and auditability
- Offline-first design for low-connectivity settings

## Layered architecture

```text
Users
  -> Mobile / Web / Telegram / SMS-USSD
  -> Auth + API
  -> Workflow Orchestrator
  -> Care Coordination Engine
  -> Unified Healthcare State
  -> Postgres + Redis
  -> External Systems
  -> Events / Notifications / Analytics
```

## Domain model

The shared model covers users, patient records, facilities, departments, services, diagnostic facilities, medicine availability, referrals, appointments, and follow-up workflows.

## Data persistence

- PostgreSQL stores durable healthcare records.
- Redis stores transient queue and availability state.
- Every referral transition emits an event for downstream consumers.

## Security guardrails

- JWT or OAuth-compatible access
- RBAC for user role transitions
- Audit logs for sensitive actions
- Protected endpoints for patient information and consent-based health data exchange

## Future extensibility

The current code is intentionally structured so that AI triage services, FHIR adapters, and teleconsultation providers can be plugged in without changing the domain interface.
