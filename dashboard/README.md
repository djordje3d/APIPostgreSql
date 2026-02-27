# Garage Dashboard

Vue 3 + Tailwind dashboard for the Parking API. Shows live parking status, garage overview, ticket activity, revenue summary, and supports New Vehicle Entry.

**Live sync:** The dashboard polls the API every 12 seconds while the tab is visible and refreshes immediately when you return to the tab. Status cards, garage overview, ticket activity, and revenue stay in sync with the database. Closing a ticket or recording a payment triggers a full refresh across all widgets.

## Setup

1. Optional: copy `env.example` to `.env`. If you don’t, the dashboard uses `http://localhost:8000` as the API URL. In `.env` you can set:
   - `VITE_API_URL` – backend URL (defaults to `http://localhost:8000` when unset)
   - `VITE_API_KEY` – optional; set when the backend requires `X-API-Key`. When using **login**, the dashboard stores the JWT after sign-in; `VITE_API_KEY` is not required for logged-in users.
2. Install and run:

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173. Ensure the backend is running and CORS allows `http://localhost:5173` (default in backend config).

## Build

```bash
npm run build
```

Output is in `dist/`. Serve with any static host or point the backend to it if you add static file serving.
