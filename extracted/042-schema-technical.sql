CREATE TABLE technical.compliance_rows (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id         UUID NOT NULL,
  bidder_id         UUID NOT NULL REFERENCES core.bidders(id) ON DELETE CASCADE,
  requirement_id    UUID NOT NULL REFERENCES core.requirements(id),
  -- AI proposal
  ai_status         TEXT NOT NULL CHECK (ai_status IN (
                      'compliant','partial','non_compliant',
                      'not_addressed','not_applicable')),
  ai_confidence     TEXT NOT NULL CHECK (ai_confidence IN ('high','medium','low')),
  ai_evidence       JSONB NOT NULL DEFAULT '[]',   -- [{quote, doc_id, page}]
  ai_gap_note       TEXT,
  ai_flag           TEXT NOT NULL DEFAULT 'none',  -- none | needs_clarification | ambiguous_requirement
  ai_proposed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  ai_model          TEXT NOT NULL,                 -- e.g. "gpt-4o@2026-03"
  ai_prompt_hash    TEXT NOT NULL,
  -- human decision
  human_status      TEXT CHECK (human_status IN (
                      'compliant','partial','non_compliant',
                      'not_addressed','not_applicable')),
  human_note        TEXT,
  override_reason   TEXT,
  human_actor       UUID REFERENCES core.users(id),
  human_decided_at  TIMESTAMPTZ,
  UNIQUE (tender_id, bidder_id, requirement_id)
);

CREATE TABLE technical.criterion_scores (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id         UUID NOT NULL,
  bidder_id         UUID NOT NULL REFERENCES core.bidders(id) ON DELETE CASCADE,
  criterion_id      UUID NOT NULL REFERENCES core.rubric_criteria(id),
  ai_score          NUMERIC,
  ai_rationale      TEXT,
  ai_confidence     TEXT CHECK (ai_confidence IN ('high','medium','low')),
  ai_evidence       JSONB NOT NULL DEFAULT '[]',
  ai_proposed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  ai_model          TEXT NOT NULL,
  ai_prompt_hash    TEXT NOT NULL,
  human_score       NUMERIC,
  human_note        TEXT,
  override_reason   TEXT,
  human_actor       UUID REFERENCES core.users(id),
  human_decided_at  TIMESTAMPTZ,
  UNIQUE (tender_id, bidder_id, criterion_id)
);

CREATE TABLE technical.seals (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id     UUID NOT NULL REFERENCES core.tenders(id),
  envelope      TEXT NOT NULL DEFAULT 'technical',
  merkle_root   TEXT NOT NULL,
  leaf_count    INTEGER NOT NULL,
  snapshot      JSONB NOT NULL,          -- canonical rows, so verification is possible
  signature     TEXT NOT NULL,           -- base64 Ed25519 over (tender|env|root|count|prev)
  signer_key_id TEXT NOT NULL,
  signed_by     UUID NOT NULL REFERENCES core.users(id),
  signed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_seal_id  UUID REFERENCES technical.seals(id),
  revoked_at    TIMESTAMPTZ,
  revoked_by    UUID REFERENCES core.users(id),
  revoke_reason TEXT
);
CREATE UNIQUE INDEX one_active_technical_seal
  ON technical.seals (tender_id)
  WHERE revoked_at IS NULL;
