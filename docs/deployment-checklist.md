# Production deployment checklist (Render + Neon)

Verified locally on 2026-10-21 with `DEBUG=False python manage.py check --deploy`
→ **0 issues**. Live re-check is required after the next push/merge.

## 1. Environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `SECRET_KEY` | yes | Long random value; never commit. |
| `DEBUG` | yes | Must be `False` in production. |
| `ALLOWED_HOSTS` | yes | Comma-separated, e.g. `smart-hospital-management-system-8zgy.onrender.com`. |
| `DATABASE_URL` | yes | Neon/Render Postgres URL (`postgres://...`). Falls back to SQLite locally. |
| `CSRF_TRUSTED_ORIGINS` | yes | `https://<render-host>` (comma-separated for custom domains). |
| `CORS_ALLOWED_ORIGINS` | optional | Only if a separate frontend calls the API. |
| `EMAIL_BACKEND` / `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | for email | Use SMTP in production. Without it Django prints emails to logs. |
| `DEFAULT_FROM_EMAIL` | optional | Display name + verified sender. |
| `SMS_BACKEND` / `WHATSAPP_BACKEND` | optional | Default console backends; replace with a provider implementation when credentials exist. |
| `TELEHEALTH_MEETING_BASE_URL` / `TELEHEALTH_ROOM_PREFIX` | optional | Video room base (default `https://meet.jit.si/`, prefix `shms-`). Point at Jitsi/Daily/Zoom/Whereby — no code change. |
| `AI_API_KEY` / `AI_MODEL` / `AI_BASE_URL` | optional | Health Assistant triage. Empty key = built-in rule-based triage; set to use any OpenAI-compatible endpoint. |

## 2. Build and start

- **Build:** `./build.sh` (installs, `collectstatic`, `migrate`, `createcachetable`).
- **Start:** `gunicorn smart.wsgi` (Render supplies `$PORT`).
- WhiteNoise serves `staticfiles/`; `collectstatic` must run on every deploy.
- `createcachetable` is idempotent and required for the database cache used by rate limiting.

## 3. Security review

- [x] `SECURE_SSL_REDIRECT`, HSTS (1 year, preload), secure session/CSRF cookies active when `DEBUG=False`.
- [x] `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` prevents redirect loops on Render.
- [x] `X_FRAME_OPTIONS=DENY`, nosniff, same-origin referrer policy.
- [x] Login/register/reset/resend/2FA/demo rate limits share the database cache across workers.
- [x] Uploads restricted by extension, size and real image sniffing.
- [x] Role guards on billing, pharmacy, lab processing, IPD and audit log.
- [x] `python manage.py check --deploy` reports 0 issues with `DEBUG=False`.

## 4. Database and backups

- [ ] Migration ran successfully on Neon (`migrate` in build log).
- [ ] `python manage.py backup_data` succeeds against production; archive stored off-platform.
- [ ] Retention policy in place (`--keep`, default 7) and restore rehearsed at least once.
- [ ] Neon branch/snapshot taken before risky migrations.

## 5. Smoke tests after deploy

1. `/` homepage 200, doctor cards render, `/doctors/` filter tabs work.
2. `/demo/` four role cards → demo login lands on the correct dashboard.
3. Patient: book → cancel; invoice shows balance after a partial payment.
4. Receptionist: admit → discharge frees the bed; collect lab sample → upload result.
5. Doctor: write a record with vitals; prescription appears in pharmacy.
6. Admin: `/audit-log/` filters, `/api/appointments/` paginates, admin dashboard metrics.
7. Login with a wrong password 11 times → 429 with `Retry-After`.

## 6. Known production limits

- **Media files are ephemeral on Render's free plan.** Uploaded photos/reports vanish on redeploy.
  Use a Render persistent disk or object storage (e.g. S3/Cloudinary) before real use.
- Free instances sleep; first request after idle is slow and Neon may need a warm-up.
- Email uses the configured SMTP account; a dedicated transactional provider is preferred.
- SMS/WhatsApp use console backends until a real provider is configured.
