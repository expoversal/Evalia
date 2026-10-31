CREATE TABLE commercial.bq_checks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id     UUID NOT NULL,
  bidder_id     UUID NOT NULL REFERENCES core.bidders(id),
  issue_type    TEXT NOT NULL,     -- extension | summation | omission | unit_mismatch
  item_code     TEXT,
  detail        JSONB NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE commercial.alt_flags (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id     UUID NOT NULL,
  bidder_id     UUID NOT NULL REFERENCES core.bidders(id),
  item_code     TEXT NOT NULL,
  rate          NUMERIC NOT NULL,
  median_rate   NUMERIC NOT NULL,
  pct_of_median NUMERIC NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE commercial.seals (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id     UUID NOT NULL REFERENCES core.tenders(id),
  envelope      TEXT NOT NULL DEFAULT 'commercial',
  merkle_root   TEXT NOT NULL,
  leaf_count    INTEGER NOT NULL,
  snapshot      JSONB NOT NULL,
  signature     TEXT NOT NULL,
  signer_key_id TEXT NOT NULL,
  signed_by     UUID NOT NULL REFERENCES core.users(id),
  signed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_seal_id  UUID REFERENCES commercial.seals(id),
  revoked_at    TIMESTAMPTZ,
  revoked_by    UUID REFERENCES core.users(id),
  revoke_reason TEXT
);
