# ConnectLite — Database Design / ERD

All primary keys are UUIDs (except join/log tables using Django's default
`BigAutoField` where a UUID adds no value). Every foreign key to the user
model uses `settings.AUTH_USER_MODEL`, never a direct import of `User`.

## Entity list and relationships

```
User (accounts)
 ├─1:1─ Profile (profiles)
 │        └─M:N─ Interest (profiles)         [through UserInterest]
 ├─1:N─ OTPVerification (accounts)            [by phone_number, not FK — see note]
 ├─1:N─ ConnectionRequest (matching)           as from_user
 ├─1:N─ ConnectionRequest (matching)           as to_user
 ├─M:N─ User (matching)                        via Match (user_low, user_high)
 ├─1:N─ CommunityMembership (communities)
 ├─1:N─ Community (communities)                 as created_by
 ├─M:N─ User (messaging)                        via Conversation (participant_low/high)
 ├─1:N─ Message (messaging)                     as sender
 ├─1:N─ Notification (notifications)
 ├─1:N─ AirtimeTransaction (airtime)            as sender (nullable — system rewards)
 ├─1:N─ AirtimeTransaction (airtime)            as recipient
 └─1:N─ VoiceVerification (voice)

WebhookEvent (notifications)   — standalone idempotency ledger, no FK to User
SMSMessage (notifications)     — standalone outbound SMS log, keyed by phone number
USSDSession (ussd)             — standalone session audit log, keyed by phone number
```

**Note on `OTPVerification`:** intentionally keyed by `phone_number` (a
plain `CharField`), not a `User` foreign key — OTPs are requested *before*
a User necessarily exists (e.g. during registration), so there's nothing to
point a FK at yet.

## Key tables

### `accounts_user`
| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| phone_number | CharField(20), unique | `USERNAME_FIELD` |
| email | EmailField, unique, nullable | |
| full_name | CharField(150) | |
| date_of_birth | DateField, nullable | |
| gender | CharField choices | |
| location | CharField(150) | |
| registration_channel | CharField choices | `web` \| `ussd` |
| is_phone_verified | Boolean | |
| is_active / is_staff | Boolean | Django auth |
| created_at / updated_at | DateTime | |

### `accounts_otp_verification`
| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| phone_number | CharField(20), indexed | |
| purpose | CharField choices | registration / login / voice_verification / password_reset |
| code_hash | CharField(64) | SHA-256 hex digest — **plaintext never stored** |
| attempts / max_attempts | SmallInt | |
| is_used | Boolean | |
| expires_at | DateTime | |

### `profiles_profile`
| Field | Type | Notes |
|---|---|---|
| user_id | UUID, PK, FK → User | 1:1 |
| bio | Text(500) | |
| occupation | CharField(100) | |
| profile_photo | ImageField, nullable | |
| interests | M2M → Interest, through `UserInterest` | |

### `matching_connection_request`
| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| from_user_id / to_user_id | FK → User | unique_together |
| status | CharField choices | pending / accepted / rejected |
| compatibility_score_snapshot | Float, nullable | score at send time |

### `matching_match`
| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| user_low_id / user_high_id | FK → User | canonical ordering, unique_together — prevents duplicate rows for a pair |
| compatibility_score | Float | |

### `communities_community` / `communities_membership`
Standard community + membership-with-role (`member`/`admin`) pattern,
`unique_together(community, user)` on membership.

### `messaging_conversation` / `messaging_message`
Same canonical-ordering pattern as `Match` for `Conversation`
(`participant_low`/`participant_high`), so a pair of users only ever has one
thread. `Message.channel` (`app`/`sms`) and `Message.status`
(`pending`/`sent`/`delivered`/`failed`) capture the app-vs-SMS bridge
explicitly rather than pretending SMS is real-time.

### `notifications_sms_message`
Outbound SMS log. `body_preview` is capped at 160 chars and — critically —
OTP dispatch never routes through this table at all (see
`apps/accounts/services.py`), so an OTP code can never end up here even
truncated.

### `notifications_webhook_event`
`(source, provider_event_id)` uniqueness is the idempotency mechanism for
every AT webhook (SMS incoming, SMS delivery, voice).

### `airtime_transaction`
| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| sender_id | FK → User, nullable | null for system-initiated rewards |
| recipient_id | FK → User | |
| amount | Decimal(10,2) | |
| purpose | CharField choices | gift / referral_reward / community_reward |
| status | CharField choices | pending / success / failed |
| provider_transaction_id | CharField, indexed | |
| idempotency_key | CharField, **unique** | DB-level replay/duplicate prevention |

## Indexes

Indexes are placed on every foreign key used in hot-path filtering
(`to_user`+`status` on `ConnectionRequest`, `recipient`+`status` and
`sender`+`status` on `AirtimeTransaction`, `conversation`+`created_at` on
`Message`, `user`+`is_read` on `Notification`) plus the natural lookup keys
used by webhooks and OTP (`phone_number`, `provider_event_id`,
`provider_message_id`).
