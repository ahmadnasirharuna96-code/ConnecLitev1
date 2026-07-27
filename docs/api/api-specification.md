# ConnectLite — API Specification (v1)

Base URL: `/api/v1/`. All authenticated endpoints expect
`Authorization: Bearer <access_token>`. All responses are JSON except the
USSD webhook, which returns `text/plain` per Africa's Talking's contract.

## Auth (`apps/accounts`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register/` | none | Web/smartphone registration |
| POST | `/auth/login/` | none | Phone + password login (blocked until phone verified) |
| POST | `/auth/logout/` | required | Blacklists the given refresh token |
| POST | `/auth/refresh/` | none | SimpleJWT token refresh |
| POST | `/auth/request-otp/` | none | Issues an OTP (never returns the code) |
| POST | `/auth/verify-otp/` | none | Verifies OTP; issues JWT tokens on success |
| GET | `/auth/me/` | required | Current user |

## Profiles (`apps/profiles`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET/PATCH | `/profile/` | required | Own profile (multipart for photo upload, or JSON) |
| GET | `/profile/<user_id>/` | required | Public view of another user (no phone/email) |
| GET | `/interests/` | required | Interest catalog |

## Matching (`apps/matching`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/discover/` | required | Ranked candidates with compatibility scores *(deviation from the literal brief — see note below)* |
| GET | `/matches/` | required | Confirmed matches |
| POST | `/matches/request/` | required | Send a connection request (`to_user_id`) |
| GET | `/connections/?direction=incoming\|outgoing` | required | List connection requests |
| POST | `/connections/<id>/respond/` | required | `{"action": "accept"\|"reject"}` |

> **Documented deviation:** the brief's endpoint list only specifies
> `GET /matches/` and `POST /matches/request/`. `GET /discover/` was added
> because "discover compatible users" is an explicit product requirement
> that doesn't fit `/matches/`'s semantics (confirmed matches, not
> candidates). No endpoints from the brief were removed.

## Communities (`apps/communities`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET/POST | `/communities/` | required | List / create (creator becomes admin) |
| GET | `/communities/<id>/` | required | Detail |
| POST | `/communities/<id>/join/` | required | Idempotent join |
| POST | `/communities/<id>/leave/` | required | Leave |
| GET | `/communities/<id>/members/` | required | Member list with roles |

## Messaging (`apps/messaging`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/conversations/` | required | List conversations, newest first |
| GET | `/conversations/<id>/messages/` | required | Messages in a thread |
| POST | `/messages/` | required | `{"to_user_id", "content"}` — routes to app or SMS automatically |

## Airtime (`apps/airtime`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/airtime/gift/` | required | `{"recipient_phone", "amount", "idempotency_key"?}` |
| GET | `/airtime/transactions/` | required | Transactions sent or received by the caller |

## Voice (`apps/voice`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/voice/verification/start/` | required | Demo-mode only — see `docs/africastalking.md` |

## Notifications (`apps/notifications`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/notifications/` | required | In-app notification feed |
| POST | `/notifications/sms/` | admin only | Send an arbitrary SMS (internal/testing use) |

## Webhooks (Africa's Talking → ConnectLite)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/webhooks/africastalking/sms/incoming/` | none (public, provider-called) | Inbound SMS from feature phones |
| POST | `/webhooks/africastalking/sms/delivery/` | none | Delivery status reports |
| POST | `/webhooks/ussd/` | none | USSD session webhook — returns `text/plain`, not JSON |
| POST | `/webhooks/voice/` | none | Voice callback placeholder (not exercised by demo-mode flow) |

All webhook handlers are idempotent via the `WebhookEvent` model — a
redelivered webhook with the same provider event ID is a no-op.

## Interactive docs

`GET /api/docs/` (Swagger UI, via drf-spectacular) and `GET /api/schema/`
(raw OpenAPI schema) are available once the server is running — generated
from the actual serializers/views, so they stay accurate as the API
evolves.
