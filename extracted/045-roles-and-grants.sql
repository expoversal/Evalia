CREATE ROLE app_role;
GRANT USAGE ON SCHEMA core, technical, commercial, audit TO app_role;
GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA core, technical, commercial TO app_role;
GRANT SELECT, INSERT ON audit.ledger TO app_role;
REVOKE UPDATE, DELETE, TRUNCATE ON audit.ledger FROM app_role;

-- The sealing service runs as a separate role that can only write seals
CREATE ROLE sealer_role;
GRANT USAGE ON SCHEMA technical, commercial, audit, core TO sealer_role;
GRANT SELECT ON core.tenders, core.requirements, core.bidders TO sealer_role;
GRANT SELECT ON technical.compliance_rows, technical.criterion_scores TO sealer_role;
GRANT SELECT ON commercial.bq_checks, commercial.alt_flags TO sealer_role;
GRANT INSERT ON technical.seals, commercial.seals TO sealer_role;
GRANT INSERT ON audit.ledger TO sealer_role;
