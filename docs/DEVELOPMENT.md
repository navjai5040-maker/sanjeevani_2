# Development guide

## Tooling

- Python 3.12 (Python 3.11+ is also supported by the current API dependencies)
- Node.js 18+
- npm

## Local setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r services\api\requirements.txt
npm.cmd install
```

The supported demo configuration is:

```env
PERSISTENCE_BACKEND=memory
```

Copy [.env.example](../.env.example) to `.env` only when local configuration is needed. Never commit `.env` or put real credentials in an example file.

## Run locally

Backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
```

Web:

```powershell
npm.cmd run dev:web -- --host 127.0.0.1 --port 5173
```

Mobile:

```powershell
cd apps\mobile
npx.cmd expo start
```

Telegram mock:

```powershell
cd apps\telegram-bot
npm.cmd run mock
```

Use [SIH_DEMO_RUNBOOK.md](./SIH_DEMO_RUNBOOK.md) for the complete rehearsal flow.

## Infrastructure boundary

Docker, PostgreSQL, Redis, cloud deployment, and production synchronization are outside the current demo scope. Reserved infrastructure assets may remain in the repository for future work, but they are not required to run or validate the local prototype.

## Validation

```powershell
npm.cmd run lint --workspace apps/telegram-bot
npm.cmd test --workspace apps/telegram-bot
npm.cmd run typecheck --workspace apps/mobile
npm.cmd run build --workspace packages/shared-types
npm.cmd run build:web
.\.venv\Scripts\python.exe -m pytest services\api\tests -q
```
