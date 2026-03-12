# Ticket image upload (optional) on new vehicle entry

## Summary

- **New vehicle entry modal**: Optional "Ticket image" file input. User can pick an image (JPEG, PNG, WebP); it is resized client-side (max 1200px) and uploaded, then the returned URL is sent with the ticket entry.
- **Backend**: New column `tickets.image_url`, optional `image_url` on ticket entry and on dashboard response; new `POST /upload/ticket-image` endpoint; static files served at `/uploads`.
- **View ticket modal**: Shows the ticket image when `image_url` is set (via existing `ImageIn` component).

## What you need to do

### 1. Run the database migration

Add the `image_url` column to the `tickets` table. From the project root:

```bash
# PostgreSQL example (adjust connection string for your DB)
psql -d your_database_name -f app/migrations/add_ticket_image_url.sql
```

Or run the SQL manually in your DB client:

```sql
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS image_url VARCHAR(512) NULL;
```

### 2. Ensure upload directory is writable

The backend writes uploaded images to `static/uploads/tickets/` (relative to project root). On first upload the `tickets` subdir is created automatically. Ensure the process can create and write to `static/uploads/`.

### 3. Optional: environment variables

- `UPLOAD_TICKET_IMAGE_MAX_BYTES` — max file size in bytes (default 5 MB). Increase if needed.
- Upload directory is `static/uploads` under project root; change in `app/config.py` if you need a different path.

### 4. Test the flow

1. Start backend and dashboard.
2. Open "New Vehicle Entry", fill required fields, optionally choose an image.
3. Submit; the image is resized in the browser, uploaded to `POST /upload/ticket-image`, then the ticket is created with `image_url` set.
4. Open a ticket that has an image from the activity list; the view modal should show the image (loaded from the API origin).

## Backend details

- **Upload**: `POST /upload/ticket-image`, form field `file`, multipart. Returns `{ "url": "/uploads/tickets/ticket_<uuid>.<ext>" }`. Same auth as rest of API (Bearer or X-API-Key when configured).
- **Ticket entry**: Request body may include `"image_url": "/uploads/tickets/..."` (or any string); stored on `tickets.image_url`.
- **Dashboard list**: Each ticket in `/tickets/dashboard` includes `image_url` when set.
- **Serving**: Files under `static/uploads/` are served at `/uploads/` (e.g. `/uploads/tickets/ticket_abc.jpg`). The dashboard prepends the API base URL when displaying so the image loads from the backend.

## Resize

Resize is **client-side only** (Canvas, max 1200px, JPEG 0.85). No Pillow or server-side image processing.
