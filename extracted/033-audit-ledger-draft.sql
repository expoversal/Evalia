CREATE TABLE audit.ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ts TIMESTAMPTZ DEFAULT now(),
  tender_id UUID,
  envelope TEXT,
  actor UUID,
  action TEXT,  -- view | propose | accept | override | seal | unseal_attempt
  target_table TEXT,
  target_id UUID,
  before JSONB,
  after JSONB,
  prev_hash TEXT,
  hash TEXT NOT NULL
);

CREATE INDEX ON audit.ledger(tender_id, ts);
