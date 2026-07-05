# ADITI

**ADITI** is a lean JEE doubt-solving pilot: upload a question image, extract text with NVIDIA MiniMax-M3, solve with SymPy, explain with MiniMax-M3, and manually review flagged answers.

Phase 0 scope: **Upload → NVIDIA MiniMax-M3 Vision OCR → SymPy → LLM explanation → human review**.

## Project structure

```
aditi/
├── backend/          FastAPI pipeline + API
├── frontend/         Next.js app (Vercel)
├── supabase/         Postgres schema
├── docker-compose.yml
└── .env.example      Docker + shared env template
```

## Prerequisites

- Node.js 20+ and Python 3.11+ (local dev), **or Docker**
- Supabase project (free tier)
- NVIDIA API key (model: `minimaxai/minimax-m3` — vision OCR + explanations; get one at https://build.nvidia.com)

## Quick start with Docker (recommended)

Supabase stays hosted — Docker runs the backend and frontend only.

```bash
cd aditi
cp .env.example .env
# Edit .env with your Supabase + NVIDIA keys

docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). Backend API: [http://localhost:8000/health](http://localhost:8000/health).

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend | 8000 |

Stop: `docker compose down`

**Notes:**
- Root `.env` feeds both containers via `docker-compose.yml`.
- `NEXT_PUBLIC_*` vars are baked into the frontend image at build time. After changing them, rebuild: `docker compose up --build`.
- For local dev without Docker, copy the same values into `backend/.env` and `frontend/.env.local`.

## 1. Supabase setup

1. Create a project at [supabase.com](https://supabase.com).
2. Run `supabase/schema.sql` in the SQL Editor.
3. Create a **private** storage bucket named `question-images`.
4. Enable Email auth in Authentication → Providers.
5. Copy these values:
   - Project URL
   - Anon key
   - Service role key
   - JWT secret (Project Settings → API → JWT Secret)

## 2. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
uvicorn app.main:app --reload --port 8000
```

Required env vars (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side DB/storage access |
| `SUPABASE_JWT_SECRET` | Validate frontend auth tokens |
| `NVIDIA_API_KEY` | Vision OCR, problem modeling, and explanations |
| `NVIDIA_MODEL` | e.g. `minimaxai/minimax-m3` |
| `ADMIN_EMAILS` | Comma-separated admin emails for `/admin` |
| `CORS_ORIGINS` | e.g. `http://localhost:3000` |

API endpoints:

- `GET /health` — health check
- `POST /api/questions` — upload image (auth required)
- `GET /api/questions/{id}` — poll question status
- `GET /api/admin/questions` — review queue (admin only)

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Frontend env:

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `NEXT_PUBLIC_API_URL` | Backend URL (default `http://localhost:8000`) |

## 4. Confidence flags

| Flag | Meaning |
|------|---------|
| `verified` | SymPy solved and verified — safe to show |
| `unverified` | LLM-only answer — shown with warning |
| `needs_review` | Low OCR confidence or solver disagreement — no bare final answer |

You are the review queue at pilot scale. Use `/admin` to spot-check flagged questions.

## 5. Deploy (when ready)

- **Frontend:** Vercel — set root to `frontend/`, add env vars
- **Backend:** Render or Fly.io — deploy `backend/`, set env vars
- **Database:** Supabase (already hosted)

Update `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` to production URLs.

## Roadmap

| Phase | Scope |
|-------|-------|
| **0 (current)** | NVIDIA MiniMax-M3 Vision OCR → SymPy → LLM explanation → manual review |
| 1 | PYQ retrieval corpus + Wolfram escalation |
| 2 | Vision LLM figures, Physics modeling, feedback |
| 3 | Full-scale architecture if pilot succeeds |

## Local development flow

1. Start backend on port 8000
2. Start frontend on port 3000
3. Sign up / sign in
4. Upload a JEE algebra/calculus question image
5. Watch status update on the question page
6. Review flagged items in `/admin`
