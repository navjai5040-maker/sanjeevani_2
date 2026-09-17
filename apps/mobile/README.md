# Mobile app

Patient-first Expo vertical slice:

`Login -> Dashboard -> Care Request -> Triage -> Matches -> Facility -> Appointment or Referral -> Referral Timeline`

Set `EXPO_PUBLIC_API_MODE=MOCK` for the included deterministic demo data, or set it to `REAL` and configure `EXPO_PUBLIC_API_BASE_URL` to the reachable FastAPI host.

## Run on Android with Expo Go

```powershell
cd apps\mobile
npx expo start
```

For a real backend on a phone, use the computer's LAN IP rather than `localhost`:

```env
EXPO_PUBLIC_API_MODE=REAL
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000
```

Start the API so it is reachable on the LAN:

```powershell
uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000
```
