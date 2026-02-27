-- Rest to pay (to full paid): total amount still to pay for closed tickets
-- that are UNPAID or PARTIALLY_PAID.
-- Matches backend: GET /payments/outstanding (optional ?garage_id=...)

-- Single query (all garages if garage_id not used):
SELECT GREATEST(
  0,
  COALESCE(SUM(
    COALESCE(t.fee, 0) - COALESCE(p.total_paid, 0)
  ), 0)
) AS total_outstanding
FROM tickets t
LEFT JOIN (
  SELECT ticket_id, SUM(amount::numeric) AS total_paid
  FROM payments
  GROUP BY ticket_id
) p ON p.ticket_id = t.id
WHERE t.ticket_state = 'CLOSED'
  AND t.payment_status IN ('UNPAID', 'PARTIALLY_PAID')
  -- optional: for one garage, uncomment and set value:
  -- AND t.garage_id = 1
;

-- Same with explicit garage filter (use when you want one garage):
-- Replace :garage_id with the garage id (e.g. 1) when running manually.
/*
SELECT GREATEST(
  0,
  COALESCE(SUM(
    COALESCE(t.fee, 0) - COALESCE(p.total_paid, 0)
  ), 0)
) AS total_outstanding
FROM tickets t
LEFT JOIN (
  SELECT ticket_id, SUM(amount::numeric) AS total_paid
  FROM payments
  GROUP BY ticket_id
) p ON p.ticket_id = t.id
WHERE t.ticket_state = 'CLOSED'
  AND t.payment_status IN ('UNPAID', 'PARTIALLY_PAID')
  AND t.garage_id = 1;   -- your garage id
*/

-- Per-ticket breakdown (to verify which tickets contribute):
SELECT
  t.id AS ticket_id,
  t.garage_id,
  COALESCE(t.fee, 0) AS fee,
  COALESCE(p.total_paid, 0) AS total_paid,
  COALESCE(t.fee, 0) - COALESCE(p.total_paid, 0) AS rest_to_pay
FROM tickets t
LEFT JOIN (
  SELECT ticket_id, SUM(amount::numeric) AS total_paid
  FROM payments
  GROUP BY ticket_id
) p ON p.ticket_id = t.id
WHERE t.ticket_state = 'CLOSED'
  AND t.payment_status IN ('UNPAID', 'PARTIALLY_PAID')
ORDER BY t.id;
