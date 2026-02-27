-- Why "Spot" on the frontend doesn't match tickets.spot_id in the database
-- ==========================================================================
--
-- The frontend "Spot" column shows SPOT_CODE (e.g. "A-01", "10010"), not spot_id.
-- The database column tickets.spot_id is a NUMBER (foreign key to parking_spot.id).
--
-- So you are comparing two different things:
--   - Frontend "Spot"  = parking_spot.code  (string, human-readable)
--   - tickets.spot_id = parking_spot.id    (integer, primary key)
--
-- They are not the same column. To see what the frontend shows, use the code:
--

SELECT
  t.id AS ticket_id,
  t.spot_id,                    -- number (this is what the API also returns)
  ps.code AS spot_code           -- this is what the frontend displays in "Spot" column
FROM tickets t
LEFT JOIN parking_spot ps ON ps.id = t.spot_id
WHERE t.garage_id = 6
ORDER BY t.id DESC;

-- So: spot_id in the API response is exactly tickets.spot_id from the DB (same value).
-- The UI just displays spot_code (from parking_spot.code) for readability, not spot_id.
