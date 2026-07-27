# ConnectLite — Security Design

## Authentication & authorization

- **JWT** (SimpleJWT) with access/refresh rotation and blacklist-on-logout
  (`rest_framework_simplejwt.token_blacklist`). Access tokens default to a
  30-minute lifetime, refresh to 7 days (both env-configurable).
- **Phone verification gate:** login is blocked (`403`) until
  `is_phone_verified=True`. Web registrants verify via OTP; USSD
  registrants are auto-verified since the telco/SIM already authenticated
  the number to reach the USSD gateway.
- Every DRF view declares `permission_classes` explicitly — the project
  default (`REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]`) is
  `IsAuthenticated`, so an endpoint that's meant to be public
  (registration, login, webhooks) must opt in to `AllowAny` rather than
  accidentally being open by omission.

## OTP handling

- Codes are generated with `secrets.choice` (CSPRNG), never `random`.
- Only a SHA-256 hash of the code is ever persisted
  (`OTPVerification.code_hash`) — the plaintext exists only in memory
  between generation and SMS dispatch, and is never logged (phone numbers
  are masked in log lines too, e.g. `080****`).
- Expiry (`OTP_EXPIRY_MINUTES`, default 5), max attempts
  (`OTP_MAX_ATTEMPTS`, default 3), and resend cooldown
  (`OTP_RESEND_COOLDOWN_SECONDS`, default 60) are all enforced
  server-side and configurable via environment variables.
- `apps/notifications/models.py::SMSMessage.body_preview` is capped at 160
  chars and — critically — OTP dispatch (`apps/accounts/services.py`)
  never routes through the general SMS notification logger at all, so an
  OTP code can never end up in that log table even truncated.

## Secrets & configuration

- All credentials (Django secret key, DB credentials, Africa's Talking
  username/API key) come from environment variables via `django-environ`,
  loaded from `backend/.env` (gitignored) — never hardcoded, never
  committed. `.env.example` at the repo root documents every required
  variable with safe non-secret defaults or empty placeholders.
- Docker Compose passes secrets via `env_file`/`environment`, never bakes
  them into an image layer; `.dockerignore` excludes `.env` from the build
  context entirely.

## Webhook security & idempotency

- Every Africa's Talking webhook (SMS incoming, SMS delivery, voice)
  writes a `WebhookEvent` row keyed on `(source, provider_event_id)`
  *before* processing, and checks for an existing processed record first —
  a redelivered webhook is a guaranteed no-op, not a best-effort one.
- Webhook views never expose internal error detail in their response body;
  failures are logged server-side and a generic acknowledgement is
  returned so Africa's Talking doesn't retry indefinitely on a payload we
  can't process.
- USSD/webhook endpoints are necessarily unauthenticated (the provider
  can't attach a user's JWT) — the idempotency ledger and input validation
  are the primary defenses here, consistent with how AT's own webhook
  model works. If AT begins signing webhook payloads in a verifiable way,
  that verification should be added to
  `apps/notifications/webhook_views.py` and `apps/ussd/views.py`.

## Airtime abuse prevention

`apps/airtime/services.py` centralizes every transfer (gift, referral
reward, community reward) through one `_execute_transaction` path:

- **Server-side amount validation** — `AIRTIME_SETTINGS["MIN_AMOUNT"]` /
  `MAX_AMOUNT"]` are enforced in the service layer, never trusting a
  frontend-supplied bound.
- **Self-reward prevention** — self-gifting and self-referral are rejected
  before any transaction row is created.
- **Replay/duplicate prevention** — `AirtimeTransaction.idempotency_key`
  has a database-level `unique` constraint (not just an application check),
  so even a retried/duplicated request can't create two transactions;
  `IntegrityError` is caught and surfaced as a clear `DuplicateTransactionError`.
- **Community rewards require admin role** — `community_reward()` checks
  `CommunityMembership.role == admin` for the actor and community
  membership for the recipient before allowing a reward.
- Every transaction is durably recorded as `pending` → `success`/`failed`
  with the provider's own transaction ID, so financial state is always
  reconstructable from the ledger.

## Input validation & data exposure

- `PublicProfileSerializer` (used for discovery, matches, connection
  requests) deliberately excludes `phone_number` and `email` — other
  users can never see a match's contact details through the API; contact
  happens through in-app/SMS messaging instead.
- All serializers use DRF's declarative validation (`ChoiceField`,
  `EmailField`, `UUIDField`, etc.) rather than manual parsing.
- DRF's `DEFAULT_THROTTLE_CLASSES` applies anonymous (20/min) and
  authenticated (120/min) rate limits globally, with the `otp` scope
  giving OTP request/verify endpoints a tighter, dedicated limit.

## CORS & transport

- `django-cors-headers` restricts allowed origins via
  `CORS_ALLOWED_ORIGINS` (env-configurable, defaults to the local Vite dev
  server only) — not a wildcard.
- `CorsMiddleware` is placed immediately after `SecurityMiddleware` and
  before `CommonMiddleware`, per django-cors-headers' own placement
  requirement.

## Known gaps / explicitly deferred (see `docs/development.md`)

- Referral rewards are wired for web registration (auto-generated
  `referral_code` per user, reward fires on phone verification, not bare
  registration) but **not** yet wired into the USSD registration flow.
- Live Africa's Talking Voice verification is unimplemented by design (see
  `docs/africastalking.md`) — do not enable `AT_DEMO_MODE=false` for Voice
  without first implementing `VoiceService._send_live` against verified AT
  documentation.
- No automated dependency/vulnerability scanning (e.g. `pip-audit`,
  `npm audit` in CI) has been configured yet.
