# SANJEEVANI SIH Demo Runbook

This runbook uses the deterministic in-memory backend. It does not require Docker, PostgreSQL, Redis, WSL, or external integrations.

## Startup

From the repository root:

```powershell
.\scripts\start-demo.ps1
```

Or use separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
npm.cmd run dev:web -- --host 127.0.0.1 --port 5173
cd apps/mobile
npx.cmd expo start
```

Open the facility workspace at `http://127.0.0.1:5173`.

For a physical Android device, set `EXPO_PUBLIC_API_MODE=REAL` and set `EXPO_PUBLIC_API_BASE_URL` to the laptop LAN IP and port `8000`, not `localhost`.

For the local Telegram adapter (no Telegram credentials required):

```powershell
cd apps/telegram-bot
npm.cmd run mock
```

To exercise the adapter against the running FastAPI backend, use `ApiClient("http://127.0.0.1:8000")` from `bot.py`; the adapter does not require a Telegram token for local QA.

## Reset

Use **Reset demo** in the facility workspace, or run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/demo/reset -Method Post
```

Reset clears in-memory care requests, referrals, referral events, appointments, and restores deterministic follow-ups.

## Golden 5–7 minute scenario

1. Open the mobile app and choose **ASHA / ANM**.
2. Select **Ravi Meena**.
3. Create a care request.
4. Review decision-support triage.
5. Open the facility match and read **Why this facility?**.
6. Create a referral to the selected facility.
7. Open the facility web workspace.
8. Open **Referrals** and select **Ravi Meena**.
9. Advance only the displayed next action:
   `Destination identified` -> `Accepted` -> `Scheduled` -> `Arrived` -> `Care completed` -> `Closed`.
10. Open **Followups** and confirm Ravi's post-referral follow-up appears.
11. Return to the ASHA app and open **Follow-up queue**.
12. Complete Ravi's follow-up. In REAL mode this updates the shared backend record.
13. Reopen Ravi's patient overview and show the shared referral, appointment, and follow-up state.

## Telegram demo

After the ASHA/facility journey has created the shared state, send these messages to one `ConversationBot` session:

```text
Ravi ka referral kahan tak pahucha?
Next kya karna hai?
Ravi ka follow-up kab hai?
Kal appointment chahiye.
1
Yes
```

The responses are read from the backend in REAL adapter mode. In MOCK mode, the same flow uses deterministic demo state. The adapter gives coordination guidance only; it does not diagnose or prescribe.

## Backup scenario

Use **Sita Devi** for a maternal follow-up:

1. ASHA -> Sita Devi.
2. Create a routine maternal-care request.
3. Select CHC, Banswara or PHC, Ghatol.
4. Book an appointment.
5. Show the facility readiness and appointment queue.
6. In the facility appointment queue, use **Mark completed** or **Cancel** only while the appointment is `Booked`.

## Troubleshooting

- Backend unavailable: verify `http://127.0.0.1:8000/healthz/`.
- Port already in use: stop the existing local process or use another port and update the web/mobile API base URL.
- Web shows `Facility unavailable`: start FastAPI first and reload the web page.
- Expo does not connect: ensure the phone and laptop share a network; for REAL mode use the laptop LAN IP.
- Demo state is confusing: run the reset command before rehearsing.
- Windows command not found: use `npm.cmd` and `npx.cmd` instead of shell aliases.

## Prototype boundaries

Facility readiness, follow-up seed data, and demo authentication are simulated. Appointment transitions currently support only the model-backed `booked -> completed` and `booked -> cancelled` actions. No live hospital telemetry or production identity verification is implied.

The prototype has not been verified on a physical Android device: **DEVICE NOT VERIFIED**. Facility matching is deterministic demo data, so an alternative facility is shown only when the backend returns one. Telegram real polling requires external credentials and is not part of the token-free local validation.
