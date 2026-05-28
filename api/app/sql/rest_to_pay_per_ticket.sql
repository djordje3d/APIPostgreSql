
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
