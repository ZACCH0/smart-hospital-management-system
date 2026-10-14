# [PROJECT] - PROJECT STATUS — SHMS (Living Document)

> **AI WORKFLOW RULE (must follow every session):**
> 1. **START:** Read this file first before any work to know current state.
> 2. **DURING:** Update §3 Stage tracker when starting a new task.
> 3. **FINISH:** When a task is done — update §3 + §10, update `%`, `Last updated`, and commit this file with the code.
> 4. Never finish a task without updating this file.

---

## 1. Overview (what, who for, hosting, repo)

- **Project:** Smart Hospital Management System (SHMS)
- **What:** Django hospital platform — appointments, records, lab, pharmacy, billing in one place. Goal: portfolio-grade, hospital-presentable product.
- **Who for:** Patients, Doctors, Receptionists, Admins (4 roles, role-based workspaces).
- **Stack:** Django 5.2.15 + Tailwind CDN + vanilla JS + DRF + django-otp + WhiteNoise + Pillow
- **Hosting:** Render (build: `pip install + collectstatic + migrate`)
- **Live URL:** https://smart-hospital-management-system-8zgy.onrender.com
- **GitHub:** https://github.com/ZACCH0/smart-hospital-management-system
- **Branch:** work on `redesign-homepage` | live is `main` | **Developer:** Alade Zaccheous Kehinde (ZacchTech)
- **Local path:** `C:\Users\DELL-7280\Videos\PYTHON ROAD MAP\Desktop\SMART HOSPITAL\smart`
- **Completion:** **39% (11 / 28 phases)** — `████████░░░░░░░░░░░░ 39%`
- **Last updated:** 2026-10-14 | **Last pushed commit:** `38b3f5c` on `redesign-homepage` (2026-10-14) | **Health:** `manage.py check` → no issues (verified 2026-10-14)
- **WHERE WE STOPPED (2026-10-14):** User chose frontend-first — finish all frontend (6b/6c/6d) before Stage 7 QA+docs. Next = approve 6b Doctor frontend to start.

## 2. Workflow rules (the hard rules above)

- **My role:** Lead developer + designer + project manager for SHMS.
- **How I communicate:** Plain, warm, professional, honest. No jargon dumps. Brief WHY for decisions. Short sections + tables. Show only relevant code unless full file asked.
- **Hard rules:**
  1. One stage at a time. Report, then STOP for approval.
  2. No invented facts (prices, emails, names, links, reviews, policies). Use `[PLACEHOLDER]` + list in §5.
  3. Never silently delete content/assets. Move old to `/legacy/` instead.
  4. No secrets in frontend.
  5. No false tested claims. State TESTED vs NOT TESTED explicitly.
  6. On conflict between instructions/sources → STOP, ask, record here. Do not guess.
  7. Mind changes = modify current stage, no restart.
  8. Clean human-style code, comments only where useful.
- **Stage report format (mandatory):** COMPLETED / TESTED (+NOT TESTED) / FILES CHANGED / DECISIONS I NEED / KNOWN PLACEHOLDERS / NEXT STAGE → then stop.
- **Deploy rule (user 2026-10-09):** Do NOT push to `main` (live Render auto-deploys main). Work on `redesign-homepage` + deliver ZIP with README. Merge to `main` only on explicit approval.

## 3. Stage tracker (stage | scope | status | date)

| Stage | Scope | Status | Date |
|-------|-------|--------|------|
| 1 Audit only (no build) | All apps/templates, duplicate views, homepage gap | DONE | 2026-10-10 |
| 2 Figma/reference inspect | 10 previews + home.html + base nav + static + doctor data | DONE | 2026-10-13 |
| 3 Design system | tokens.css + app.css + partials, locked user choices | DONE | 2026-10-13 |
| 4 Homepage build | 13 sections in place + read-only `core/views.home` + nav CTA | DONE, awaiting visual approval | 2026-10-13 |
| 4b Doctors filter tabs | Specialty tabs (All + 8, JS-only) on homepage grid | DONE, awaiting visual approval | 2026-10-13 |
| 5 Homepage test/fix | `check` + `/` + roles + 390px mobile from user review | DONE — user approved homepage as-is, no fix notes | 2026-10-13 |
| 6 Dashboards | Admin/Doctor/Patient/Receptionist + all-pages responsive fix-pass, user approved | DONE — approved, no fix notes | 2026-10-14 |
| 6b Doctor frontend | `doctor_home` + `doctors/patient_list,patient_detail,write_medical_record,add_prescription` responsive + availability self-toggle | NEXT — awaiting approval to start | — |
| 6c Patient frontend | `patient_home` + `patients/my_appointments,my_medical_records,my_prescriptions,book_appointment,profile_settings` + `billing/patient_invoices` responsive | QUEUED | — |
| 6d Admin + shared frontend | `admin_home` + `pharmacy/*, notifications/*, 404/500/403, demo, accounts/*` polish | QUEUED | — |
| 7 QA + docs | README cleanup (Phase 27), final review (Phase 28) | DEFERRED — after 6b/6c/6d per user 2026-10-14 | — |

**Phase progress (28-phase plan):** Phases 1–11 complete; 12–28 remaining (see §10 tail list).
- [x] 1 Security Foundation · [x] 2 Multi-profile Architecture · [x] 3 Audit Logging · [x] 4 2FA (TOTP) · [x] 5 DB Performance · [x] 6 Appointment Upgrade · [x] 7 Email Verification · [x] 8 Lab Access Control · [x] 9 Doctor Appointment Restrictions · [x] 10 Demo Environment · [x] 11 UI/UX Dark Sidebar + Homepage
- [ ] 12 EMR Improvement · [ ] 13 Prescriptions · [ ] 14 Pharmacy · [ ] 15 Laboratory · [ ] 16 Billing · [ ] 17 IPD/Ward · [ ] 18 Notifications · [ ] 19 REST API Pro · [ ] 20 Dashboards & Analytics · [ ] 21 Automated Testing · [ ] 22 Audit & Security UI · [ ] 23 Backup & Recovery · [ ] 24 Multi-tenancy · [ ] 25 Hospital Registration · [ ] 26 Subscriptions · [ ] 27 Documentation (README lines 39-282 tutorial cleanup) · [ ] 28 Final Quality Review

## 4. Confirmed info (facts I approved)

| Fact | Approved |
|------|----------|
| Tracker canonical file = `PROGRESS_STATUS.md`; `PROJECT_PROGRESS.md` / `PROJECT_STATUS.md` are aliases, never create duplicates | 2026-10-09 |
| No push to `main`; work on `redesign-homepage` + ZIP delivery | 2026-10-09 |
| Contact placeholders AISLE (never invent real ones) | 2026-10-09 |
| Footer uses `[HOSPITAL_*_TO_BE_PROVIDED]` placeholders | 2026-10-13 |
| Keep AI modal + AOS + gradients on homepage as-is (no removal) | 2026-10-13 |
| Home may become a function view supplying real doctors (read-only) | 2026-10-13 |
| Services section = 8 cards (6 + Emergency & Triage + Wards & Admissions) | 2026-10-13 |
| Testimonials stay omitted | 2026-10-09 (brief) |
| Full Medlink-style doctors directory page = DEFERRED to later phase | 2026-10-13 |
| Homepage shows only real DB doctors (5); empty specialties hidden | 2026-10-13 |
| Auth mobile = form-first (mint hero hidden < lg) on register + login | 2026-10-13 |
| Public stats are demo-safe only (roles/modules/doctors/role-based) | 2026-10-09 (brief) |

## 5. Placeholders open (who must supply each)

| Placeholder | Used in | Supplier |
|-------------|---------|----------|
| `[HOSPITAL_EMAIL_TO_BE_PROVIDED]` | Homepage footer contact + emergency strip | Hospital owner |
| `[HOSPITAL_PHONE_TO_BE_PROVIDED]` | Homepage footer contact + emergency strip Call button | Hospital owner |
| `[HOSPITAL_ADDRESS_TO_BE_PROVIDED]` | Homepage footer contact block | Hospital owner |
| Seed data cleanup ("Dr" inside some first names → renders "Dr. Dr …") | DB seed / demo data | Developer (on request) |

## 6. Design / brand (colours, fonts, tone)

- **Source tokens (`static/css/tokens.css`, single source of truth):** Primary #225A5D · Primary-dark #13271E · Secondary #31798A · Accent #489D9A · Accent-light #B1CBCD · Background #F8F9FA · Deep green #37554D · Warm #A37557 (demo/upsell only, never status). Text #1c2b29 · Muted #5f6f6d · Border #dfe7e5. Success #1e7e4d · Warning #b45309 · Danger #c0392b.
- **Brief palette:** Primary #0F9D9A, Deep #087F7B, Light #E8F7F6, BG #F8FAFC, Surface #FFFFFF, Text #172033, Muted #64748B, Border #E2E8F0 (Figma reference; implementation follows tokens.css teal family).
- **Fonts:** Inter if installed, else system stack (offline-safe). Sizes: page 22 · section 17 · card 15 · body 14.5 · muted 13 · table 13.5 · label 12.5 · nav 13.5.
- **Tone:** Plain, warm, professional, honest. SHMS voice (e.g. register "Your Health, One Secure Account", login "Your Care Continues Here"). Zero Medlink wording in auth templates.
- **Quality gate:** Whitespace, subtle shadows, restrained teal, hierarchy, clean CTAs. No excessive gradients/animations/giant text/random colors/rainbow nav (exception: user chose to KEEP existing hero AI modal + AOS on homepage).
- **Components (reusable):** Button, Card, Badge, Doctor/Appointment/Stat cards, Section Header, Modal, Input, Table, Empty State, Alert, Pagination (`templates/partials/` + `static/css/app.css`).
- **Responsive:** 1440/1280/1024/768/390/375 — intentional mobile, not shrunk desktop.

## 7. Audit findings (original problems found)

- **Registration 500 on Render (CLOSED 2026-10-10):** `send_mail(fail_silently=False)` unguarded + duplicate view defs + no atomicity. Fixed: single defs, `_send_verification_email()` try/except, `transaction.atomic()` + `get_or_create` profile, hardened resend.
- **Duplicate `accounts/views.py` defs (CLOSED 2026-10-10):** `role_redirect/choose_role/register_patient` defined twice; imports duplicated. Cleaned, verified via grep.
- **Registration IntegrityError on duplicate email (CLOSED 2026-10-10):** added `clean_email` strip+lower + `email__iexact` check + `IntegrityError` guard → friendly error.
- **Invented footer contacts (CLOSED 2026-10-13):** Lagos address/phone + support@shms.com replaced with §5 placeholders.
- **Homepage gaps vs 13-section brief (CLOSED 2026-10-13):** trust strip, About, 2 service cards, Why SHMS, Doctors, How It Works, appointment/final CTAs, FAQ all missing; `#stats` mislabeled as How It Works; no Book Appointment CTA. All built 2026-10-13.
- **`home` was context-less TemplateView (CLOSED 2026-10-13):** could not supply real doctors. Superseded: read-only `core/views.home` (see §8).
- **Dead AI modal API key (OPEN, kept per user):** `home.html` Gemini call has empty `apiKey`. User chose to keep as-is 2026-10-13.
- **README polluted (OPEN):** lines 39-282 contain pasted tutorial — move to docs in Phase 27, never silently delete.
- **Dead `.gitignore` (FOUND + FIXED 2026-10-13):** file was UTF-16 encoded — git cannot parse it, so zero patterns worked. Consequence: ~125 `__pycache__/*.pyc` files AND 18 `media/` user uploads (profile photos, lab-report PDFs) got committed. Fixed: converted `.gitignore` to UTF-8 (verified via `check-ignore`), `git rm --cached` all pyc/media (working tree untouched, 0 remain tracked). Secrets check: no `.env`/sqlite ever tracked. Remaining risk: old commits still contain those files — needs history cleanup (`filter-repo`) before any public push of those commits, or leave history and go forward clean (decision needed).
- **`partials/status_badge.html` broken filter (CLOSED 2026-10-13):** used non-existent `replace` filter — latent crash on any page rendering it with data (e.g. doctor dashboard with appointments). Fixed with explicit labels (`No Show`, `In Progress`, `capfirst` for rest); all 12 statuses render-tested. Homepage never used it (inline badges).

## 8. Decisions (answered / working defaults / superseded)

**Answered:**
- 2026-10-09: canonical tracker = `PROGRESS_STATUS.md` (resolved naming conflict).
- 2026-10-09: no-push-to-`main` deploy rule + placeholders approved.
- 2026-10-13: footer → placeholders YES; AI modal/AOS → KEEP; home function view → ALLOW; services → 8 cards.
- 2026-10-13: specialty filter tabs NOW (JS-only); full doctors directory page LATER.
- 2026-10-13: this 12-section status format adopted for this file.

**Working defaults (assumed, reversible):**
- Patient booking links point to `patients:book_appointment` (login-required; anonymous users redirect to login — safe).
- Homepage doctor cards show qualification + experience (no working-hours field exists on the model).
- "View Profile" link omitted on homepage cards (no public doctor-profile route exists) — Book Appointment only.
- **DEFERRED to doctor-pages pass (user 2026-10-14):** doctor self-toggle for Available/Unavailable (one tap on doctor dashboard). Receptionist chat declined — toggle chosen instead as the coordination fix. Receptionist board already reads `available`, so no board change needed when toggle lands. Build it when we reach doctor pages.

**Superseded:**
- "No new view" brief constraint → superseded 2026-10-13 by approved read-only `core/views.home` (needed for real DB doctors; no writes, no URL-name changes).
- Old `#stats` numbers band → content moved to trust strip; section now holds How It Works steps (anchor id kept so nav still works).

## 9. Project structure (folders, where config lives, commands)

```
smart/                  # Django project root (manage.py lives here)
├── accounts/  api/  appointments/  billing/  core/  dashboard/
├── doctors/  laboratory/  medical_records/  notifications/
├── patients/  pharmacy/  prescriptions/
├── smart/              # config package (settings.py, urls.py — no views.py)
├── templates/          # home.html, base.html, accounts/, dashboard/, partials/
├── static/             # css/app.css, css/tokens.css, js/tailwindcdn.js, js/chart.umd.min.js
├── staticfiles/  media/  manage.py  requirements.txt  Procfile  build.sh  runtime.txt
../SHMS FIGMA/          # 40 JPG previews (01–43, some missing) + notwant/copyhomepage.jpeg
../.venv/               # virtualenv (use ..\.venv\Scripts\python.exe)
```

- **Opencode/agent config:** none in project (no `opencode.json`, no `.opencode/`, no `AGENTS.md`). Global `~/.config/opencode/opencode.jsonc` = defaults only.
- **Home route:** `/` → `core/views.home` (was `TemplateView`), name=`home`.
- **Commands:**
```bash
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py runserver
git status --short
git log --oneline -10
```

## 10. Last changes (dated, per stage, fixes + tests)

- **2026-10-14 (plan — frontend-first):** user chose complete frontend of everything before Stage 7. Split remainder into 6b Doctor / 6c Patient / 6d Admin+shared, Stage 7 DEFERRED. 58 templates mapped; receptionist 9 + home/auth/base already approved. Tested: no code change. NOT tested: 6b/6c/6d pages.

- **2026-10-14 (Stage 6 approval — user approved):** user replied "approved" for all-pages responsive receptionist flow, no fix notes. Tracker updated (§1, §3, §12). Tested: no code change. NOT tested: Stage 7 QA + docs (LOCKED, awaiting approval).

- **2026-10-14 (Stage 6 fix-pass — ALL PAGES RESPONSIVE, last task done):** per your "all the stuff should adjust itself": all 9 receptionist-flow pages rebuilt — All Appointments + Invoices + Lab lists now full-width (`max-w-7xl`) with scaled headers/summaries/tables; Create Invoice + Record Payment + Request Lab Test + Upload Result + Cancel + No-Show now fluid cards (`lg:max-w-2xl`) with 2-col fields on tablet+ and stacked→row buttons on phone. **Fault found + fixed:** `billing/views.create_invoice` crashed 500 on every GET (audit `log_action` referenced unsaved `invoice`) — moved inside valid-POST branch; GET 200 verified. Note: Request Lab Test stays doctor-only by design (receptionist 403 is correct). Tested: `check` clean; 5 live GETs 200, 4 object-pages parse OK, 20/20 asserts PASS. NOT tested: your real eyes on laptop + phone + object-page GETs (cancel/record/upload need real records). STOP POINT = here.

- **2026-10-14 (Stage 6 fix-pass — BOOK PAGE RESPONSIVE, last task done):** per your "adjust itself to screen size": `appointments/book_appointment.html` rebuilt — fluid card (`max-w-lg → md:2xl → lg:4xl`), padding/title scale up, form auto-splits into 2 columns on tablet+ (patient+doctor, date+time side by side; reason full row), Cancel + Book buttons stack on phone, row right-aligned on desktop. Tested: `check` clean; anon 302, recep GET 200, 6/6 asserts PASS (fluid card, grid, reason span, actions, all 6 fields render). NOT tested: your real eyes on laptop + phone + actual booking submit. STOP POINT = here.

- **2026-10-14 (Stage 6 fix-pass — DESKTOP RESPONSIVENESS, last task done):** per your note (desktop hero/buttons/profile too small, space wasted): hero now scales up from `lg` (avatar 96px, title 30px, padding 32px, counts bigger); Book/All buttons sit side-by-side at full 44px size on desktop via new `.btn-sm.btn-desk` rule in `app.css` (still compact stacked on phone/tablet); schedule+approvals/doctors board now splits 2/3 + 1/3 from `lg` (was `xl`, so laptops 1024+ use the width); profile page widens to `lg:max-w-4xl` with taller banner + bigger avatar. Mobile/tablet classes untouched. Tested: `check` clean, both pages 200, 11/11 render asserts PASS (lg classes, desk buttons, grid breakpoint, pens intact). NOT tested: your real eyes on laptop + 390px phone. STOP POINT = here.

- **2026-10-14 (Stage 6 correction — PENCIL EDIT on photo + banner, last task done):** per your correction, both images now carry a pencil button that opens its file chooser (instant preview, Save keeps). Banner became uploadable: new `CustomUser.profile_banner` + migration `accounts/0005` + `dashboard/forms.ReceptionistProfileForm` (photo + banner hidden inputs); `receptionist_profile.html` rebuilt with pencil overlays + preview JS; desk hero shows her banner photo under a dark-teal overlay (gradient fallback when none). Tested: `check` + migrate clean; anon 302, recep GET 200 (both pens + hidden inputs present), photo+banner POST upload 302 and saved, hero renders banner URL. Test uploads + temp users cleaned. NOT tested: your real tap-the-pencil + Save on phone/browser. STOP POINT = here.

- **2026-10-13 night (Stage 6 — RECEPTIONIST PAGE, last task done):** rebuilt `receptionist_home` view (today's schedule excl. cancelled/no_show, pending approvals top-10, doctor board with `today_load` + available/unavailable counts, `select_related` for perf, `@receptionist_required` guard) + rebuilt `receptionist_home.html` (gradient hero with profile + Book/All buttons + 3 counts, 3 Figma stat cards with mint footer strip, Today's Schedule table 12 max, Pending Approvals table with inline Approve + confirm modal, Doctors' Schedule live board with All/Available/Unavailable + per-doctor badge + booked-today). Part of `c5b9f59` (48 files) pushed to `origin/redesign-homepage`. Tested: `check` clean, 19/19 matrix ALL PASS. NOT tested: real browser look at 390px + approve-click flow by you. STOP POINT = here.

- **2026-10-13 (push):** `c5b9f59` pushed to `origin/redesign-homepage` — 48 files (Stage 6 all: guards, reception board, Figma shell, teal sweep, mobile retrofit). Secrets scanned clean, `main` untouched, tree clean.

- **2026-10-13 (Stage 6 mobile rail):** per user, icon rail now persistent on ALL sizes — phones get a slimmer 64px rail (tablets 84px), no hidden drawer, hamburger retired; content/topbar offset accordingly. Tested: `check` clean, 19/19 matrix ALL PASS. NOT tested: real Android device at 360–430px.

- **2026-10-13 (fixed header):** public nav now `position:fixed` (stays pinned on scroll; was `sticky`) + `main` offset `pt-64/70px`; anchor sections (`features/roles/stats/footer`) got `scroll-mt` so jumps clear the bar; AI modal lifted to `z-90` above header. **Fault found 2026-10-13:** stray Tailwind `relative` class on the header was overriding the pin (same specificity, later CDN stylesheet) — removed + selector bumped to `header.pub-header` with a do-not-touch note. Tested: `check` clean, GET `/` + login + register + demo 200. NOT tested: real scroll/pinned behavior on device. **USER-CONFIRMED 2026-10-13: pin works.**

- **2026-10-13 (commit):** `a35834d` pushed to `origin/redesign-homepage` — 163 files (homepage build + dashboard updates + static/partials first commit + 144 junk untracks). Secrets scanned clean, `main` untouched. Tree fully clean after push.
- **2026-10-13 (review):** full fault sweep — dead UTF-16 `.gitignore` revived (UTF-8) + 144 tracked junk files untracked (`__pycache__`, `media/` uploads); no invalid filters left; all btn/badge CSS verified; 6 public pages render 200 (`/api/` 403 anonymous is pre-existing DRF auth, untouched). Tested: `check` clean; NOT tested: browser, logged-in pages.
- **2026-10-13 (fix):** `status_badge.html` crash fix — explicit labels, all 12 statuses render-tested; `/`, register, login, demo all 200. Tested: `check` clean + render asserts; browser NOT tested.
- **2026-10-13 (Stage 4b):** Homepage doctors specialty filter tabs (All + 8, JS-only, empty tabs auto-hide) per 06_preview. Full directory page DEFERRED. Tested: `check` clean, GET / 200 (9 tabs, 5 cards); browser NOT tested.
- **2026-10-13 (Stage 4):** Homepage 13-section build — trust strip, About, 8 services, Why SHMS, real-DB doctors, How It Works, 2 CTA bands, FAQ, final CTA, footer placeholders, nav Book CTA, `core/views.home`. Tested: `check` clean, GET / + register + login all 200; browser NOT tested.
- **2026-10-13:** Auth mobile form-first (register + login mint hero `hidden lg:flex`, centered logo pill). Tested: `check` clean; 390px look NOT tested.
- **2026-10-10:** Palette WCAG AA audit — all pass (white-on-primary 7.81, muted 5.27, links 4.96); fixed placeholder contrast #9aa8a5→#64756f (4.87). Tested: `check` clean.
- **2026-10-10:** Auth copy original SHMS voice; login rebuilt as register twin (Pexels 6011604 photo, eye toggle, no dead Remember-Me). Tested: `check` clean, GET asserts pass; browser + POST NOT tested.
- **2026-10-10:** Register Figma split rebuild (mint + white sheet, Pexels 5452291 photo, Terms, eye toggles, double-submit guard) + header hidden on auth pages. Tested: `check` clean, GET 200s; POST/SMTP NOT tested.
- **2026-10-10 (Stage 1 fixes):** Registration 500 fix + IntegrityError guard + views dedup. Tested: `py_compile` + `check` clean; live SMTP/duplicate POST NOT retested.
- **2026-10-10 (Stage 1):** Audit complete — branch, 60 templates, duplicate views, homepage gap, Figma 02/03. No code changed.
- **2026-10-09:** Tracker renamed to PROGRESS_STATUS.md; Figma found (40 JPGs); registration 500 diagnosed; role/workflow brief saved; homepage brief saved.
- **2026-10-08:** Phase 11 polish (teal→slate-50, badges/hovers, footer, hero) + baseline tracker created.

## 11. Known limitations (free-plan limits, untested items, risks)

- **Render free tier (per README):** expect cold-start sleeps; verify plan + env (`EMAIL_HOST_USER/PASSWORD`, `DEFAULT_FROM_EMAIL`) in dashboard. Live SMTP delivery NOT tested.
- **Untested by user:** browser look (1440/768/390) for homepage + auth + tabs; tab click behaviour; POST register/login; logged-in role views of `/`; booking flow end-to-end.
- **Risks:** large uncommitted pile (`templates/`, `static/`, `templates/partials/`, this file) on `redesign-homepage` — commit soon. Old git history still contains `media/` uploads + pyc files (see §7 — needs history-cleanup decision before public push of those commits). `db.sqlite3` + `.env` must never be committed (now enforced by working `.gitignore`).

## 12. Next recommended action

> **WHERE WE STOPPED (2026-10-14): FRONTEND-FIRST approved — finish 6b/6c/6d before Stage 7.** Receptionist flow approved.
> **WHAT NEXT:** 6b Doctor frontend (`doctor_home` + 4 doctors pages + availability toggle) — needs your approval to start. Then 6c Patient, 6d Admin+shared, then Stage 7 QA+docs.
> **DEFERRED (not building now):** doctor availability self-toggle — lands in the doctor-pages pass. Chat declined.
> **HI-RULE (user 2026-10-14):** anytime you say "hi", I reply with Where-stopped + What-next from this section, no extra digging.
> **BASE APPROVED 2026-10-13 (user):** `templates/base.html` done for now. No further base edits without new request.
> **RECEPTIONIST FLOW APPROVED 2026-10-14 (user):** all 9 pages responsive + Create-Invoice fix approved as-is.

1. **User visual review** of `/` (desktop + 390px): hero, 8 services, doctors + tabs, FAQ, footer — reply with fixes or "approved".
2. **Commit** the pile on `redesign-homepage` (`git add templates/ static/ core/ smart/ PROGRESS_STATUS.md` → commit → push branch, never `main`).
3. Then **Stage 5 test/fix** from review notes → **Stage 6 dashboards** (needs explicit approval per scope lock).

---

## Update Template (copy for new entries)

```md
- YYYY-MM-DD (Stage N): <what done> — <files changed>. Tested: <how verified>. NOT tested: <what remains>.
```

- On phase completion: update `39%` = `completed/28*100`, move item from §3 remaining list, redraw bar (`█` = 5%).
