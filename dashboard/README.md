# Garage Dashboard

Vue 3 + Tailwind dashboard for the Parking API. Shows live parking status, garage overview, ticket activity, revenue summary, and supports New Vehicle Entry.

This dashboard is the frontend for the Parking API in this repository. Install Python dependencies, PostgreSQL, run Alembic migrations, and start the API using the project root [README.md](../README.md). Configure `DATABASE_URL`, authentication (`API_KEY`, login), and CORS there; this document only covers the Vue app.

**Live sync:** The dashboard polls the API every 10 seconds while the tab is visible and refreshes immediately when you return to the tab. Status cards, garage overview, ticket activity, and revenue stay in sync with the database. Closing a ticket or recording a payment triggers a full refresh across all widgets.

## Setup

**Prerequisites:** Backend running and reachable at `VITE_API_URL`. Full stack setup (database, migrations, API, auth, CORS) is in the project root [README.md](../README.md).

1. Optional: copy `env.example` to `.env`. If you don’t, the dashboard uses `http://localhost:8000` as the API URL. In `.env` you can set:
   - `VITE_API_URL` – backend URL (defaults to `http://localhost:8000` when unset)
   - `VITE_API_KEY` – optional; if the **backend** `API_KEY` is set (see root [README.md](../README.md)), set this to the **same value** so the dashboard sends `X-API-Key`. Omit when the API has no `API_KEY` or when you use **login** only (JWT is sent instead).

### Authentication

When the API is started **without** `API_KEY`, you normally need neither `VITE_API_KEY` nor login—the dashboard can call the API without credentials. When **`API_KEY` is set** on the server, requests must include either **`X-API-Key`** (from `VITE_API_KEY`) or **`Authorization: Bearer <jwt>`** after sign-in; once logged in, the client sends the JWT and stops attaching the static key. Prefer **login** for interactive sessions (built-in expiry handling); use **`VITE_API_KEY`** for quick local wiring or scripts without the login form. `VITE_*` values are embedded in the production bundle, so anyone who can load the built site can recover `VITE_API_KEY`—do not treat it as a server-only secret in production.

2. Install and run:

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173. Ensure the backend is running and CORS allows `http://localhost:5173` (default in backend config).

## Troubleshooting

- **CORS errors in the browser (requests blocked):** Ensure the API’s `CORS_ORIGINS` includes the **exact** dashboard origin (scheme, host, and port, e.g. `http://localhost:5173`—no path). Production rules and full CORS behavior are in the project root [README.md](../README.md).
- **Network errors, connection refused, or timeouts:** Confirm the API is running and that `VITE_API_URL` points at the real base URL (default if unset: `http://localhost:8000`). The dev client uses a **5s** request timeout; a slow or unreachable API can show as timeout or network errors.
- **401 Unauthorized, redirect to login, or “session expired”:** If the backend has `API_KEY` set, set `VITE_API_KEY` to the same value **or** sign in so the app sends a JWT. Check for typos, an expired token (sign in again), or stale auth data (clear site data for this origin and retry).
- **Changed `.env` but behavior did not update:** Stop and **restart** `npm run dev` so Vite reloads `VITE_*` variables. After `npm run build`, env values are **baked into** the output—run a **new build** whenever you change `VITE_API_URL` or `VITE_API_KEY` for production.

## Build

```bash
npm run build
```

Output is in `dist/`. Serve with any static host or point the backend to it if you add static file serving.
