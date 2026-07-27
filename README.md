# ConnectLite

**Connecting everyone, even without internet.**

ConnectLite is an offline-first social & dating platform for Africa. Smartphone
users get a full web app; feature-phone users get the same social ecosystem —
dating, friendship, communities — via **USSD** and **SMS**, powered by
Africa's Talking.

> Built for the *Dating and Social Networks Solutions Hackathon*.

## Status: all 11 build phases implemented

| Phase | Scope | Status |
|---|---|---|
| 1 | Foundation — config, custom User, JWT auth, base frontend | ✅ |
| 2 | Profiles + configurable compatibility-scoring matching engine | ✅ |
| 3 | Africa's Talking SMS + idempotent webhooks, notifications, communities, messaging | ✅ |
| 4 | USSD flow (registration, discovery, matches, communities, profile, airtime, help) | ✅ |
| 5 | Airtime gifting + referral/community rewards, abuse prevention | ✅ |
| 6 | Voice — demo-mode verification (live AT call flow deliberately unimplemented, see below) | ✅ |
| 7 | Frontend — all 14 screens, design system, mobile-first responsive layout | ✅ |
| 8 | Integration pass — found & fixed a webhook-namespacing bug, Docker networking fixes | ✅ |
| 9 | QA — static/consistency checks only, see honesty note below | ⚠️ partial |
| 10 | Documentation | ✅ |
| 11 | Demo script | ✅ |

**⚠️ Honesty note:** this codebase was built in a sandboxed environment with
no network access — no `pip install`, `npm install`, Docker daemon, or live
database were available. Every file was hand-written and syntax-checked, but
**none of it has been executed**. Treat your first `pytest` run and
`docker compose up` as real QA. See `docs/development.md` for the bugs
already caught by static review and what's still unverified.

## Tech stack

- **Backend:** Python, Django, Django REST Framework, PostgreSQL, JWT (SimpleJWT)
- **Frontend:** React, Vite, Tailwind CSS
- **External services:** Africa's Talking (SMS, USSD, Airtime, Voice)
- **Infra:** Docker Compose (dev), nginx-served production frontend build, GitHub Actions CI

## Project structure

```
ConnectLite/
├── backend/
│   ├── config/                        # settings, urls, wsgi/asgi
│   ├── apps/
│   │   ├── accounts/                  # custom User, OTP, JWT auth
│   │   ├── profiles/                  # Interest catalog, Profile CRUD
│   │   ├── matching/                  # compatibility scoring, discovery, connections, Match
│   │   ├── communities/               # Community, CommunityMembership
│   │   ├── messaging/                 # Conversation/Message, app<->SMS channel routing
│   │   ├── notifications/             # SMS log, WebhookEvent idempotency, in-app feed
│   │   ├── ussd/                      # stateless USSD flow handler
│   │   ├── airtime/                   # AirtimeTransaction ledger, gifting/rewards
│   │   └── voice/                     # demo-mode voice verification
│   └── integrations/africastalking/   # sms.py, ussd.py, airtime.py, voice.py, client.py
├── frontend/
│   ├── Dockerfile                     # dev (Vite dev server)
│   ├── Dockerfile.prod                # production multi-stage nginx build
│   ├── nginx.conf
│   └── src/{api,context,components,pages}
├── docs/
│   ├── architecture/system-architecture.md
│   ├── database/erd.md
│   ├── api/api-specification.md
│   ├── africastalking.md
│   ├── security.md
│   ├── development.md
│   └── demo-script.md
├── .github/workflows/docker.yml       # CI build (no registry push until secrets configured)
├── .env.example
└── docker-compose.yml
```

## Local setup

### Prerequisites
- Python 3.12+, Node 20+, PostgreSQL 16 (or use `docker compose up db`)

### 1. Environment variables
```bash
cp .env.example backend/.env
# edit backend/.env — at minimum set DJANGO_SECRET_KEY and DB_* values
```

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations   # migrations aren't pre-generated — see docs/development.md
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
API: `http://localhost:8000/api/v1/`. Interactive docs: `http://localhost:8000/api/docs/`.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
App: `http://localhost:5173/`.

### 4. Or, everything via Docker
```bash
docker compose build
docker compose up
```
Services communicate via Docker Compose service names (not `localhost`,
which inside a container means the container itself) — see
`docs/development.md` for the specific bug this caused and how it was
fixed.

| Service | Container port | Host port |
|---|---|---|
| frontend (Vite dev server) | 5173 | 5173 |
| backend (Django dev server) | 8000 | 8000 |
| db (PostgreSQL) | 5432 | 5432 |

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose logs -f
docker compose down          # stop
docker compose down -v       # stop and wipe the Postgres volume
```

**Production frontend:** `frontend/Dockerfile.prod` is a separate
multi-stage build serving the compiled app via nginx (`frontend/nginx.conf`)
— use this for deployment, not `frontend/Dockerfile` (dev server only):
```bash
docker build -f frontend/Dockerfile.prod --build-arg VITE_API_BASE_URL=https://api.example.com/api/v1 -t connectlite-frontend ./frontend
```

**CI:** `.github/workflows/docker.yml` builds both images on every push to
`main`/PR. It does not push to any registry until `REGISTRY_HOST` /
`REGISTRY_USERNAME` / `REGISTRY_PASSWORD` secrets and the
`ENABLE_REGISTRY_PUSH` repo variable are configured — no registry URL or
namespace is assumed or fabricated.

### 5. Run backend tests
```bash
cd backend && pytest
```
~70 tests across all 9 apps. Not yet executed in this build — see the
honesty note above.

## Africa's Talking integration

All AT calls live behind `backend/integrations/africastalking/` — never
called directly from views. `AT_DEMO_MODE=true` (default) uses local mock
adapters so the whole app works without live credentials. Flip to `false`
and supply real `AT_USERNAME`/`AT_API_KEY` to go live — no business-logic
code changes required, **except Voice**, whose live call flow is
deliberately left unimplemented pending sandbox verification. Full detail:
`docs/africastalking.md`.

## Documentation index

- [`docs/architecture/system-architecture.md`](docs/architecture/system-architecture.md) — logical architecture, app responsibilities, matching engine, messaging bridge, USSD design
- [`docs/database/erd.md`](docs/database/erd.md) — entities, relationships, key tables
- [`docs/api/api-specification.md`](docs/api/api-specification.md) — full endpoint reference
- [`docs/africastalking.md`](docs/africastalking.md) — integration layer detail, demo mode, Voice scope note
- [`docs/security.md`](docs/security.md) — auth, OTP handling, webhook idempotency, airtime abuse prevention
- [`docs/development.md`](docs/development.md) — bugs found during self-review, deliberately deferred scope, setup checklist
- [`docs/demo-script.md`](docs/demo-script.md) — 3–5 minute hackathon demo flow

## Business model

- **Freemium:** basic matching/profile/communities/messaging free forever
  (the accessibility mission never goes behind a paywall); premium tier
  adds advanced matching filters and discovery.
- **Community subscriptions** for universities, organizations, professional
  associations, NGOs.
- **Airtime commission** on supported gifting/reward flows.
- **Business accounts** — verified/sponsored communities.
- **Premium verification** — optional paid verification tiers.

## Roadmap (deliberately deferred, see `docs/development.md`)

1. Wire referral rewards into **USSD** registration too (already wired for web)
2. Verified live Africa's Talking Voice integration
3. Reply-code protocol for feature-phone users with multiple open conversations
4. ML-based matching (the scoring engine's `compatibility_score` signature
   was designed for a drop-in replacement)

## License

TBD — add your hackathon team's chosen license before submission.
