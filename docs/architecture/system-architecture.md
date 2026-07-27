# ConnectLite — System Architecture

## Overview

ConnectLite is a hybrid online/offline social platform. Smartphone users
reach it through a React web app; feature-phone users reach the *same*
backend and the *same* social graph through USSD and SMS, via Africa's
Talking. Nothing about a user's account, matches, or communities differs
based on which channel they use to access it.

## Logical architecture

```
                        USERS
                          |
           +--------------+--------------+
           |                             |
      Smartphone                   Feature Phone
           |                             |
   React (Vite) SPA               USSD / SMS (Africa's Talking)
           |                             |
           +--------------+--------------+
                          |
                Django REST Framework API
                     (config/api_v1_urls.py)
                          |
      +-------------------+--------------------+
      |                   |                    |
  Authentication      Business Services     Webhooks
  (JWT, OTP)        (matching, messaging,   (idempotent,
                     communities, airtime)   WebhookEvent-backed)
      |                   |                    |
      +-------------------+--------------------+
                          |
                      PostgreSQL
                          |
              integrations/africastalking/
               /        |         \        \
             sms      ussd      airtime    voice
```

**Rule enforced throughout the codebase:** the React frontend never talks
to Africa's Talking directly. It only ever talks to the Django API, which
is the only thing holding AT credentials.

```
Correct:   React -> Django -> Africa's Talking
Never:     React -> Africa's Talking
```

## Django apps

| App | Responsibility |
|---|---|
| `accounts` | Custom phone-first `User`, OTP issuing/verification, JWT auth |
| `profiles` | `Interest` catalog, `Profile` (bio/occupation/photo/interests) |
| `matching` | Compatibility scoring engine, discovery, connection requests, `Match` |
| `communities` | `Community`, `CommunityMembership`, join/leave/admin |
| `messaging` | `Conversation`/`Message`, app-vs-SMS channel routing |
| `notifications` | Outbound SMS log, in-app `Notification` feed, `WebhookEvent` idempotency ledger, AT SMS webhook receivers |
| `ussd` | Stateless USSD flow handler (`apps/ussd/services.py`) driven by AT's cumulative `text` field |
| `airtime` | `AirtimeTransaction` ledger, gifting/referral/community reward services |
| `voice` | Demo-mode voice verification; live AT Voice flow intentionally unimplemented (see `integrations/africastalking/voice.py`) |

Every app follows the same internal shape: `models.py` (data), `services.py`
(business logic / provider calls), `serializers.py` + `views.py` (HTTP
surface), `urls.py`, `admin.py`, `tests/`. Provider calls never happen
directly inside a view — they go through `apps/<app>/services.py` and then
`integrations/africastalking/<channel>.py`.

## Africa's Talking integration layer

```
backend/integrations/africastalking/
    client.py       # single place the SDK is initialized; demo-mode switch
    sms.py          # SMSService.send() / send_otp()
    ussd.py         # CON/END response formatting helpers
    airtime.py      # AirtimeService.send()
    voice.py        # VoiceService — demo-mode only, live path documented as unimplemented
    exceptions.py
```

`AT_DEMO_MODE=true` routes every provider call through a local mock that
never leaves the process (see each service's `_send_demo` method) but
follows the exact same code path a live call would, down to producing a
`provider_transaction_id`/`provider_message_id`-shaped result. Flipping to
`AT_DEMO_MODE=false` with real credentials requires **no changes** to any
app-level code — only `integrations/africastalking/*.py` talks to the SDK.

## Matching engine

`apps/matching/scoring.py` exposes one pure function:
`compatibility_score(user_a, user_b, weights=None) -> int` (0–100), combining:

- **Location** (default 30%) — exact match / neutral if either is unset
- **Shared interests** (default 35%) — Jaccard similarity over each user's `Interest` set
- **Age compatibility** (default 20%) — linear falloff over `MATCHING_MAX_AGE_DIFF` years
- **Community overlap** (default 15%) — currently a neutral placeholder; the
  weight is reserved so a real Jaccard-over-`CommunityMembership` calculation
  can be dropped in later with no caller changes

Weights are configurable via `settings.MATCHING_WEIGHTS` (env-driven). The
function is deliberately stateless and side-effect-free so it can be
swapped for an ML-based recommender later without touching any calling code
in `matching/services.py`, `matching/views.py`, or `ussd/services.py`.

## Messaging: app vs. SMS bridge

`apps/messaging/services.py::send_message` checks the recipient's
`registration_channel`:
- **Web-registered recipient** → stored as an in-app `Message`
  (`channel="app"`, `status="delivered"` immediately — this is polling-based,
  *not* pretended-real-time WebSocket chat, per the project's explicit
  requirement).
- **USSD-registered recipient** → bridged out over SMS via
  `notifications.services.send_sms_notification`, with the resulting
  `Message.status` reflecting the SMS send outcome (`sent`/`failed`).

Inbound SMS (feature-phone replies) arrive at
`POST /api/v1/webhooks/africastalking/sms/incoming/`, which resolves the
sender by phone number and routes the message into their most recently
active `Conversation`. This routing simplification (no per-conversation
reply codes) is documented in `apps/messaging/services.py` and is a
deliberate, disclosed scope reduction — see `docs/development.md`.

## USSD flow design

`apps/ussd/services.py::handle_ussd_request` is written as a pure function
of Africa's Talking's cumulative `text` field (segments separated by `*`),
not a server-side state machine — AT redelivers the *entire* input path on
every hop, so deriving the current step from that path directly is simpler
and more restart-safe than trying to keep a session object in sync. A
`USSDSession` row is still written on every request for audit/analytics,
but it is not the source of truth for navigation.

## Security-relevant design choices

- OTP codes are hashed (SHA-256) before storage; plaintext exists only
  transiently in memory between generation and SMS dispatch.
- Every webhook handler records a `WebhookEvent` keyed on the provider's own
  event ID before processing, making redelivery idempotent by construction.
- Airtime transfers go through one shared `_execute_transaction` path with
  server-side amount validation, self-gift/self-referral prevention, and a
  unique `idempotency_key` constraint at the database level (not just
  application-level checks).
- The custom `User` model is referenced everywhere via
  `settings.AUTH_USER_MODEL`, never imported directly, per Django best
  practice for swappable user models.
