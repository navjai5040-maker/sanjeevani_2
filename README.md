# SANJEEVANI

SANJEEVANI is an **Intelligent Rural Healthcare Access, Coordination & Continuity Platform** prototype. It connects a patient or frontline ASHA/ANM worker to triage decision support, care-readiness matching, explainable facility selection, referrals, appointments, and follow-up coordination.

The supported local setup uses an in-memory FastAPI backend and deterministic demo data. It does not require Docker, WSL, PostgreSQL, Redis, cloud services, or production integrations.

## What the prototype demonstrates

- Shared patient identity across mobile, ASHA/ANM, facility, backend, and Telegram
- Triage decision support with emergency escalation
- Care-readiness facility matching
- Explainable **Why This Facility?** results
- Closed-loop referral lifecycle and timeline
- Appointment slot lookup, booking, completion, and cancellation
- Backend follow-up state and completion
- English/Hindi/Hinglish Telegram coordination
- Lightweight mock/demo behavior
- Simulated facility readiness and coordination signals

Safety boundary: **Decision-support guidance - not a diagnosis.**

## Repository structure

```text
apps/mobile/          Expo patient and ASHA/ANM application
apps/web/             React + Vite facility workspace
apps/telegram-bot/    Deterministic Telegram mock/local adapter
services/api/         FastAPI routes, models, repositories, and services
packages/shared-types Shared TypeScript contracts
docs/                 Runbook and development documentation
scripts/              Windows-friendly local startup helpers
infra/                Reserved infrastructure assets; not required for demo
```

## Prerequisites

- Windows PowerShell
- Python 3.12 (Python 3.11+ is also supported by the current API dependencies)
- Node.js 18+
- npm

If dependencies are not already installed:

```powershell
python -m pip install -r services\api\requirements.txt
npm.cmd install
```

Do not commit `.env` files, local virtual environments, `node_modules`, Expo caches, build output, or credentials. Use [.env.example](./.env.example) and the app-specific examples as templates.

## Local startup

The simplest Windows demo startup is:

```powershell
.\scripts\start-demo.ps1
```

Or use separate terminals.

### Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000` and uses `PERSISTENCE_BACKEND=memory`.

### Facility web

```powershell
npm.cmd run dev:web -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

### Mobile

```powershell
cd apps\mobile
$env:EXPO_PUBLIC_API_MODE="MOCK"
npx.cmd expo start
```

For a LAN-connected device later, use `EXPO_PUBLIC_API_MODE=REAL` and set `EXPO_PUBLIC_API_BASE_URL` to the laptop LAN address, never `localhost`. Physical-device testing is not claimed.

### Telegram mock mode

```powershell
cd apps\telegram-bot
npm.cmd run mock
```

Mock mode needs no Telegram account, bot token, or external service. The local adapter can call `http://127.0.0.1:8000` when used in a test harness. Real Telegram polling is opt-in and requires a token supplied outside version control.

## Demo reset

Use **Reset demo** in the facility workspace, or run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/demo/reset -Method Post
```

Reset restores deterministic in-memory care requests, referrals, referral events, appointments, and follow-up state.

## SIH golden demo

1. Reset the demo.
2. In mobile, choose ASHA/ANM and select **Ravi Meena**.
3. Create a care request, review triage, and inspect facility matches.
4. Open **Why This Facility?** and create the referral.
5. In the facility workspace, open Ravi's referral.
6. Advance: Destination Identified, Accepted, Scheduled, Arrived, Care Completed, Closed, and Follow Up.
7. Open the ASHA follow-up queue and complete Ravi's generated follow-up.
8. Use Telegram to ask for referral status, next action, follow-up status, and an appointment.

See [docs/SIH_DEMO_RUNBOOK.md](./docs/SIH_DEMO_RUNBOOK.md) for the click-by-click sequence and troubleshooting.

## Architecture overview

```text
Patient / ASHA mobile ─┐
                       ├─> FastAPI coordination API
Facility web ──────────┤       ├─ patient registry
                       │       ├─ care requests + triage
Telegram adapter ──────┘       ├─ matching + referrals
                               ├─ appointments
                               └─ follow-ups
```

The backend is the source of truth for coordination state. Telegram is an orchestration and conversation layer; it does not diagnose, select care independently, or replace backend validation.

## Current limitations

- In-memory persistence only for the supported demo.
- Facility readiness, queue, diagnostics, medicines, and operational state are simulated.
- No live hospital telemetry, doctor attendance, bed availability, government integration, ABDM, production FHIR, cloud deployment, or production offline synchronization.
- Physical Android device testing is not verified.
- Real Telegram polling requires external credentials and is not part of token-free local validation.

## Validation commands

```powershell
npm.cmd run lint --workspace apps/telegram-bot
npm.cmd test --workspace apps/telegram-bot
npm.cmd run mock --workspace apps/telegram-bot
npm.cmd run typecheck --workspace apps/mobile
npm.cmd run build --workspace packages/shared-types
npm.cmd run build:web
.\.venv\Scripts\python.exe -m pytest services\api\tests -q
```
