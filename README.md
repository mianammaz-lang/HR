# 🧠 Talent Pool Management System

AI-powered talent pool management platform with optional ERPNext integration.

- **Backend**: FastAPI + SQLAlchemy (async), deployed as a Vercel Python
  serverless function from `api/`
- **Frontend**: Next.js 14 + React + Tailwind, deployed as a normal Vercel
  Next.js app from `frontend/`
- **Database**: any Postgres (Neon, Supabase, RDS, ...) in production, or
  a local SQLite file with zero config for local development
- **Auth**: JWT + bcrypt, 6 RBAC roles

> ⚠️ **If you received this project as a copy of an earlier version**: that
> version had real database credentials and an admin password committed to
> the repo, and an authentication bypass that gave every request super-admin
> access. Both have been fixed here. If those old credentials were ever
> pushed to GitHub or shared, **rotate your database password now** —
> treat it as compromised regardless.

---

## 🚀 Deploy to Vercel

1. Push this repo to GitHub (the `.gitignore` already excludes `.env`,
   `node_modules/`, `.next/`, `venv/`, `__pycache__/`, and local `.db` files
   — double-check `.env` isn't tracked before you push).
2. Go to [vercel.com/new](https://vercel.com/new) and import the repo.
   Vercel will use the root `vercel.json`, which builds the Next.js app
   from `frontend/` and deploys `api/index.py` as a Python serverless
   function, with `/api/*` requests routed to it.
3. Add the environment variables below in **Project Settings → Environment
   Variables**, then deploy.
4. After the first deploy, create your admin user by calling the seed
   endpoint once (see **First-time setup** below).

### Required environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string, e.g. `postgresql+asyncpg://user:pass@host/db?ssl=require`. Get one free from [Neon](https://neon.tech) or [Supabase](https://supabase.com). |
| `JWT_SECRET` | Random secret for signing login tokens. Generate with `openssl rand -hex 32`. The app will refuse to start on Vercel without this set. |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins, e.g. `https://your-app.vercel.app`. |

### Environment variables for first-time admin setup

| Variable | Description |
|---|---|
| `SEED_ADMIN_EMAIL` | Email for the initial super-admin account. |
| `SEED_ADMIN_PASSWORD` | Password for that account — pick something strong. |
| `SEED_SECRET` | A one-time random secret (e.g. `openssl rand -hex 16`) required to call the seed endpoint. |

### Optional environment variables

| Variable | Description |
|---|---|
| `ERP_NEXT_URL`, `ERP_API_KEY`, `ERP_API_SECRET` | ERPNext integration. |
| `OPENROUTER_API_KEY` | Enables AI-assisted CV parsing/scoring via OpenRouter. Without it, the app falls back to the built-in (non-AI) parser. |
| `NEXT_PUBLIC_API_URL` | Leave **unset** on Vercel — the frontend calls the same-origin `/api/*` rewrite automatically. Only set this for a split deployment where the frontend and backend live on different domains. |

### First-time setup: creating the admin user

The seed endpoint is disabled until you configure it, and requires the
`SEED_SECRET` you set above as a header — so it's safe to leave deployed:

```bash
curl -X POST https://your-app.vercel.app/api/admin/seed \
  -H "X-Seed-Secret: <your SEED_SECRET value>"
```

This creates one super-admin user with `SEED_ADMIN_EMAIL` /
`SEED_ADMIN_PASSWORD`. Log in with those at `/login`. Once you've logged in
and created any other users you need from **Settings → Users**, you can
remove `SEED_SECRET` from your Vercel env vars to close the endpoint off
entirely (it responds 503 if unconfigured).

### ⚠️ A note on file storage on Vercel

CV uploads are written to `/tmp`, which is the only writable path in
Vercel's serverless environment — but `/tmp` is **ephemeral** and isn't
shared reliably across function instances or requests. This is fine to try
things out, but for production CV storage, wire `documents.py` /
`forms.py` / `webhook.py` up to real object storage such as
[Vercel Blob](https://vercel.com/docs/storage/vercel-blob) or S3.

---

## 💻 Local Development

### Quick start

```bash
cp .env.example .env
# edit .env: at minimum set DATABASE_URL (or leave it to default to a
# local SQLite file) and JWT_SECRET

./start.sh          # macOS/Linux
start.bat           # Windows
```

This installs dependencies, starts the API on `http://localhost:8000`, and
the frontend on `http://localhost:3000`. On first run, seed an admin user
the same way as in production (see above) against `http://localhost:8000`.

### Manual setup

```bash
# Backend
cd api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py                 # http://localhost:8000, docs at /api/docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

### Seeding demo data (optional)

`api/seed_demo.py` populates the database with synthetic candidates and
requisitions for exploring the UI — no real data, safe to run against a
fresh dev database:

```bash
cd api && python seed_demo.py
```

---

## 🐳 Docker

```bash
cp .env.example .env   # set DATABASE_URL and JWT_SECRET
docker-compose up -d
```

---

## 📁 Project Structure

```
├── api/
│   ├── index.py           # Vercel serverless entry point
│   ├── run.py              # local dev server runner
│   ├── seed_demo.py        # optional synthetic demo data
│   ├── requirements.txt    # Python deps (single source of truth)
│   └── app/
│       ├── main.py         # FastAPI app + router registration
│       ├── config.py       # settings (env-driven, no hardcoded secrets)
│       ├── database.py     # SQLAlchemy async engine
│       ├── models.py       # database models
│       ├── auth.py         # JWT auth + RBAC
│       ├── schemas.py      # Pydantic schemas
│       ├── routers/        # API endpoints (11 modules)
│       └── services/       # AI, ERPNext, CV parsing
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # React components
│   │   └── lib/            # API client (attaches auth token), store
│   └── package.json
├── vercel.json              # Vercel deployment config
├── docker-compose.yml        # Docker deployment
├── start.sh / start.bat      # one-command local start
└── .env.example               # copy to .env and fill in
```

There is a single backend source tree (`api/`) used for local dev, Docker,
and Vercel alike — no duplicated/drifting copies.

## 🏗️ Architecture

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (async)
- **Frontend**: Next.js 14 + React + Tailwind CSS
- **Database**: Postgres (production) or SQLite (local dev fallback)
- **Auth**: JWT tokens + bcrypt + 6 RBAC roles — enforced server-side;
  unauthenticated requests get a real `401`, not a default admin session
- **AI**: OpenRouter API for CV parsing, scoring, semantic search (optional)
- **ERP**: ERPNext integration via REST API (optional)

## 📋 Features

- CV upload with a built-in parser (no API key needed)
- AI-powered candidate scoring (0–100)
- ERPNext sync (auto above a configurable score threshold, or manual push)
- Public application forms with JD display + resume upload
- No-code filter builder (AND/OR logic)
- Semantic search
- Dashboard with analytics charts
- Role-based access (6 roles)
- Webhook API for pushing CVs in from other systems
- Application form management with expiry
- Excel/CSV export
- Duplicate detection

## 🔒 Security notes

- All API routes except `/api/health`, `/api/auth/login`, the public
  `/api/apply/*` application-form endpoints, and the gated `/api/admin/seed`
  require a valid `Authorization: Bearer <token>` header.
- The webhook endpoint (`/api/webhook/cv`) runs in open mode until you set
  an API key for it under **Settings → Webhook** — set one before relying
  on it in production, since unset it accepts CV submissions unauthenticated.
- CORS is restricted to `CORS_ORIGINS`, not `*`.
"# HR" 
