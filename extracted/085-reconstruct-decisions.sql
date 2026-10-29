-- Latest state of a compliance row, from the ledger alone
WITH decisions AS (
  SELECT DISTINCT ON (target_id)
    target_id,
    after->>'human_status' AS human_status,
    after->>'override_reason' AS override_reason,
    ts
  FROM audit_witness.ledger
  WHERE action = 'override' AND target_table = 'technical.compliance_rows'
  ORDER BY target_id, ts DESC
)
SELECT * FROM decisions;
