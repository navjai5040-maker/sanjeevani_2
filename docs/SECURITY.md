# Security

## Baseline controls

- Use environment variables for secrets.
- Keep authentication tokens behind the API layer.
- Role-based access using a shared user role enum.
- Consent-aware access for medical history exchange.
- Audit log generation for care actions and referral movement.

## Operational guidance

- Validate all incoming requests.
- Keep FHIR / ABDM adapters behind service boundaries.
- Use Redis only for transient workflow state and rate limiting.
- Do not claim production integrations without credentialed access.
