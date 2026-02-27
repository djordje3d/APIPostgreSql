-- Per-ticket "Rest to pay" to compare with frontend "Ticket activity (last 10)".
--
-- IMPORTANT: The app has NO "rest to pay" column in tickets. The table only has "fee".
-- Rest to pay is always computed as:  fee - SUM(payments for that ticket)
-- (Frontend shows "–" for OPEN and PAID tickets; for others it shows that value.)
--
-- 1) ORDER: Frontend shows tickets in NEWEST-first order (ORDER BY id DESC).
--    Your query was ORDER BY id ASC (oldest first), so row order was reversed.
--
-- 2) FEE: Frontend uses the FEE returned by the API. The API returns COMPUTED fee
--    (from entry_time, exit_time and rate) when both times are set; otherwise stored fee.
--    This query uses the STORED fee from tickets.fee. If you changed entry_time
--    or exit_time directly in the DB, stored fee was NOT updated, so stored fee
--    can differ from what the frontend shows (frontend gets computed fee from API).
--
-- Run this for garage 6, same order as frontend (DESC):

SELECT
  t.id AS ticket_id,
  t.ticket_state,
  t.payment_status,
  COALESCE(t.fee, 0) AS fee_stored,
  COALESCE(p.total_paid, 0) AS total_paid,
  GREATEST(0, COALESCE(t.fee, 0) - COALESCE(p.total_paid, 0)) AS rest_to_pay
FROM tickets t
LEFT JOIN (
  SELECT ticket_id, SUM(amount::numeric) AS total_paid
  FROM payments
  GROUP BY ticket_id
) p ON p.ticket_id = t.id
WHERE t.garage_id = 6
ORDER BY t.id DESC;

-- To match frontend "Rest to pay" exactly you must use the same FEE the API uses.
-- When entry_time and exit_time are both set, the API computes fee from duration
-- and rate (vehicle type or garage default_rate). So if stored fee and frontend
-- disagree, update tickets.fee for those rows or rely on the API (dashboard
-- already returns computed fee so the table shows the right rest-to-pay).
