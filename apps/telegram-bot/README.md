# SANJEEVANI Telegram conversational access

This is a token-free prototype adapter for the SANJEEVANI care-coordination APIs. Conversation understanding is deterministic and session-scoped; triage, matching, referrals, appointments, and follow-ups remain backend responsibilities.

## F2 conversation engine (first increment)

`conversation_engine.py` provides the stable understanding boundary used by `bot.py`.
It currently supports deterministic intent classification, basic English/Hinglish
language detection, patient/location/duration/symptom extraction, and missing-slot
identification. The existing numbered menu remains available, and natural messages
can start the same care-request flow.

Example:

```text
I am Ravi from Ghatol, I have chest pain for two hours
→ pat-ravi, chest pain, two hours, Ghatol
→ backend triage and facility matching
```

This is not an LLM and does not make diagnoses or independently select facilities.

Natural appointment requests are also supported:

```text
Book Ravi for cardiology tomorrow
→ available backend slots
→ explicit slot selection
→ booking summary and confirmation
→ appointment booking
```

The bot never books a slot before the user confirms. Slot availability and
booking validation remain controlled by the FastAPI appointment service.

## Local mock mode

No Telegram account or package installation is required:

```powershell
cd apps/telegram-bot
python bot.py --mock --script /start 1 "chest pain" 1 4 complete
```

The mock flow uses deterministic Ravi Meena data and exercises:

- `/start` menu
- Find Care
- backend-shaped triage guidance
- facility matching and explanation
- referral creation
- My Referral
- My Appointment
- Follow-up completion

## Environment

Copy `.env.example` to `.env` if desired:

```env
TELEGRAM_BOT_MODE=mock
TELEGRAM_BOT_TOKEN=
SANJEEVANI_API_BASE_URL=http://127.0.0.1:8000
```

`TELEGRAM_BOT_TOKEN` is never required in mock mode and must never be committed.

## Backend mode

Set `TELEGRAM_BOT_MODE=real` and provide `SANJEEVANI_API_BASE_URL` to call the existing FastAPI routes:

- `POST /api/v1/care-requests`
- `POST /api/v1/triage`
- `GET /api/v1/facilities/matches`
- `POST /api/v1/referrals`
- `GET /api/v1/referrals`
- `GET /api/v1/referrals/{id}/events`
- `GET /api/v1/appointments`
- `GET /api/v1/followups`
- `POST /api/v1/followups/{id}/complete`

With `TELEGRAM_BOT_TOKEN` set, run:

```powershell
python bot.py
```

The adapter uses Telegram's HTTPS `getUpdates` and `sendMessage` endpoints. Polling is opt-in and no token is needed for mock mode.

Run the focused adapter tests with:

```powershell
npm.cmd test --workspace apps/telegram-bot
```

The bot uses the wording **Decision-support guidance — not a diagnosis.** Emergency guidance directs the user to immediate human/emergency care.
