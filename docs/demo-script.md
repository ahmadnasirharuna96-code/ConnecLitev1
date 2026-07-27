# ConnectLite — Hackathon Demo Script (3–5 minutes)

## Setup (before judges arrive)

- `AT_DEMO_MODE=true` in `backend/.env` — every SMS/Airtime/Voice call is
  simulated but follows the real code path (no live AT sandbox required).
- Have two browser windows/devices ready: one for the "smartphone user",
  one for viewing the admin panel (`/admin/`) to show the USSD/SMS session
  data landing in the same database in real time.
- Pre-create one feature-phone user via the USSD flow (see step 3) so
  "My Matches" has something to show without waiting live, or run it live
  if time allows — it's fast.

## 1. The problem (30s)

> "Most social and dating apps assume you have a smartphone, mobile data,
> and stable internet. That's not true for a huge number of people across
> Africa. ConnectLite is one social graph — dating, friendship,
> communities — reachable from a smartphone *or* a basic feature phone,
> through USSD and SMS."

## 2. Smartphone journey (60–90s)

1. Land on `/` — point out the smartphone↔feature-phone visual.
2. Register a new account (`/register`) — name, phone, password, DOB,
   gender, location.
3. OTP screen — in demo mode, no real SMS goes out; open the Django admin
   or server logs to show the OTP being generated and "dispatched"
   (masked phone number, demo tag) rather than typing a fabricated code —
   this is honest about what demo mode does.
4. Land on **Discover** — show the ranked candidate list with
   compatibility scores, explain the four-factor scoring (location,
   interests, age, community-reserved).
5. Tap **Connect** on someone → if it's mutual, show the instant "It's a
   match!" — otherwise show the pending request on **Matches**.

## 3. The innovation: feature-phone user (60–90s)

This is the centerpiece — narrate it explicitly as the differentiator.

1. Simulate dialing the USSD code (via `curl` to
   `/api/v1/webhooks/ussd/` with a fresh `phoneNumber`, or a USSD
   simulator if available) — show the welcome menu.
2. Register through USSD: name → age → gender → location → confirm.
   Point out this is the *same* `User` model, same database, same
   matching engine — not a separate system.
3. From the USSD main menu, dial into **Find Connections** — show the
   top-3 ranked matches with scores, right there in a text menu.
4. Send a connection request from USSD.

## 4. The bridge: smartphone ↔ feature phone (45–60s)

1. On the smartphone side (**Messages**), send a message to the
   feature-phone user you just created.
2. Show the message row in the admin panel: `channel=sms`,
   `status=sent`, with a demo `provider_message_id` — explain that in
   live mode this is a real SMS via Africa's Talking.
3. Simulate the feature-phone user's SMS reply by POSTing to
   `/api/v1/webhooks/africastalking/sms/incoming/` with `from`/`text`.
4. Refresh **Messages** on the smartphone side — the reply appears,
   tagged "via SMS" — this is the smartphone ↔ ConnectLite ↔ feature-phone
   loop closing.

## 5. Airtime as a social reward (30s)

1. On **Airtime**, gift a small amount to the match from earlier.
2. Show the transaction land as `success` (demo mode) with a
   `DEMO-AT-...` provider ID, and the transaction history list.
3. Mention the abuse checks running underneath (self-gift blocked,
   min/max enforced, idempotency key) without demoing them live unless
   there's time.

## 6. Communities (optional, if time remains, 20s)

Quickly show creating/joining a university or interest community —
tie back to "even without internet, you're still part of your campus or
professional network."

## 7. Close — business model & roadmap (20–30s)

> "Freemium membership, community subscriptions for universities and
> organizations, airtime commission, verified business communities. The
> free tier — including full USSD/SMS access — never goes away; that's
> the accessibility mission. Next: wiring the referral-reward system into
> registration, and a verified Africa's Talking Voice integration once
> sandbox access is confirmed."

## Honesty notes for Q&A

If asked "did you test this live against Africa's Talking":
be upfront — this build was developed without live sandbox access to AT in
this particular working session; demo mode exercises the exact same code
paths minus the actual provider call, and flipping `AT_DEMO_MODE=false`
with real credentials requires no code changes, only environment
variables (point to `docs/africastalking.md`).
