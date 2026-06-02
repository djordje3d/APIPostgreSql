# Garage Dashboard

Vue 3 + TypeScript + Tailwind dashboard for the Garage Manage API in this repository.

**Main views**

- **Dashboard** (`/dashboard`, optional `/:garageId`) ÔÇö live parking status, garage overview, ticket activity, revenue summary, timeline chart, new vehicle entry, payments.
- **Garage detail** (`/garage/:id`) ÔÇö spots, open tickets, revenue for one garage.
- **Login** (`/login`) ÔÇö JWT sign-in (required to use the app; see [Authentication](#authentication)).

**Live sync:** Polls the API every **10 seconds** while the tab is visible; refreshes immediately when you return to the tab. Closing a ticket or recording a payment triggers a full refresh across widgets.

**i18n:** English and Serbian (`vue-i18n`); language is stored in the browser and can be switched from the header.

Backend setup (PostgreSQL, migrations, API, CORS, env) is in the project root [README.md](../README.md) and [api_python/README.md](../api_python/README.md). This document covers only the Vue app.

## Requirements

- Node.js 18+ (LTS recommended)
- Backend API running and reachable at `VITE_API_URL` (default `http://localhost:8000`)
- Backend login configured (`AUTH_USERNAME` / `AUTH_PASSWORD` or `AUTH_PASSWORD_HASH` in `api_python/.env`, with legacy root `.env` fallback) ÔÇö the dashboard always routes through `/login` until a JWT is stored
- For **ticket images** in the UI: file server on port **9009** (see [Ticket images](#ticket-images))

## Setup

1. Optional: copy `env.example` to `.env` in this folder. If you skip it, defaults below apply.

   | Variable | Purpose |
   |----------|---------|
   | `VITE_API_URL` | API base URL, no trailing slash (default: `http://localhost:8000`) |
   | `VITE_API_KEY` | Optional; same value as backend `API_KEY` when you are **not** using login (see [Authentication](#authentication)) |
   | `VITE_FILESERVER_URL` | HTTP origin for uploaded ticket images (default: `http://localhost:9009`) |

   **Dev proxy (optional):** Vite can proxy `/api` and `/uploads` to the backend (`vite.config.ts`). To use it, set `VITE_API_URL` to the dashboard origin with the `/api` prefix, e.g. `http://localhost:5173/api` (no trailing slash). Otherwise point `VITE_API_URL` directly at the API.

2. Install and run:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Ensure the backend is running and `CORS_ORIGINS` includes `http://localhost:5173` (common default when CORS is enabled).

### Authentication

Two layers apply:

1. **Dashboard (always):** Vue Router requires a stored JWT for all routes except `/login`. Sign in with credentials that match backend `AUTH_USERNAME` / `AUTH_PASSWORD` (configured in `api_python/.env`, with legacy root `.env` fallback).

2. **API (when `API_KEY` is set on the server):** Each request must include either `X-API-Key` or `Authorization: Bearer <jwt>`. After sign-in, the client sends the JWT and removes the static key header. If you are not using the login form, set `VITE_API_KEY` to the same value as backend `API_KEY`.

When the backend has **no** `API_KEY`, the API does not require a key or Bearer tokenÔÇöbut you still **sign in** in the dashboard so the app can store and send a JWT.

Prefer **login** for normal use (session expiry handling, idle prompt). Use **`VITE_API_KEY`** only for quick local wiring without the login form. `VITE_*` values are embedded in production buildsÔÇödo not treat `VITE_API_KEY` as a server-only secret.

### Ticket images

Uploads go through the API (`POST /upload/ticket-image`); the dashboard loads images from the **file server**, not the API host.

1. From workspace root:

```bash
cd fileserver/storage
npm install
npm run dev
```

2. Keep `VITE_FILESERVER_URL=http://localhost:9009` (default) or match your file server URL.

Relative `image_url` values from the API are resolved as `{VITE_FILESERVER_URL}{path}` (see `src/utils/ticketImageUrl.ts`). More detail: [api_python/docs/TICKET_IMAGE_UPLOAD.md](../api_python/docs/TICKET_IMAGE_UPLOAD.md).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Vite dev server (port **5173**) |
| `npm run build` | Typecheck (`vue-tsc`) + production build Ôćĺ `dist/` |
| `npm run preview` | Serve `dist/` locally after a build |

## Project layout

| Path | Role |
|------|------|
| `src/api/` | Axios client, auth, REST helpers |
| `src/views/` | Page components (dashboard, garage detail, login) |
| `src/components/` | UI and dashboard widgets |
| `src/composables/` | Polling, formatters, garage/ticket state |
| `src/locales/` | `en.json`, `sr.json` |
| `env.example` | Sample `VITE_*` variables |

## Troubleshooting

- **CORS errors:** `CORS_ORIGINS` must include the exact dashboard origin (e.g. `http://localhost:5173`, no path). See root [README.md](../README.md).
- **Network errors / timeouts:** Confirm the API is up and `VITE_API_URL` is correct. The Axios client uses a **5s** timeout (`src/api/client.ts`).
- **401 / session expired:** Sign in again, or set `VITE_API_KEY` when the backend uses `API_KEY` and you are not using JWT. Clear site data for this origin if auth state is stale.
- **Login fails / ÔÇťnot configuredÔÇŁ:** Set `AUTH_USERNAME` and `AUTH_PASSWORD` (or `AUTH_PASSWORD_HASH`) in `api_python/.env` (preferred; legacy root `.env` fallback is supported) and restart the API.
- **Ticket images broken:** Start the file server on port 9009 and check `VITE_FILESERVER_URL`. Upload directory must be writable (`LOCAL_STORAGE_PATH`, default `fileserver/storage/`).
- **Changed `.env`:** Restart `npm run dev`. After `npm run build`, run a **new build** whenever `VITE_*` values change for production.

## Build

```bash
npm run build
```

Output is in `dist/`. Serve with any static host, or use `npm run preview` to smoke-test the build locally.
