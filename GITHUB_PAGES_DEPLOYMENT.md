# EcoSphere AI — GitHub Pages deployment

This repository contains the Next.js frontend in `ecosphere-ai/frontend` and a Python FastAPI backend in `ecosphere-ai/backend`.

## Public demonstration website (GitHub Pages)

The root-level workflow `.github/workflows/deploy-pages.yml` builds the frontend and deploys its generated static `out/` directory.

1. Open **Settings → Pages → Build and deployment**, and select **GitHub Actions** as the source. GitHub may not allow an app to change this repository setting.
2. Open **Actions → Deploy EcoSphere AI to GitHub Pages** to inspect the build and deployment checks.
3. The deployment URL appears in the **deploy** job. Project pages usually use `https://<user>.github.io/EcoSphere-AI/`; if a custom domain is configured for the owner's site, it may instead use `https://<custom-domain>/EcoSphere-AI/`.

The frontend's `next.config.ts` detects GitHub Actions (`GITHUB_PAGES=true`) and statically exports with the appropriate repository subpath. Navigation in the dashboard preserves the deployed subpath. `.nojekyll` is included so the `_next` assets load.

## Real audit mode requires a separate backend

GitHub Pages hosts static files, not Python processes, PostgreSQL, authentication servers, or private evidence storage. The public website contains an explicitly identified demonstration. **Do not claim real audit mode is operational solely from a successful Pages deployment.**

To enable real data, deploy FastAPI on a compatible host, configure Supabase PostgreSQL/Auth and private evidence storage, and set these GitHub Actions **repository variables** under Settings → Secrets and variables → Actions → Variables:

- `NEXT_PUBLIC_API_URL` — production HTTPS URL of your FastAPI service (no trailing slash).
- `NEXT_PUBLIC_SUPABASE_URL` — your Supabase project URL.
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` — the *public* browser key only.
- `NEXT_PUBLIC_DEVELOPER_LINKEDIN` — optional developer profile.

Configure the backend CORS allowed origins for the deployed website. Never put PostgreSQL connection strings or Supabase service-role secrets in `NEXT_PUBLIC_*` variables. These values are bundled into public frontend JavaScript.

## Verify before inviting real users

Check that the landing page, dashboard, navigation, 3D visuals, and simulated-data disclaimer work. For real audit mode, test authenticated registration, audit persistence, authorization, evidence access, confirmed recycling, and report generation separately.

If the workflow fails, open its **build** job to find the exact error. A successful GitHub Pages job does not verify the separate API or database.
