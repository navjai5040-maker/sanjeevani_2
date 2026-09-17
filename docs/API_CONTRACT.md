# API contract

## Endpoints

### Health

- GET `/healthz/`

### Care requests

- POST `/api/v1/care-requests`
- GET `/api/v1/care-requests/{request_id}`

```json
{
  "patient_id": "pat-456",
  "requester_id": "asha-123",
  "symptoms": "chest pain and dizziness",
  "duration": "2 hours",
  "urgency_indicators": ["chest pain"],
  "location": "Ghatol",
  "preferred_language": "hi"
}
```

Required fields are `patient_id`, `requester_id`, `symptoms`, `duration`, and `location`. `urgency_indicators` defaults to an empty list and `preferred_language` defaults to `en`.

### Triage

- POST `/api/v1/triage`

Request body:

```json
{
  "patient_id": "pat-456",
  "requester_id": "asha-123",
  "symptoms": "chest pain and dizziness",
  "duration": "2 hours",
  "urgency_indicators": ["chest pain"],
  "location": "Ghatol",
  "preferred_language": "hi"
}
```

Response:

```json
{
  "request_id": "req-123",
  "level": "urgent",
  "rationale": ["Urgency indicator requires prompt clinical review"],
  "requires_emergency_escalation": false
}
```

### Care matching

- GET `/api/v1/facilities`
- GET `/api/v1/facilities/{facility_id}`
- GET `/api/v1/facilities/{facility_id}/state`
- GET `/api/v1/facilities/matches?patient_id=pat-456&requester_id=asha-123&symptoms=cardiology&duration=1%20day&location=Ghatol`

Matches exclude facilities without a relevant capability. Ranking considers capability, specialist and diagnostic availability, medicines, readiness, queue, and travel; it is not a nearest-facility sort.

Facility responses include `facility_id`, `facility_name`, `district`, `facility_type`, `services`, `specialist_availability`, `diagnostics`, `medicines`, `queue_minutes`, `operational_status`, `travel_minutes`, and `readiness`.

### Appointments and queue

- GET `/api/v1/appointments/slots?facility_id=fac-udaipur-dh&service=cardiology`
- POST `/api/v1/appointments`
- GET `/api/v1/appointments/{appointment_id}`

```json
{
  "patient_id": "pat-456",
  "facility_id": "fac-udaipur-dh",
  "provider_id": "provider-1",
  "service": "cardiology",
  "starts_at": "2026-09-17T09:00:00Z"
}
```

Appointment conflicts return `409 Conflict`; past appointment times return `422 Unprocessable Entity`.

Required booking fields are `patient_id`, `facility_id`, `provider_id`, `service`, and `starts_at`. Slot responses include `slot_id`, provider, service, time, estimated wait, and status.

### Referral lifecycle

- GET `/api/v1/referrals/states`
- POST `/api/v1/referrals`
- GET `/api/v1/referrals`
- GET `/api/v1/referrals/{referral_id}`
- GET `/api/v1/referrals/{referral_id}/events`
- POST `/api/v1/referrals/{referral_id}/transition`

Referral transitions are strictly ordered. A transition that skips a lifecycle state returns `409 Conflict`, and every accepted transition creates a durable domain event in the service boundary.

Referral creation requires `patient_id` and `destination`. Referral event responses contain `referral_id`, `state`, `timestamp`, and `description`.
