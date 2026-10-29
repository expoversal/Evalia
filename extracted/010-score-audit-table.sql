CREATE TABLE score_audit (
  id BIGSERIAL PRIMARY KEY,
  evaluation_id UUID NOT NULL,
  criterion_id TEXT NOT NULL,
  actor TEXT NOT NULL,            -- 'system:gpt-4o@2026-03' or user id
  action TEXT NOT NULL,           -- proposed | accepted | overridden
  payload JSONB NOT NULL,
  prev_hash TEXT,
  hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
