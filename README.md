# AI in Health Summit 2026 — Event Platform 

**The full event platform behind AHFID's AI in Health Summit 2026 (Abuja, 19–20 October 2026): public site, registration and payments, admin CMS, and a passwordless delegate portal.**

🔗 **Live:** https://aiinhealthsummit.org

<!-- ![Home](docs/home.png) ![Admin](docs/admin.png) ![Delegate portal](docs/portal.png) -->

### Highlights

- **Four surfaces in one MERN + TypeScript app:** a public site, an admin CMS, a delegate portal, and the API.
- **Registration and payments:** attendee, exhibitor, sponsor, and volunteer registration, abstract submission, and **Paystack** payments with idempotent write endpoints.
- **Role-based admin CMS:** four roles (super admin, content editor, registrations officer, viewer) covering registrations, content, payments, check-in, and analytics.
- **Delegate portal:** magic-link (passwordless) sign-in, QR e-tickets, a delegate directory, and meeting requests.
- **Integrations:** Microsoft Graph email, Web Push notifications, and Cloudinary media.
- **Production practices:** CI (typecheck, test, and build on every PR), Vitest + Supertest tests, multi-stage Dockerfiles, Docker Compose, GA4 analytics, and SEO prerendering.

**Stack:** React · Vite · TypeScript · Node.js · Express · MongoDB / Mongoose · Paystack · Microsoft Graph · Cloudinary · Web Push · Docker · GitHub Actions

**Built by** Fowosere Ademola Abraham ([@Zionnaire](https://github.com/Zionnaire)) for [AHFID](https://github.com/AHFIDAILabs).

---

## Developer Guide


The event platform for the AI in Health Summit 2026 (Abuja, Nigeria, 19–20 October
2026), convened by AHFID. A MERN app with four surfaces:

- **Public site** (`frontend`, `/`) — marketing pages, registration (attendee /
  exhibitor / sponsor / volunteer), abstract submission, Paystack payment.
- **Admin CMS** (`frontend`, `/admin`) — role-gated back office for registrations,
  content, payments, check-in, analytics. Four roles: `super_admin`,
  `content_editor`, `registrations_officer`, `viewer`.
- **Delegate portal** (`frontend`, `/portal`) — magic-link (passwordless)
  self-service for confirmed delegates: e-ticket/QR, directory, meeting requests.
- **API** (`backend`) — Express + TypeScript + MongoDB/Mongoose.

## Prerequisites

- Node.js 20+
- Either a MongoDB connection string, **or** nothing at all — leaving `MONGO_URI`
  unset in dev spins up an ephemeral local MongoDB automatically (see
  [Local development](#local-development) below).

## Repository layout

```
backend/    Express API — see backend/.env.example for every config var
frontend/   React + Vite app (public site, admin CMS, delegate portal)
docker-compose.yml   Local full-stack Docker environment (alternative to npm run dev)
.github/workflows/ci.yml   Typecheck + test + build, on every push/PR
```

## Local development

Two terminals, no Docker required:

```bash
# Backend — http://localhost:5000
cd backend
cp .env.example .env   # every var is documented inline; the defaults work as-is for local dev
npm install
npm run dev

# Frontend — http://localhost:5173
cd frontend
cp .env.example .env
npm install
npm run dev
```

Leaving `backend/.env`'s `MONGO_URI` blank is deliberate for local dev: the backend
starts its own ephemeral MongoDB (via `mongodb-memory-server`) persisted to
`backend/.mongo-data/`, so there's nothing to install or run separately. Point
`MONGO_URI` at a real MongoDB Atlas connection string for staging/production, or
whenever you want data to survive a `.mongo-data/` deletion.

Similarly, leaving the Microsoft Graph (`MS_*`), Paystack (`PAYSTACK_*`), and Web
Push (`VAPID_*`) vars blank disables those integrations gracefully — emails/pushes
are logged instead of sent, and Paystack payment always auto-succeeds. This is the
normal way to run the app locally without needing live credentials for everything.

The one exception is **Cloudinary** (`CLOUDINARY_*`) — every profile/logo photo
upload (admin settings, delegate portal, speakers, partners, innovations) goes
straight there, with no local-disk fallback. Leaving these blank doesn't degrade
gracefully like the others; the upload endpoint returns a clear 503 instead, since
there's no safe fake image URL to hand back to a picker expecting a real one. Set
real values (a free Cloudinary account's dashboard has them under Account Details)
to exercise any image-upload flow locally.

The first time the backend boots with no `MONGO_URI` set, it auto-seeds a
`super_admin` (`SEED_SUPER_ADMIN_EMAIL`/`SEED_SUPER_ADMIN_PASSWORD` in `.env`,
defaults documented there). Against a real database (`MONGO_URI` set), run the seed
script explicitly instead: `npm run seed` (backend).

### Docker alternative

```bash
docker compose up --build
```

Runs backend (`:5000`), frontend (`:5173`, served via nginx), and a real MongoDB
container together. Uses placeholder secrets defined in `docker-compose.yml` —
fine for local use, not for anything shared or deployed.

## Tests

```bash
cd backend && npm test    # Vitest + Supertest, against an ephemeral in-memory MongoDB
cd frontend && npm test   # Vitest + React Testing Library
```

Coverage is deliberately not exhaustive — it targets the flows most likely to
break silently and matter most if they did: idempotency of every public write
endpoint (registration, payment, access codes, newsletter), auth/RBAC, and
check-in. `npm run test:coverage` in either package generates an HTML report
under `coverage/`.

## CI

`.github/workflows/ci.yml` runs on every push and pull request: `npm run
typecheck`, `npm test`, and `npm run build` for both packages. A failing check
blocks merging (once branch protection is turned on for this repo — not something
this workflow file itself controls).

## Deploying

Both `backend/Dockerfile` and `frontend/Dockerfile` are multi-stage and
platform-agnostic (Render, Railway, Fly.io, a plain VPS, etc. all work). Points
that need a real decision at deploy time, not left to guesswork here:

- **`MONGO_URI`** — a real MongoDB Atlas (or self-hosted) connection string.
  Required; the backend refuses to boot without it once `NODE_ENV` is `staging` or
  `production` (see `backend/src/config/env.ts`).
- **`COOKIE_SAME_SITE`** — defaults to `lax`, which works as long as the frontend
  and backend share a registrable domain (e.g. `app.example.com` /
  `api.example.com`). If they end up on genuinely unrelated domains (no shared
  suffix — e.g. separate platforms' default `*.vercel.app` / `*.onrender.com`
  URLs), set this to `none` instead, or auth cookies silently stop being sent on
  cross-site API calls. See the comment on this var in `backend/src/config/env.ts`.
- **`CLOUDINARY_CLOUD_NAME`/`CLOUDINARY_API_KEY`/`CLOUDINARY_API_SECRET`** — real
  Cloudinary credentials, required once `NODE_ENV` is `staging` or `production`
  (same boot-time gate as `MONGO_URI`). Every profile/logo photo upload (admin
  settings, delegate portal, speakers, partners, innovations) goes straight to
  Cloudinary — nothing is ever written to the container's local disk, so this isn't
  affected by a platform's filesystem being ephemeral across redeploys.
- **`MS_TENANT_ID`/`MS_CLIENT_ID`/`MS_CLIENT_SECRET`/`MS_SENDER_EMAIL`** — real
  Microsoft Graph app-only credentials, required once `NODE_ENV` is `staging` or
  `production` (same boot-time gate as `MONGO_URI`). Without these, no real email
  (password resets, magic links, access codes, confirmations) ever sends.
- **`PAYSTACK_SECRET_KEY`/`PAYSTACK_PUBLIC_KEY`** — real Paystack keys. Without
  them, payment "succeeds" automatically in the dev-fallback path — fine for
  staging demos, never acceptable for a real production launch.
- **`VITE_API_URL`** (frontend build arg/env var) — the backend's real public URL,
  baked into the frontend bundle at *build* time, not read at runtime.

Every other required/optional var, and what each one actually controls, is
documented inline in `backend/.env.example` and `frontend/.env.example`.
