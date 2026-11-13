# EcoSphere AI 🌍

**Intelligence for a Plastic-Free Tomorrow.**  
*AI-Powered Campus Plastic Audit & Environmental Intelligence Platform*  
**Designed & Developed by Raja © 2026** — Founder, Creator & Lead Developer.

An original cinematic sustainability platform combining a rotating 3D Earth, a clickable low-poly campus digital twin, a premium analytics dashboard, and a real database-backed plastic-audit system. **SDG 12** is the primary focus, supported by **SDGs 11, 13, 14 and 15**.

> **Data integrity first:** Public **Demo Mode** uses clearly labeled simulated measurements and never writes them into the real dataset. **Real Audit Mode** uses authenticated, campus-scoped, user-entered observations only. Missing baselines, unverified evidence, and unconfirmed recycling are not represented as proven benefits.

## What is included

| Area | Implemented behavior |
|---|---|
| Cinematic landing | Responsive motion system, mouse-responsive React Three Fiber Earth, WebGL/reduced-motion fallback, scroll reveals, project story, Raja developer card and credit popup. |
| Navigation | Landing, authenticated/demo dashboard, About, Developer and IGEN GreenDay 2026 showcase pages; 12 dashboard workspaces; route-level loading/error/404 boundaries. |
| Real audit workflow | Create, view, edit (creator/admin), soft-delete (creator/admin, with confirmation), search, date filtering, one-item-per-audit weight recording and automatic timestamps; server-side validation. |
| Workspace setup | Create a campus, departments, zones, per-zone heatmap thresholds, custom plastic categories and scoring weights. |
| Demo exploration | Seeded deterministic simulated audit records, clearly labeled as simulated; no login required. |
| Analytics | Daily trends, category donut, zone comparison, cumulative baseline reduction area, recycling stacked comparison, audit-day heatmap, composition treemap, provisional score radar and scaled 3D waste model. |
| Metric calculations | Recorded kilograms, single-use percent, **confirmed** recycling rate, same-length preceding-period baseline, reduction *or increase*, configurable provisional sustainability score with visible weights. |
| Digital twin | Interactive rotating/zoomable campus buildings and clickable zones, with configurable low/moderate/high thresholds and empty states. Stylized conceptual geometry, **not a surveyed CAD/BIM model**. |
| Recommendations | Deterministic, data-grounded sustainability assistant; basic exploratory scikit-learn forecast after sufficient observations, clearly marked as uncalibrated. **No LLM credentials or invented measurements required.** |
| Evidence | PNG/JPEG/WebP/PDF uploads with server file-type/signature checks, size limits, private local or optional private Supabase Storage, authenticated previews, pending/reviewed/approved/rejected status; reviewer roles. |
| Intervention tracking | Reduction actions, dated before/after measured weights, notes, attached evidence and caution about comparable observation conditions. |
| Measurable goals | Campus reduction targets with kg deadlines and provisional progress linked to observed matched-period reduction; no claims of independent verification. |
| Exports | Audits exported as UTF-8 CSV; server-generated multi-section PDF environmental reports, with charts, baseline limitations and developer credit; print/share shortcuts in UI. |
| Security | Supabase JWT verifier, campus-scoped reads/writes, owner/admin audit editing, reviewer-only approval/recycling confirmation, soft deletes, private evidence routes, Postgres RLS policy script, limited request throttling. |

**Important maturity notes:** This is a substantial local-development application and deployment *starter*, not a certified environmental-monitoring system or an audited production deployment. Authenticated browser flows and the Next.js production build still require integration verification with your configured Supabase project and installed npm dependencies. Advanced shared-campus account invitations, globally verified interdepartmental leaderboard rankings, automatic independent photo verification, industrial-grade distributed rate limiting, asynchronous report queues, real campus GIS/BIM models, formal DB migrations and live hardware telemetry are **not** included. The leaderboard intentionally avoids claiming verified ranks until an independent scoring process exists. Carbon savings are intentionally not calculated without documented conversion factors.

## Monorepo layout

```text
ecosphere-ai/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Cinematic landing
│   │   ├── dashboard/page.tsx       # Dashboard application
│   │   ├── about/page.tsx           # Project vision
│   │   ├── developer/page.tsx       # Raja profile
│   │   └── showcase/page.tsx        # GreenDay 2026 showcase
│   ├── components/
│   │   ├── DashboardApp.tsx         # Dashboard routing and real/demo workflows
│   │   ├── AuditForm.tsx
│   │   ├── SiteChrome.tsx
│   │   ├── charts/AnalyticsCharts.tsx
│   │   ├── three/{EarthScene,CampusScene,WasteScene}.tsx
│   │   └── ui/primitives.tsx
│   ├── lib/{client,demo,types}.ts
│   ├── .env.example
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, basic rate limit
│   │   ├── auth.py                 # Supabase JWT / opt-in local-only dev auth
│   │   ├── models.py               # 17 SQLAlchemy relational tables
│   │   ├── schemas.py              # Pydantic constraints
│   │   ├── routers/                # Workspace, audits, imports, analytics,
│   │   │                           # evidence, actions, reports
│   │   └── services/metrics.py
│   ├── tests/
│   ├── .env.example
│   └── Dockerfile
├── db/supabase_rls.sql             # Optional direct-Data-API RLS protections
├── .env.example                    # Docker Compose settings
├── docker-compose.yml
└── README.md
```

## Fastest local setup: SQLite + development authentication

Prerequisites: **Python 3.12+**, **Node.js 22+**, npm. Run the backend and frontend in separate terminals. This mode is **development only** and allows locally hosted, unverified audit data entry so you can evaluate end-to-end functionality without third-party credentials.

**1. Backend** (terminal 1):

```bash
cd ecosphere-ai/backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # Windows: Copy-Item .env.example .env
# Confirm DEV_AUTH_MODE=true only for local testing
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend automatically creates the local SQLite schema at `backend/ecosystem_local.db` on first run. Open **http://127.0.0.1:8000/docs** for interactive API documentation and **http://127.0.0.1:8000/api/health** for a basic status check. Local uploaded evidence is stored under `backend/uploads/`.

**2. Frontend** (terminal 2):

```bash
cd ecosphere-ai/frontend
cp .env.example .env.local       # Windows: Copy-Item .env.example .env.local
# Confirm NEXT_PUBLIC_DEV_AUTH_MODE=true only for local testing
npm install
npm run dev
```

Open **http://localhost:3000**. Select **Explore Dashboard** to browse labeled demo data, then select **Real audit mode** to create your own campus workspace. In **Settings**, add one department and one zone. In **Plastic Audit**, record your first actual measured item and optionally attach evidence. Use **Analytics** or **Impact Reports** to view calculations and download your data. These local records are developer-entered test data, **not** verified live environmental measurements.

To restart a fresh SQLite development workspace, shut down the API and manually remove `backend/ecosystem_local.db` (this irrevocably deletes the local records). The included SQLAlchemy `create_all()` bootstrap is suitable for a first local setup, not schema migrations on an existing production database.

## Production-oriented configuration: Supabase Auth + PostgreSQL

The backend must **not** run with `DEV_AUTH_MODE=true` outside a loopback-only development environment.

1. Create a Supabase project with **asymmetric JWT signing keys** supported by the backend verifier (RS256/ES256). Enable the desired email/password sign-in flow.
2. Provide `SUPABASE_URL=https://<project>.supabase.co`, `SUPABASE_JWT_AUDIENCE=authenticated`, a `DATABASE_URL` for its PostgreSQL database (or your own Postgres instance), and `DEV_AUTH_MODE=false` in `backend/.env`. Store database credentials **server-side only**.
3. In `frontend/.env.local`, set `NEXT_PUBLIC_DEV_AUTH_MODE=false`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_URL`, and optionally `NEXT_PUBLIC_DEVELOPER_GITHUB` / `NEXT_PUBLIC_DEVELOPER_LINKEDIN`. Public Supabase publishable keys are permitted in the browser; **never** put a service-role key, JWT secret or database password in any `NEXT_PUBLIC_*` variable.
4. Initialize the backend schema by starting FastAPI on an empty database (for now, it calls `Base.metadata.create_all()`); on managed production systems replace this bootstrap with reviewed **Alembic migrations** and coordinated database backups.
5. **If the database is managed through Supabase**, review and apply `db/supabase_rls.sql` **after** tables exist and test policies against authenticated/anonymous roles. The FastAPI server enforces independent campus permissions even if its DB credentials bypass RLS.
6. Optional evidence offload: create a **private** Supabase Storage bucket named `ecosphere-evidence` (or set a custom name). Configure `SUPABASE_SERVICE_ROLE_KEY` **on the backend only**. Without the key, evidence is stored in the local backend volume, not exposed to the public.
7. Require HTTPS, configure strong secret management, secure backups, a reverse proxy, observability, durable request rate limiting, access reviews, security headers, restore drills and staging/prod integration tests before accepting real institutional data.

**Authorization scope:** Each newly signed-in account can create its own campus workspace and becomes its administrator. The schema and API honor admin, auditor and reviewer roles, but **there is no in-app multi-user invitation/role administration interface yet**. This is required before a multi-team institutional rollout.

### Docker Compose (PostgreSQL, production-style Supabase authentication)

```bash
cd ecosphere-ai
cp .env.example .env          # then edit PostgreSQL password and Supabase keys
docker compose up --build
```

Open **http://localhost:3000**. Containers run with `DEV_AUTH_MODE=false`; without valid Supabase configuration, the **public demo still works** but real-data sign-in is **unavailable by design**. API port `8000` is bound to host loopback, not the public Internet. This Compose file is a **single-host starter**, not a complete hardened internet deployment.

> If changing public Supabase settings for Docker, **rebuild** the frontend image: Next.js embeds `NEXT_PUBLIC_*` variables at build time. For remote hosting, change the public API origin and backend CORS allowlist and terminate TLS at the ingress.

## CSV import format

1–500 rows per import, UTF-8 CSV, maximum 1 MiB. `department`, `zone` and `category` must match entities already configured in **Settings**. Dates must use `YYYY-MM-DD`; booleans use `true`/`false`, `yes`/`no` or `1`/`0`; weights are **measured kilograms** (positive, up to 4 decimals). Each submission ID must be unique within its campus.

```csv
submission_id,audit_date,department,zone,auditor_name,category,item_type,item_count,weight_kg,single_use,recyclable,disposal_method,observations,corrective_action
ECO-001,2026-11-10,Computer Science,Library,Raja,PET bottles,500 mL PET bottle,12,0.3060,true,true,segregated,Counted and weighed after lunch,Install refill water station
```

The CSV import is all-or-nothing: any invalid row or duplicate submission rejects the transaction. Change the date to a day on or before the current date. The audit form also supports optional measured evidence photos after saving the audit. Exported CSV escapes user-entered spreadsheet-formula prefixes in text fields.

## Environmental calculations and limitations

| Metric | Rule |
|---|---|
| Total plastic mass | Sum of selected-period recorded item weights (`kg`). |
| Single-use share | `100 × single-use recorded mass / total recorded mass`. |
| Confirmed recycling rate | `100 × reviewer-confirmed recycled mass / recorded plastic mass`. Merely marking an item recyclable does **not** count. |
| Reduction (kg) | `previous-period mass − current-period mass`; a negative result is shown as an **increase**, not savings. |
| Reduction (%) | `100 × reduction / previous-period mass`; missing/zero baseline yields `null` / `—`. |
| Provisional EcoSphere score | Weighted blend of reduction, recycling, single-use share reduction, audit-completion target and **approved** evidence fraction. Defaults: **30% / 25% / 15% / 15% / 15%**. Admin can configure the five weights and weekly audit target. No score is generated without both baseline/current audit observations and nonzero baseline mass. |

The baseline is the **equally long immediately preceding date interval**. The system does **not** assume unobserved days contained zero waste. Comparisons are meaningful only if data collection coverage and methods are similar, which users must check. This score is **not an officially certified rating**. No unsupported CO₂ conversion or environmental benefit is invented.

The optional scikit-learn prediction is a simple linear model on the observed day-series, **not** a calibrated scientific forecast. The UI and API mark its uncertainty range as indicative and state modeling limitations. The AI assistant otherwise uses **deterministic rule-based responses** from current audit measurements.

## Test and verification

```bash
cd ecosphere-ai/backend
PYTHONPATH=. pytest -q       # Windows PowerShell: $env:PYTHONPATH='.'; pytest -q
python -m compileall app
cd ../frontend
npm run lint              # tsc --noEmit, after npm install
npm run build             # production build, after npm install
```

**Validation conducted in the provided source environment:** backend automated tests passed (5 tests), and API-level integration checks covered campus onboarding, audit create/import, duplicate protection, metrics, recycling, evidence, interventions, PDF and CSV. TypeScript/TSX source syntax was checked with a locally available global TypeScript compiler. **Full Next.js dependency installation/production build was not verifiable here because npm registry access was unavailable**; run both TypeScript and production-build commands in your deployment environment. Supabase-hosted login, RLS, bucket uploads and real-device WebGL performance also require testing against your own infrastructure.

## Suggested deployment checklist

- Replace `create_all` with managed, reviewed schema migrations; configure database backups and recovery.
- Confirm Supabase JWT and authorization, RLS, private buckets, role assignment and cross-campus isolation using production-like accounts.
- Test frontend lint/build, full browser journeys, accessibility and mobile WebGL fallback; establish Core Web Vitals baselines.
- Configure hostnames, HTTPS, HSTS/CSP at the ingress, monitoring, distributed rate limiting and upload scanning.
- Independently review campus sampling methodology, weighing devices, comparable periods and evidence-verification practices before publishing impact claims.

## Credits and rights

**Raja** — Founder, Creator & Lead Developer, **EcoSphere AI** (2026). Social profile URLs are intentionally not invented and can be configured using environment variables. The GreenDay 2026 page is a project showcase; it does **not** imply IGEN approval, affiliation or certification.
