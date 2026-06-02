-- Add optional image_url to tickets (for ticket image on entry).
-- Run this once against your database, e.g.:
--   psql -d your_db -f api_python/app/sql/add_ticket_image_url.sql

ALTER TABLE tickets
ADD COLUMN IF NOT EXISTS image_url VARCHAR(512) NULL;

