# Opencode — Sprint Form Analyzer Session Notes

## Overview
Sprint analysis on right/left legs. User uploads image + selects phase + running direction. Backend measures hip/knee/ankle per leg (+ thigh separation for touchdown) and compares to phase-specific optimal ranges.

## Phases & Ranges
All angles in degrees. Hip = thigh vs vertical (`180 - signed_raw`; trailing thigh → >180). Knee = `calculate_angle(hip,knee,ankle)`. Ankle = shin vs foot. Thigh-thigh = angle between thigh vectors.

```python
RANGES = {
  "toe_off": {
    "swing":  {"hip": (97,113),  "knee": (58,80),   "ankle": (96,104)},
    "stance": {"hip": (193,204), "knee": (138,155), "ankle": (110,147)},
  },
  "mid_stance": {
    "swing":  {"hip": (126,146), "knee": (26,41),   "ankle": (108,132)},
    "stance": {"hip": (155,165), "knee": (141,149), "ankle": (79,88)},
  },
  "touchdown": {
    "swing":  {"hip": (157,168), "knee": (39,49),   "ankle": (116,130)},
    "stance": {"hip": (141,152), "knee": (146,156), "ankle": (97,105)},
    "thigh_thigh": (7, 28),  # flat key, not nested `extra`
  },
}
```

Notes:
- Swing/stance are *roles*, not anatomical sides — auto-assigned via penalty (try `SWING=right/STANCE=left` vs swapped, pick lower penalty). So anatomical right being stance vs swing doesn't matter.
- Touchdown: stance leg is in *front* (reaching), hence hip 141-152 < mid-stance 155-165. Thigh-thigh only for touchdown.

## Auth
- Frontend uses **Auth.js v5 (`next-auth@beta`)** with Google OAuth; sessions are JWTs. `frontend/auth.ts` also exposes an optional Credentials provider (`AUTH_DEV_LOGIN=1`) for local work without Google credentials.
- Browser never calls FastAPI directly. `frontend/lib/backend.ts` authenticates the Auth.js session, mints a 1-hour HS256 token with `AGOS_INTERNAL_SECRET`, and forwards it as `Authorization: Bearer`.
- Server components/actions use `backendFetch`; client uploads go through `app/api/backend/[...path]/route.ts`, which applies the same bridge.
- Backend `services/auth.py` verifies the token (`PyJWT`, requires `exp` + `sub`), upserts the local user by email, and returns the user id. `api/deps.py` exposes `get_current_user_id` / `get_current_user`.
- `X-User-Id` is no longer trusted. The dev-user fallback exists only when `AGOS_ALLOW_DEV_USER=1` (default off).
- Both sides must share the same 32+ character `AGOS_INTERNAL_SECRET`. `AUTH_SECRET`, `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET` live in `frontend/.env.local`.

## Backend
- `backend/services/pose.py`: maps HalPE26 → MediaPipe slots. Legs only: `SLOT_*_HIP/KNEE/ANKLE/HEEL/FOOT` (10 slots), `SLOT_TO_HALPE`. No nose/shoulders. `MIN_KEYPOINT_CONFIDENCE=0.5` used for drawing; low-conf keypoints carry `(-1,-1)`+`visibility`.
- `backend/services/analysis.py`: `SWING_POINTS=(24,26,28,30,32)`, `STANCE_POINTS=(23,25,27,29,31)`. Helpers guard zero-length vectors → `NaN`, `_is_visible` (visibility `<0.5` or `(-1,-1)`), `_measure_leg` returns `NaN` angles if any point invisible, `_penalty` adds `1e6` for `NaN`, `_mirror_landmarks(x→-x)`. `analyze_angles` raises `ValueError` if no confident leg. Touchdown `thigh_thigh` returns `None` on low confidence.
- `backend/main.py`: FastAPI app; CORS (`AGOS_CORS_ORIGINS`, defaults to `http://localhost:3000`), exception handlers (`repo.ValidationError`→400, `repo.ConflictError`/integrity→409, `psycopg.OperationalError`→503), includes routers, closes the DB pool on shutdown.
- `backend/api/`: `analyze` + image/file/humanization routes in `images.py`; nested session CRUD in `sessions.py`; `/me` in `users.py`; `/`+`/health` in `health.py`; `deps.py` identity; `schemas.py` Pydantic models; `serializers.py` adds `original_url`/`annotated_url`.
- `backend/services/image_service.py`: `analyze_and_store` (decode→pose→angles→save original+annotated→DB insert; cleans files on failure), `delete_image`/`delete_session`/`delete_user` (collect paths then unlink). `backend/services/storage.py`: per-user layout `users/{id}/images/{uuid}{ext}` + `{uuid}_annotated.jpg`, path-traversal guard, best-effort delete. `pose.py` caches detector/pose ONNX sessions (`lru_cache`).
- `POST /analyze` always persists (form `file`, `phase`, `direction`, optional `session_id`) and returns analysis fields + `image_id` + `annotated_image` (base64) + `original_url`/`annotated_url`. Uploads limited by `AGOS_MAX_UPLOAD_BYTES` (10 MB) → 413.
- `backend/scripts/download_models.py`: cross-platform Python alternative to the bash script; `.gitignore` covers model weights and uploads.

## Humanization (Groq + local)
- `backend/services/humanization.py` builds a metadata-only prompt (`phase`, swing/stance angles, `thigh_thigh`, rule-based feedback, `RANGES`). No image bytes are sent anywhere.
- `AGOS_HUMANIZATION_PROVIDER=auto` uses Groq when `GROQ_API_KEY` is set, otherwise the local Hugging Face model. Force with `groq` or `local`.
- Groq defaults: `AGOS_GROQ_MODEL=llama-3.1-8b-instant`, `GROQ_API_KEY` (secret). This is the deployed Render path: no torch/model weights needed.
- Local default model: `HuggingFaceTB/SmolLM2-1.7B-Instruct` (non-gated). Override with `AGOS_HUMANIZATION_MODEL`; tune `AGOS_HUMANIZATION_DEVICE` (default `cpu`) and `AGOS_HUMANIZATION_MAX_TOKENS` (default 160).
- Local heavy dependencies are optional: `pip install -r backend/requirements-llm.txt` (`transformers`, `torch`, `accelerate`). Weights download on first generation. Missing configuration/dependencies produce a 503 with instructions.
- Generation is on-demand: `POST /images/{id}/humanization/generate` stores/replaces the row via `repo.upsert_humanization` and returns it. Manual CRUD remains at `GET/PUT/PATCH/DELETE /images/{id}/humanization`.

## Frontend
- Auth: `app/(public)/login/page.tsx` (Google button + optional dev form), `app/api/auth/[...nextauth]/route.ts` (Auth.js handlers), `proxy.ts` protects `/analyzer`, `/sessions`, `/images`.
- `app/(app)/layout.tsx`: header with Analyzer/Library links + server-action logout. Root layout no longer renders a header (fixes the previous double header).
- `app/(app)/analyzer/`: server page parses `?session=<id>`, client component posts to `/api/backend/analyze`, appends `session_id`, shows annotated result and links to the saved image.
- `app/(app)/sessions/`: library browser — root/nested sessions (`?session=<id>`), create/delete session actions, image grid using proxied `annotated_url`/`original_url`, links into image detail.
- `app/(app)/images/[id]/`: persisted image detail with angle table, rule feedback, humanization card, on-demand generate button (server action), and delete.
- `lib/backend.ts`: server-side authenticated fetch, `backendJson`, `backendAssetUrl` (`/api/backend` prefix). `lib/backend-token.ts`: HS256 minting with `jose`.
- Old custom email/password login routes, `lib/session.ts`, and the orphan `/dashboard` route were removed.

## Database
- Raw SQL, `backend/db/schema.sql` — `users` (OAuth-compatible), `sessions` (nestable `parent_id`, Drive-like), `images` (`session_id NULL` = root, original filename for display, `uuid` stored path), `image_humanizations` (model metadata only: phase/angles/feedback vs RANGES).
- `psycopg[binary]` + `psycopg-pool` + `python-dotenv`; `DATABASE_URL` (Neon or localhost); pool in `backend/db/connection.py`.
- CRUD: `backend/db/repository.py` (users, nested sessions + cycle prevention, images, humanizations). Every user-scoped query filters `user_id`; cross-user session/image refs raise `ValidationError`. `backend/db/init.py` + `scripts/init_db.py` create DB and apply schema. Composite FKs `(session_id,user_id)`/`(image_id,user_id)`, `UNIQUE (id,user_id)`, `updated_at` triggers, unique `(user_id,stored_filename)`. `list_image_files` (recursive subtree) feeds file cleanup. Wired into `/analyze` and all HTTP routes.

## Endpoints
- `POST /analyze`
- `GET/POST /sessions`, `GET/PATCH/DELETE /sessions/{id}`, `GET /sessions/{id}/images`
- `GET /images`, `GET/PATCH/DELETE /images/{id}`, `GET /images/{id}/file`, `GET /images/{id}/annotated`
- `GET/PUT/PATCH/DELETE /images/{id}/humanization`, `POST /images/{id}/humanization/generate`
- `GET/PATCH /me`, `GET /health`, `GET /`

## Frontend API bridge
- `app/api/backend/[...path]/route.ts` forwards GET/HEAD/POST/PUT/PATCH/DELETE to `AGOS_API_URL`, attaching `Authorization: Bearer <minted token>`. Multipart uploads are forwarded as an `ArrayBuffer` with the original content type.
- Client components use `/api/backend/...`; server components use `backendFetch` with the same identity. Backend-relative asset paths are wrapped by `backendAssetUrl`.
- `next.config.ts` needs no rewrite; the proxy route is explicit and works in dev and on Vercel.

## Setup
- Backend: `python backend/scripts/init_db.py [DATABASE_URL]`.
- Env: root `.env.example` (backend: `DATABASE_URL`/`AGOS_DATABASE_URL`, `AGOS_UPLOAD_DIR`, `AGOS_MAX_UPLOAD_BYTES`, `AGOS_INTERNAL_SECRET`, `AGOS_ALLOW_DEV_USER`, `AGOS_DEV_USER_EMAIL`, `AGOS_CORS_ORIGINS`, humanization settings). Frontend: copy `frontend/.env.example` to `frontend/.env.local` (`AUTH_SECRET`, `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, matching `AGOS_INTERNAL_SECRET`, `AGOS_API_URL`, optional `AUTH_DEV_LOGIN`).
- Google OAuth redirect URI: `http://localhost:3000/api/auth/callback/google` (plus the production domain).

## Testing
- Backend: `cd backend && .venv/bin/python -m pytest tests -q` — **39 tests** (repository, storage, service validation, humanization prompt, auth bridge/401, full API via `TestClient`; `/analyze` uses a monkeypatched analyzer so no ONNX needed). Uses `TEST_DATABASE_URL`, default `postgresql:///agos_test`; creates/applies schema automatically.
- Frontend: `npx tsc --noEmit`, `npm run lint`, `AUTH_SECRET=... AGOS_INTERNAL_SECRET=... npx next build`.
- Synthetic pose smoke remains available for the real ONNX pipeline; `python -m compileall -q api db services scripts tests main.py`.

## Status / Remaining
- Done: analysis pipeline; DB CRUD; persisted originals/annotated JPEGs; recursive cleanup; sessions/images/humanizations API; Google OAuth via Auth.js; frontend↔backend token bridge; session/gallery + image detail UI; on-demand Groq/local coach feedback; Render/Neon/Vercel deployment; 41 tests.
- Remaining: set `GROQ_API_KEY` on Render; upload a real full-body sprint photo for final smoke test; optional chat extension.

## Decisions
- **Auth:** Google OAuth through Auth.js, with a short-lived internal JWT to FastAPI. Keeps the browser off the API origin, avoids trusting user-supplied `X-User-Id`, and leaves room for other providers. Dev fallback is explicit and off by default.
- **Humanization model:** Groq (`llama-3.1-8b-instant`) for the free Render deployment; no torch or model weights on the host. Local SmolLM2-1.7B remains available for development via `AGOS_HUMANIZATION_PROVIDER=local`. Metadata-only prompts keep images out of the LLM request.
- **Direction (ltr/rtl):** explicit selector, not auto-detected. Two leg-swap candidates are still tried automatically.
- **Storage:** DB holds metadata/paths only; JPEGs stay under `backend/uploads/` (or `AGOS_UPLOAD_DIR`).
- **DB/hosting:** raw SQL, no ORM/Alembic. Neon for hosted Postgres, localhost fallback. FastAPI on Render (long-running ONNX sessions), Next.js on Vercel.

## Gotchas
- Hip >180 means thigh trailing behind vertical (toe-off stance 193-204). Assumes image y+ down.
- User must set direction correctly for mirrored photos — no auto fallback.
- `_SLOT_TO_HALPE` ↔ `PHASES` values must stay in sync (`toe_off`/`mid_stance`/`touchdown`).
- `AGOS_INTERNAL_SECRET` mismatch → every API request 401. Rotate it on both sides together.
- Set `AGOS_ALLOW_DEV_USER=0` outside local development.
- Humanization on Render uses Groq and needs `GROQ_API_KEY`; local mode instead needs `requirements-llm.txt` and enough RAM for model weights.
- Models/uploads are gitignored: first-time setup must run `python backend/scripts/download_models.py`; local humanization additionally needs `requirements-llm.txt`, while deployment uses Groq.
- Backend-relative URLs (`/images/...`) must be prefixed with `/api/backend` on the frontend (`backendAssetUrl`).
