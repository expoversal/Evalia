CREATE TABLE audit.ledger (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ts           TIMESTAMPTZ NOT NULL DEFAULT now(),
  tender_id    UUID NOT NULL,
  envelope     TEXT,                    -- 'technical' | 'commercial' | null (cross-cutting)
  actor        UUID REFERENCES core.users(id),
  action       TEXT NOT NULL,           -- view | propose | accept | override | seal | unseal | reveal_attempt
  target_table TEXT,
  target_id    UUID,
  before       JSONB,
  after        JSONB,
  prev_hash    TEXT NOT NULL,
  hash         TEXT NOT NULL
);
CREATE INDEX ON audit.ledger (tender_id, ts DESC);
CREATE INDEX ON audit.ledger (envelope, ts DESC);

-- DB-level immutability (belt + braces over role-level revocation)
CREATE OR REPLACE FUNCTION audit.immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit.ledger is append-only';
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON audit.ledger
  FOR EACH ROW EXECUTE FUNCTION audit.immutable();
