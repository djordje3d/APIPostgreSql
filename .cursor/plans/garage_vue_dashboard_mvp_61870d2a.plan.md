---
name: Garage Vue Dashboard MVP
overview: Add a Vue 3 + Tailwind dashboard that consumes the existing Parking API for live parking status, garage overview, ticket activity, revenue summary, and New Vehicle Entry with optional backend enhancements for revenue and ticket details.
todos:
  - id: todo-1770550536946-1jjqoshgl
    content: ""
    status: pending
isProject: false
---

# Garage Dashboard (Vue.js + Tailwind) – MVP Plan

## Project analysis summary

The backend is a **FastAPI** app with:

- **Auth:** `X-API-Key` header when `API_KEY` is set in `.env`; CORS already allows `http://localhost:5173` (Vite).
- **Endpoints used by dashboard:**


| Need                              | Existing API                                                              | Notes                                                                                               |
| --------------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Free / occupied / inactive counts | `GET /spots?only_free=true`, `GET /spots?active_only=false`               | Frontend can count items; no global totals endpoint.                                                |
| Open tickets count                | `GET /tickets?state=OPEN`                                                 | Use `total` from paginated response.                                                                |
| Garage list                       | `GET /garages`                                                            | Paginated.                                                                                          |
| Spots per garage                  | `GET /spots?garage_id=X&active_only=false`                                | Per-garage; frontend aggregates for overview.                                                       |
| Last 10 tickets                   | `GET /tickets?limit=10&offset=0`                                          | Ordered by `id` desc. **TicketResponse has no licence_plate or spot code** — see backend gap below. |
| Unpaid / partially paid           | `GET /tickets?payment_status=UNPAID` (and PARTIALLY_PAID)                 | Exists.                                                                                             |
| Today / month revenue             | **Missing**                                                               | No `GET /payments?from=&to=` or revenue summary.                                                    |
| New vehicle entry                 | `GET /vehicles/by-plate/{plate}`, `POST /vehicles`, `POST /tickets/entry` | Entry needs vehicle_id; backend supports auto-assign when `spot_id` omitted.                        |


**Backend gaps (recommended for MVP):**

1. **Revenue (Section D):** Add either:
  - `GET /payments?from=date&to=date` returning paginated payments in range, and dashboard sums `amount`, or
  - A small **dashboard endpoint** e.g. `GET /dashboard/revenue?from=&to=` returning `{ total_amount, count }` (or today + month in one call).
2. **Ticket activity (Section C):** `TicketResponse` has `vehicle_id` and `spot_id` but not `licence_plate` or `spot.code`. Options:
  - **Option A (recommended):** Add optional expand or a dedicated endpoint that returns ticket list with `licence_plate` and `spot_code` (join Vehicle + ParkingSpot) so the dashboard table can show plate and spot without N+1.
  - **Option B (MVP without backend change):** Dashboard fetches vehicle (and optionally spot) per ticket for the last 10; acceptable for 10 rows only.

---

## Architecture (high level)

```mermaid
flowchart LR
  subgraph frontend [Vue Dashboard]
    Layout[Layout + Nav]
    Status[Live Status Cards]
    GarageTable[Garage Overview Table]
    TicketTable[Ticket Activity Table]
    Revenue[Revenue Summary]
    NewEntry[New Vehicle Entry]
  end
  subgraph api [FastAPI Backend]
    Garages[/garages]
    Spots[/spots]
    Tickets[/tickets]
    Payments[/payments]
    Vehicles[/vehicles]
    VehicleTypes[/vehicle-types]
  end
  Layout --> Status
  Layout --> GarageTable
  Layout --> TicketTable
  Layout --> Revenue
  Layout --> NewEntry
  Status --> Spots
  Status --> Tickets
  GarageTable --> Garages
  GarageTable --> Spots
  TicketTable --> Tickets
  Revenue --> Payments
  NewEntry --> Vehicles
  NewEntry --> VehicleTypes
  NewEntry --> Tickets
```



---

## Frontend: Vue 3 + Tailwind

- **Scaffold:** New app in project root, e.g. `dashboard/` (or `frontend/`), with **Vite + Vue 3** and **Tailwind CSS**.
- **API client:** Single axios (or fetch) instance with base URL from env (e.g. `VITE_API_URL=http://localhost:8000`), and `X-API-Key` from env (e.g. `VITE_API_KEY`) so all requests are authenticated when backend expects it.
- **Routing:** Vue Router with one main dashboard view; optional second view for “Garage detail” (click garage row). No CRUD forms — overview + actions only.

---

## Section A – Live parking status (top of page)

- **Four cards/counters:**
  - **Free spots:** `GET /spots?only_free=true` (use `total` or sum over all garages: call without `garage_id` to get global count, or call per garage and sum).
  - **Occupied spots:** Derive from (total active spots − free spots), or count open tickets: `GET /tickets?state=OPEN` → `total`.
  - **Inactive spots:** `GET /spots?active_only=false` total − (active spots count). Or: total spots with `active_only=true` vs `active_only=false` and subtract.
  - **Open tickets:** `GET /tickets?state=OPEN` → `total`.
- **Data source detail:**  
  - Free: `GET /spots?only_free=true&limit=1000` (or paginate and sum).  
  - Open tickets: `GET /tickets?state=OPEN&limit=1` just to get `total`.  
  - For “total active” and “inactive”: `GET /spots?active_only=true` total and `GET /spots?active_only=false` total; occupied = open tickets count or (total active − free).
- **UI:** Simple stat cards (e.g. green/red/yellow/neutral) with numbers; optional short labels. Refresh on load and optionally with a “Refresh” button or interval (e.g. every 30s).

---

## Section B – Garage overview (by garage)

- **Table columns:** Garage name, Total spots, Free, Occupied, Rentable (count).
- **Data:**  
  - `GET /garages` (all or paginated).  
  - For each garage: `GET /spots?garage_id=X&active_only=false` → total; `GET /spots?garage_id=X&only_free=true&active_only=true` → free; occupied = total − free; rentable = filter spots with `is_rentable` (backend has no direct “rentable count” filter; frontend can count from full spot list or add a lightweight backend count later).
- **Aggregation:** Frontend aggregation is acceptable for MVP; alternatively add a single backend endpoint like `GET /garages/overview` returning `[{ garage_id, name, total_spots, free_spots, occupied, rentable_count }]` to reduce round-trips.
- **Action:** Row click → navigate to garage detail (e.g. `/garage/:id`) showing same garage’s spots and open tickets (using existing `GET /spots?garage_id=X`, `GET /tickets?state=OPEN&garage_id=X`).

---

## Section C – Ticket activity (last 10 / live)

- **Columns:** Entry time, Spot code, Vehicle plate, Status (e.g. OPEN/CLOSED).
- **Data:** `GET /tickets?limit=10&offset=0` (already ordered by id desc).
- **Vehicle plate / spot code:** Backend `TicketResponse` does not include them.  
  - **Recommended (backend):** New response schema (e.g. `TicketListRow`) or query param `expand=vehicle,spot` returning `licence_plate` and `spot.code` in list.  
  - **MVP without backend change:** For each of the 10 tickets, `GET /vehicles/{vehicle_id}` and `GET /spots/{spot_id}` (spot_id can be null); display plate and spot code. Acceptable for 10 rows.
- **Actions (buttons per row):**
  - **View ticket:** Navigate to ticket detail or open a simple modal with `GET /tickets/{id}` (and vehicle/spot if not in list).
  - **Close ticket:** Call `POST /tickets/{id}/exit` (only for OPEN tickets); then refresh list.
  - **Go to payment:** Link or navigate to a “Payment” view/modal for that ticket (ticket must be CLOSED); use `GET /payments/by-ticket/{id}` and `POST /payments` with ticket_id + amount. Minimal payment form: amount, method, then submit.

---

## Section D – Payments & revenue (simple first)

- **Display:**  
  - Today’s revenue (sum of payments where `paid_at` is today).  
  - This month’s revenue (sum of payments in current month).  
  - Unpaid / partially paid tickets: count and optionally link to list — `GET /tickets?payment_status=UNPAID` and same for `PARTIALLY_PAID` (or one call without filter and count on frontend).
- **Data source:** Backend currently has **no** list payments by date. Options:
  - **Backend (recommended):** Add `GET /payments?from=date&to=date` (and optionally `limit`/`offset`), returning paginated payments; dashboard sums `amount` for today and for month.  
  - **Or:** Add `GET /dashboard/revenue?from=&to=` returning `{ total_amount }` (and optionally counts); dashboard calls it for “today” and “this month” (e.g. from=first day of month, to=now).
- **Unpaid:** Use existing `GET /tickets?payment_status=UNPAID` and `payment_status=PARTIALLY_PAID`; show count and link to a simple “Unpaid tickets” list (reuse ticket table with filter).

---

## New Vehicle Entry (prominent action)

- **Placement:** Visible in layout (e.g. header or sidebar): **“New Vehicle Entry”** button that opens a modal or slide-over form.
- **Minimal fields:**  
  - **Licence plate** (required).  
  - **Vehicle type** (required) — dropdown from `GET /vehicle-types`.  
  - **Garage** (required) — dropdown from `GET /garages`.  
  - **Spot:** Optional. Two modes:  
  - **Auto (recommended):** “Assign first free spot” — do not send `spot_id`; backend already assigns via `allocate_free_spot`.  
  - **Manual:** Optional dropdown of free spots: `GET /spots?garage_id=X&only_free=true` when garage selected; user can pick one or leave empty for auto.
- **Submit flow:**
  1. **Find or create vehicle:** `GET /vehicles/by-plate/{plate}`. If 404, `POST /vehicles` with `{ licence_plate, vehicle_type_id, status: 1 }`. If 200, use returned `id` (optionally confirm same vehicle type or show warning).
  2. **Create ticket:** `POST /tickets/entry` with `{ vehicle_id, garage_id, spot_id?: number | null, rentable_only: false }`. For auto-assign, omit `spot_id` or send `null`.
  3. On success: show success message, refresh open tickets and spot counts, close form. On 409 “No free spots available”, show error and do not create vehicle if it was new (or leave vehicle created for next time).
- **Optional later:** Rentable-only checkbox (`rentable_only: true`), notes (no backend field today — skip or store elsewhere later).

---

## Suggested file structure (Vue app)

```
dashboard/
  index.html
  package.json
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  env.example          # VITE_API_URL, VITE_API_KEY
  src/
    main.ts
    App.vue
    router/index.ts
    api/client.ts      # axios/fetch + base URL + X-API-Key
    api/garages.ts
    api/spots.ts
    api/tickets.ts
    api/payments.ts
    api/vehicles.ts
    api/vehicleTypes.ts
    views/
      DashboardView.vue   # Sections A–D + New Entry trigger
      GarageDetailView.vue  # Optional: garage spots + open tickets
    components/
      StatusCards.vue
      GarageOverviewTable.vue
      TicketActivityTable.vue
      RevenueSummary.vue
      NewVehicleEntryModal.vue
      PaymentModal.vue    # For “Go to payment” from ticket row
```

---

## Backend changes (minimal, in this repo)

1. **Revenue (required for Section D):**
  - Add `GET /payments?from=date&to=date&limit=&offset=` in [app/routers/payments.py](app/routers/payments.py) (filter by `paid_at`), returning existing `PaginatedResponse[PaymentResponse]`. Dashboard computes sum for “today” and “this month” from items (or add a small `GET /dashboard/revenue` that returns aggregates).
2. **Ticket list with plate/spot (optional but recommended):**
  - In [app/routers/tickets.py](app/routers/tickets.py): either add query param `expand=vehicle,spot` and return a DTO that includes `licence_plate` and `spot_code` (from joined Vehicle and ParkingSpot), or add a separate endpoint `GET /tickets/dashboard?limit=10` returning list of `{ ...ticket, licence_plate?, spot_code? }` so the dashboard avoids N+1.
3. **CORS:** Already allows `http://localhost:5173`. Ensure [app/config.py](app/config.py) `CORS_ORIGINS` includes the URL you use for the Vue dev server.

---

## Implementation order

1. **Backend:** Add `GET /payments?from=&to=` (and optionally a tiny revenue summary endpoint). Optionally add ticket list with vehicle/spot for dashboard.
2. **Frontend scaffold:** Vite + Vue 3 + Tailwind + Vue Router in `dashboard/`, API client with `VITE_API_URL` and `VITE_API_KEY`.
3. **Dashboard view:** Layout with nav; Section A (status cards) using existing spots/tickets APIs.
4. **Section B:** Garage overview table (frontend aggregation); garage detail route optional.
5. **Section C:** Ticket activity table (last 10) with View / Close / Go to payment; Payment modal for closed tickets.
6. **Section D:** Revenue block (today, month, unpaid count) using new payments endpoint.
7. **New Vehicle Entry:** Modal with plate, vehicle type, garage, optional spot; find-or-create vehicle + `POST /tickets/entry` with auto-assign by default.

---

## Summary

- **Vue 3 + Tailwind** dashboard in a new `dashboard/` app; single main dashboard view + optional garage detail; overview and actions only (no generic CRUD forms).
- **Sections A–C** can be implemented with current API; Section C benefits from ticket list including `licence_plate` and `spot_code` (optional backend change).
- **Section D** requires a **new backend endpoint**: list payments by date (and optionally a revenue summary).
- **New Vehicle Entry** uses existing `POST /vehicles` and `POST /tickets/entry` with **auto-assign** (omit `spot_id`); flow: get/create vehicle by plate → ticket entry.

This gives you a clear MVP scope and a path to implement it step by step.