# ConnectLite × Africa's Talking Integration

## Design principle

All Africa's Talking calls live in `backend/integrations/africastalking/`.
No Django view, serializer, or app-level service ever imports the
`africastalking` SDK directly. Every submodule exposes the same shape:
a `*Service` class with a `send`/`start_*` method that returns a small
result object (`success`, provider ID, `is_demo` flag), so callers never
need to know whether they're talking to the real API or the demo mock.

## Demo mode

`AT_DEMO_MODE=true` (the default) routes every provider call through a
local mock in the same module as the live implementation — e.g.
`SMSService._send_demo` vs `SMSService._send_live` — so switching to a real
Africa's Talking sandbox is purely a matter of environment variables:

```
AT_USERNAME=your-sandbox-username
AT_API_KEY=your-sandbox-api-key
AT_ENVIRONMENT=sandbox
AT_DEMO_MODE=false
```

No application code changes are required. Demo-mode responses are clearly
tagged (`is_demo=True`, `provider_message_id` prefixed `DEMO-`) so they can
never be confused with a real provider transaction in the database or
logs.

## SMS (`integrations/africastalking/sms.py`)

Used for: OTP delivery, match notifications, connection-request
notifications, and the app↔feature-phone messaging bridge.

- `SMSService.send(phone_number, message)` — general send
- `SMSService.send_otp(phone_number, code)` — templated OTP message

Live implementation uses the official `africastalking` Python SDK's
`SMS.send()`, checking AT's own status code convention (`101` = queued
successfully) rather than assuming success from an HTTP 200.

## USSD (`apps/ussd/services.py` + `integrations/africastalking/ussd.py`)

Unlike SMS/Airtime, Africa's Talking USSD has no outbound "send" call to
wrap — AT calls **our** webhook (`POST /api/v1/webhooks/ussd/`) with the
full accumulated session input, and expects a plain-text response prefixed
`CON` (continue) or `END` (terminate). `integrations/africastalking/ussd.py`
only centralizes that response formatting; all the actual menu logic lives
in `apps/ussd/services.py`, written as a pure function of the cumulative
`text` field rather than a server-tracked state machine (see
`docs/architecture/system-architecture.md` for why).

## Airtime (`integrations/africastalking/airtime.py`)

`AirtimeService.send(phone_number, amount)` wraps AT's Airtime API. All
business-rule enforcement (min/max amount, self-gift prevention,
idempotency) happens one layer up, in `apps/airtime/services.py` — this
module is a thin, swappable transport layer only.

## Voice — deliberately incomplete, and why

**This is the one area where the implementation is intentionally partial,**
per the project's own instruction to never invent undocumented Africa's
Talking behaviour and to document reduced scope rather than ship something
fragile.

This build was produced without verified access to an Africa's Talking
Voice sandbox. The *live* flow described in the brief —

```
User requests verification -> AT calls user -> user confirms -> webhook -> profile verified
```

 — requires confirming the current Voice API's call-initiation endpoint and
the exact webhook/callback payload shape against Africa's Talking's live
documentation. Rather than fabricate plausible-looking field names,
`integrations/africastalking/voice.py::VoiceService._send_live` raises
`NotImplementedError` with a clear message pointing back to this file.

What **is** implemented and fully working:
- `VoiceService._send_demo` — simulates the same user-facing flow
- `POST /api/v1/voice/verification/start/` — in demo mode, immediately
  marks the user's phone verified, so the product story/demo can be shown
  end-to-end
- `POST /api/v1/webhooks/voice/` — a webhook receiver stub that records
  `WebhookEvent`s for future wiring, but isn't exercised by the demo flow

**Before enabling live Voice:** confirm the current call-initiation
endpoint and webhook payload format against Africa's Talking's official
docs, then fill in `_send_live` and the webhook handler's field parsing
accordingly.

## Idempotency

Every webhook receiver (SMS incoming, SMS delivery, voice) creates a
`WebhookEvent` row keyed on `(source, provider_event_id)` *before*
processing. A redelivered webhook — which AT will do on anything other than
a 2xx response — is detected and short-circuited, so retries can never
double-process a message, double-update a delivery status, or double-fire
a notification.
