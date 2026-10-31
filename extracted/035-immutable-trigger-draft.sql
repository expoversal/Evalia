CREATE OR REPLACE FUNCTION audit.immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit.ledger is append-only';
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON audit.ledger
  FOR EACH ROW EXECUTE FUNCTION audit.immutable();
