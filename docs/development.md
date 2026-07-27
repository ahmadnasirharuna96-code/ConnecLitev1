# ConnectLite — Development Notes

## Environment constraints this build was produced under

This codebase was written in a sandboxed environment with **no network
access** — no `pip install`, no `npm install`, no live Django server, no
Docker daemon, no database. Every file was hand-written and syntax-checked
(`python -m py_compile` on every backend `.py` file, `node --check` plus
manual/bracket-balance review on frontend `.js`/`.jsx` files), but **none
of it has actually been executed**. Please treat the first real
`pip install -r requirements.txt && python manage.py migrate && pytest`
and `npm install && npm run dev` as genuine QA, not a formality — report
anything that breaks.

## Bugs already found and fixed during self-review

- **Webhook URL namespacing.** `config/api_v1_urls.py` originally included
  `notifications.webhook_urlpatterns` and `voice.webhook_urlpatterns` as
  bare lists via `include(webhook_urlpatterns)`. Django only applies a
  module's `app_name` when you `include()` the *module* (or its dotted
  path) — including a bare list of `path()` objects gives those routes no
  namespace at all, which would have silently broken
  `reverse("notifications:sms-incoming-webhook")` and
  `reverse("voice:voice-webhook")` (used throughout the test suite). Fixed
  by including `(webhook_urlpatterns, "notifications")` /
  `(webhook_urlpatterns, "voice")` tuples instead.
- **USSD webhook response format.** An early draft returned Africa's
  Talking's required plain-text `CON`/`END` response via DRF's `Response`
  class, which would have JSON-encoded it (wrapping it in quotes) via the
  default renderer instead of sending raw text. Fixed by returning a plain
  `django.http.HttpResponse` instead, which bypasses DRF's content
  negotiation/rendering entirely.
- **Docker Compose service networking.** The backend's `.env` defaults
  `DB_HOST` to `localhost`, which inside a container refers to the
  container itself, not the `db` service. `docker-compose.yml` now
  explicitly overrides `DB_HOST`/`DATABASE_URL` to point at the `db`
  service name for the `backend` container.

## Deliberately reduced scope (documented, not silently dropped)

Per the project's own hackathon-strategy guidance ("recommend reducing
scope rather than producing fragile code"), the following were scoped down
rather than half-implemented:

1. **Referral rewards.** ~~Not yet wired into registration~~ — **now wired**
   (see commit history). `RegisterSerializer` accepts an optional
   `referred_by_code`; every user gets an auto-generated, unique 6-character
   `referral_code` (excludes ambiguous characters like `0`/`O`/`1`/`I` since
   it may be read aloud or typed over USSD/SMS). The reward fires in
   `VerifyOTPView` — deliberately on **phone verification**, not bare
   registration, so an unverified/fake number can't trigger a payout. Still
   not wired into the **USSD** registration flow (kept out to avoid
   destabilizing the already-tested USSD flow within this session) — that's
   the one remaining piece if USSD-originated referrals matter for the
   demo.
2. **Live Africa's Talking Voice.** See `docs/africastalking.md` — the
   outbound-call flow needs the current AT Voice API shape confirmed
   before implementation; demo mode covers the full user-facing flow in
   the meantime.
3. **Inbound SMS conversation routing.** With no reply-code protocol,
   inbound SMS is routed to the sender's *most recently active*
   conversation (see `apps/messaging/services.py::deliver_inbound_sms`).
   This is correct for the demo's single-conversation-per-feature-phone-user
   story but would misroute a feature-phone user with multiple concurrent
   conversations. A `R <code> <message>` reply-code protocol is the
   natural next step if that becomes a real use case.
4. **Guest USSD browsing.** The brief's initial USSD welcome screen shows
   a "Find Connections" option even for unregistered numbers; this build
   requires registration first (matching requires a `Profile`, which
   requires a `User`). Documented in `apps/ussd/services.py`.

## Local setup checklist

```bash
cp .env.example backend/.env
# edit backend/.env: DJANGO_SECRET_KEY, DB_* (or DATABASE_URL)

cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations   # migration files are NOT pre-generated in this build
python manage.py migrate
python manage.py createsuperuser
pytest                             # run the full test suite
python manage.py runserver

cd ../frontend
npm install
npm run dev
```

**Important:** this build does not include pre-generated Django migration
files (only `migrations/__init__.py` in each app) — they were not created
because doing so requires actually running `makemigrations` against a
configured Django environment, which this sandbox couldn't do. Run
`python manage.py makemigrations` yourself as the first real step; review
the generated migrations before applying them, as with any Django project.

## Code layout conventions

- `apps/<name>/services.py` is where business logic and provider calls
  live — views stay thin (parse request → call service → serialize
  response). This is deliberate so the same logic is reachable from REST
  views, the USSD flow, and tests without duplication (e.g.
  `matching.services.send_connection_request` is called from both
  `matching/views.py` and `ussd/services.py`).
- Cross-app imports inside service functions are done as local imports
  (inside the function body, not at module top) specifically to avoid
  import-time circular dependencies between apps that reference each other
  (e.g. `matching` notifying via `notifications`, `ussd` calling into
  `matching`/`messaging`/`airtime`). This is a deliberate pattern, not an
  oversight — please preserve it when adding new cross-app calls.
- Every model with a foreign key to the user references
  `settings.AUTH_USER_MODEL` as a string, never `apps.accounts.models.User`
  directly, so the custom user model swap stays valid app-wide.
