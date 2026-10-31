-- ops/monthly/access-review.sql
SELECT u.email, u.display_name, u.role, u.active,
       max(al.ts) FILTER (WHERE al.action = 'view') AS last_view,
       max(al.ts) FILTER (WHERE al.action IN ('override','accept','propose')) AS last_write,
       count(*) FILTER (WHERE al.ts > now() - interval '30 days') AS actions_30d
FROM core.users u
LEFT JOIN audit.ledger al ON al.actor = u.id
GROUP BY u.id
ORDER BY u.role, u.email;
