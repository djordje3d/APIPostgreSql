# Postman setup for Parking API

This document describes how to configure Postman for the Parking API and what to capture in screenshots.

---

## 1. Base URL

- **Local:** `http://localhost:8000`
- Set this as a collection variable or in the request URL (e.g. `{{baseUrl}}/garages`).

---

## 2. API key (when authentication is enabled)

If you set `API_KEY` in your `.env` file, **every request except `GET /health`** must send the API key.

### Option A: Per request

1. Open a request (e.g. GET Garages).
2. Go to the **Headers** tab.
3. Add a header:
   - **Key:** `X-API-Key`
   - **Value:** the same value as `API_KEY` in your `.env` (e.g. `your-secret-key`).

### Option B: For the whole collection

1. Right‑click your collection → **Edit**.
2. Open the **Authorization** tab.
3. **Type:** API Key  
   **Key:** `X-API-Key`  
   **Value:** your API key (or a variable like `{{apiKey}}`)  
   **Add to:** Header  
4. Save. All requests in the collection will send the header.

**Screenshot tip:** When API key is required, your Postman screenshots should show the **Headers** tab with `X-API-Key` present, or the collection **Authorization** settings (API Key, Header).

---

## 3. Garages: PUT vs PATCH

| Method | Endpoint | Use case | Body |
|--------|----------|----------|------|
| **PUT** | `PUT /garages/{id}` | Full replace | All garage fields (name, capacity, default_rate, lost_ticket_fee, night_rate, day_rate, open_time, close_time, allow_subscription) |
| **PATCH** | `PATCH /garages/{id}` | Partial update | Only the fields you want to change (e.g. `{"name": "New name"}` or `{"default_rate": 120}`) |

**Example – PATCH (partial update):**

- **URL:** `PATCH http://localhost:8000/garages/1`
- **Headers:** `Content-Type: application/json` (and `X-API-Key` if auth is on)
- **Body (raw JSON):** e.g.  
  `{"name": "Updated garage name"}`  
  or  
  `{"default_rate": 150, "allow_subscription": false}`  

**Screenshot tip:** For garage updates, you can show one request as **PUT** (full body) and one as **PATCH** (only a few fields in the body).

---

## 4. Reference screenshots (what to show)

When updating or re-taking Postman screenshots, use this as a checklist:

| File | Suggested content |
|------|--------------------|
| **Postman1.jpg** | Overview: collection or request list (e.g. Garages, Vehicles, Tickets, Payments, Spots, Health). Optionally show one request with **Headers** tab open and `X-API-Key` visible. |
| **Postman2_settings.jpg** | Collection or environment settings. If using API key: **Authorization** tab with Type = API Key, Key = `X-API-Key`, Add to = Header. |
| **Postman3_settings.jpg** | Another settings view (e.g. Variables or a request’s Headers with `X-API-Key`). |
| **Postman3_payments.jpg** | Payments request example (e.g. POST payment or GET by-ticket) with URL, method, and body/headers as needed. |
| **Postman4_settings.jpg** | Same idea as above: settings or headers so that API key usage is clear when auth is enabled. |

After the updates:

- At least one screenshot should show the **`X-API-Key`** header (or collection auth) when you use `API_KEY`.
- At least one request should demonstrate **`PATCH /garages/{id}`** with a small JSON body (partial update).

No changes are required in Postman if you **do not** set `API_KEY` in `.env`; in that case the API does not require authentication.
