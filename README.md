# ĀGOS

[![CI](https://github.com/mikledez/agos/actions/workflows/ci.yml/badge.svg)](https://github.com/mikledez/agos/actions/workflows/ci.yml)

Sprint form analysis from a single photo. Upload a side-on photo, pick the
phase (toe off, mid stance or touchdown) and the running direction. ĀGOS finds
the athlete's pose, measures hip, knee and ankle angles for the swing and
stance legs, and compares them with reference ranges for that phase.

You get:

- an annotated photo with green **target zones** showing where each body part
  should be, and numbered red markers for what to fix
- angle cards in degrees, for coaches
- plain-language problems such as "Knee too straight, Toes pointing down"
- on-demand AI coaching feedback and a chat for each image

## Architecture

```
Browser ──► Next.js (Vercel) ──► FastAPI (Render) ──► Postgres (Neon)
            Auth.js Google login     ONNX pose models       users, folders,
            server-side API proxy    angle analysis         images, chat
                                     Groq LLM (text only)
```

- The browser only talks to Next.js. The server checks the Auth.js session,
  signs a short-lived internal JWT, and calls FastAPI with it. The API is
  never called directly from the browser.
- **Pose:** a two-stage, top-down pipeline. YOLOX-nano finds the person,
  then RTMPose-m (HalPE26 keypoints, including heels and toes) finds the
  keypoints. Both use pretrained weights and run on CPU with ONNX Runtime.
- **Analysis:** swing and stance leg roles are assigned automatically. Angles
  are compared with ranges for each phase, and both running directions are
  handled by mirroring.
- **AI feedback:** only the analysis results are sent to Groq, never the
  image itself.
- **Storage:** images and their small thumbnails are stored in Postgres. An
  image is deleted after 48 hours without activity. Inside an athlete folder
  only the full-size photo is removed; the measurements and thumbnail stay so
  progress can be tracked over time.
- **Athletes:** an athlete is a folder that shows a form score over time
  (share of measured joints in range) and each joint's angle against its
  target band, per phase, across all its subfolders.

## Tech stack

| Layer    | Tech |
|----------|------|
| Frontend | Next.js 16 (App Router, server actions), Auth.js v5, shadcn/ui, Tailwind v4 |
| Backend  | FastAPI, ONNX Runtime, OpenCV, NumPy, psycopg 3, raw SQL |
| Database | PostgreSQL (Neon in production) |
| AI text  | Groq `openai/gpt-oss-20b`, with an optional local Hugging Face model |
| CI/CD    | GitHub Actions; Render deploys only after CI passes; Vercel |

## Run locally

Requirements: Python 3.12, Node 22 and a local PostgreSQL.

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/download_models.py        # ONNX weights, kept out of git
cp ../.env.example ../.env               # then fill in the values
python scripts/init_db.py                # creates the database and schema (safe to re-run)
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env.local               # AUTH_SECRET, Google OAuth, AGOS_INTERNAL_SECRET
npm run dev
```

`AGOS_INTERNAL_SECRET` must be the same 32+ character value in both env files.
For local development without Google credentials, set `AUTH_DEV_LOGIN=1`.

## Tests

```bash
cd backend && python -m pytest tests -q     # needs Postgres; uses TEST_DATABASE_URL
cd frontend && npx tsc --noEmit && npm run lint && npm run build
```

The backend tests cover the database layer, authentication, every API route,
angle measurement and feedback, and the overlay geometry. One overlay test
re-measures each drawn target zone and checks that it matches the reference
range in both directions. The pose models are stubbed, so the tests need no
model weights.

CI runs both sets of checks on every push and pull request to `main` and
`staging`. Render only deploys a commit after CI passes.

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the Neon, Render and Vercel
setup.
