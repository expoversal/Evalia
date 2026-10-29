CREATE TABLE award.config (
  tender_id     UUID PRIMARY KEY REFERENCES core.tenders(id) ON DELETE CASCADE,
  formula       TEXT NOT NULL CHECK (formula IN ('lcp','qfm','pqm')),
  params        JSONB NOT NULL DEFAULT '{}',
  frozen_at     TIMESTAMPTZ,           -- set when the tender is published; cannot change after
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
