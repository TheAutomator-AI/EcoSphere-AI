# EcoSphere AI — Live deployment on GitHub + Vercel

## Production website

- **Website:** https://ecosphere-ai-navy.vercel.app/
- **Source:** https://github.com/TheAutomator-AI/EcoSphere-AI
- **Vercel project:** `ecosphere-ai` in team `rajaamlengineer-6389s-projects`
- **Framework:** Next.js 16 / React / TypeScript
- **Root directory:** `ecosphere-ai/frontend`
- **Production branch:** `main`
- **Node.js:** `22.x`

The Vercel project is Git-connected: a push to `main` automatically builds and publishes the frontend. Do not upload a ZIP to Vercel manually.

## Credential-free public preview

This is intentionally a **public demonstration site**, not a live campus data collection service.

Vercel build-time settings:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_DEMO_ONLY` | `true` |
| `NEXT_PUBLIC_DEV_AUTH_MODE` | `false` |
| `NEXT_PUBLIC_DEVELOPER_GITHUB` | `https://github.com/TheAutomator-AI` |

No Supabase account, database connection, service-role key, or FastAPI server is needed to view the site. The browser can display:

- Cinematic 3D Earth, campus twin, developer page and project showcase
- Date-filtered dashboards and simulated audit records
- Rule-based analysis of **simulated** sample data
- Explicitly marked **SIMULATED DEMO** CSV sample exports

The interface clearly labels demo observations as simulated. It does not claim real environmental measurements, verified images or certified outcomes. The public preview does not save visitor audit submissions. It does not offer authentication, evidence verification or real environmental PDF reports.

## If the website needs troubleshooting

Open Vercel → `ecosphere-ai` → Deployments. A healthy production deployment shows **READY**. Its build should generate `/`, `/dashboard`, `/about`, `/developer` and `/showcase` without TypeScript errors.

The Vercel project is configured to protect previews with Vercel Authentication, while the production deployment is public.

GitHub Pages uses a separate GitHub Actions workflow; **Vercel is the preferred live site**.

## Future real-audit upgrade (optional)

Actual cross-device campus records, private evidence, user roles, audit logs and PDF server reports require a persistent database and trusted backend. The repository includes a separate FastAPI backend under `ecosphere-ai/backend`, but it is **not deployed by the frontend Vercel project**.

Do not switch off `NEXT_PUBLIC_DEMO_ONLY` or advertise real-audit functionality until backend/authentication/storage are fully deployed and tested. Never put database passwords or privileged keys into `NEXT_PUBLIC_*` variables.

**Developed by Raja — EcoSphere AI · 2026.**
