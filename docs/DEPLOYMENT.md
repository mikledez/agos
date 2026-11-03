# Deployment — staging checklist

Three services: **Neon** (Postgres), **Render** (FastAPI + ONNX), **Vercel**
(Next.js). The browser only talks to Vercel; Vercel mints the internal JWT and
calls Render server-side.

## 1. Neon

1. Create a Neon project and copy the **pooled** connection string
   (`...?sslmode=require`).
2. Apply the schema once:
   ```bash
   DATABASE_URL='postgresql://...neon.tech/agos?sslmode=require' \
     python backend/scripts/init_db.py
   ```
3. Verify:
   ```bash
   DATABASE_URL='...' python backend/scripts/check_db.py
   ```
   Expect `users`, `sessions`, `images`, `image_humanizations`.

## 2. Render (FastAPI)

1. Push the repository, then create a Blueprint from `render.yaml` at the repo
   root (or point Render at this file).
2. Set the secret env vars in the dashboard:
   - `DATABASE_URL` — the Neon pooled URL.
   - `AGOS_INTERNAL_SECRET` — same 32+ char value as Vercel.
   - `GROQ_API_KEY` — from https://console.groq.com/keys.
3. `AGOS_ALLOW_DEV_USER` is `0`; never enable it in staging/production.
4. The default blueprint uses Render's **free** plan with
   `AGOS_UPLOAD_DIR=/tmp/agos-uploads`: no payment method, but image files are
   lost on redeploy/restart (metadata stays in Neon). For persistent JPEGs,
   switch to `plan: starter`, uncomment the 1 GB disk block, set
   `AGOS_UPLOAD_DIR=/var/data/uploads`, and expect the paid instance + disk.
   The free 512 MB instance can be tight for both ONNX models; if analysis is
   OOM-killed, use the Starter plan or an object-storage backend.
5. Build downloads the ONNX models via `scripts/download_models.py` (skips
   files that already exist). Models stay outside git.
6. Health check: `GET https://<service>.onrender.com/health` → `{"status":"ok","database":"ok"}`.

Coach feedback uses Groq by default in the Render blueprint:

- `AGOS_HUMANIZATION_PROVIDER=groq`
- `AGOS_GROQ_MODEL=llama-3.1-8b-instant`
- `GROQ_API_KEY=<your Groq API key>` (set as a secret in Render)

The local Hugging Face model is **not** installed by the default build. Rendering
SmolLM2-1.7B locally needs roughly 2 GB+ RAM, so use `AGOS_HUMANIZATION_PROVIDER=local`
only on a larger instance and install `requirements-llm.txt` in the build command.
If Groq is selected without `GROQ_API_KEY`, generation returns a clear 503.

## 3. Vercel (Next.js)

1. Import the repository and set **Root Directory = `frontend`**.
2. Environment variables (Production + Preview):
   - `AUTH_SECRET` — `openssl rand -base64 32`
   - `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`
   - `AGOS_INTERNAL_SECRET` — exactly the same value as Render
   - `AGOS_API_URL` — `https://<service>.onrender.com`
   - optional `AUTH_DEV_LOGIN=0`
3. Deploy. Vercel serves `/api/backend/*`, `/api/auth/*`, and the app routes.
4. Add the production callback URL in Google Cloud:
   `https://<vercel-domain>/api/auth/callback/google`
   (keep `http://localhost:3000/api/auth/callback/google` for local dev).

## 4. Google OAuth

- OAuth consent screen: External; scopes `openid`, `email`, `profile`.
- OAuth client: Web application; authorized origin is the Vercel domain and
  localhost; redirect URIs are the two callback URLs above.
- Add your Google account as a test user while the app is in testing mode.

## 5. Smoke test

```bash
curl https://<service>.onrender.com/health
```

Then in the browser: sign in with Google → create a session → upload an image
→ open the saved analysis → generate feedback (if the LLM is installed).

## Staging branch flow

```bash
git switch staging
git merge origin/landing-login   # already included on this branch
git push -u origin staging
```

Configure Vercel Preview deployments for the `staging` branch, or promote it to
production after the smoke test passes.

## Secrets rule

Commit only the `.env.example` files. Real values live in the platform
dashboards and in ignored `frontend/.env.local` / `backend/.env` files.
