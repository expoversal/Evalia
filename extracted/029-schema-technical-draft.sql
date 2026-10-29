CREATE TABLE technical.compliance_rows (
  id UUID PRIMARY KEY,
  tender_id UUID,
  bidder_id UUID,
  requirement_id UUID,
  status TEXT, -- compliant, partial, non_compliant, not_addressed, not_applicable
  ai_confidence TEXT,
  evidence JSONB, -- [{quote, doc_id, page}]
  gap_note TEXT,
  evaluator_flag TEXT,
  ai_proposed_at TIMESTAMPTZ,
  human_status TEXT,
  human_note TEXT,
  human_actor UUID,
  human_decided_at TIMESTAMPTZ,
  override_reason TEXT,
  audit_chain_id UUID
);

CREATE TABLE technical.criterion_scores (
  id UUID PRIMARY KEY,
  tender_id UUID,
  bidder_id UUID,
  criterion_id UUID,
  ai_score NUMERIC,
  ai_rationale TEXT,
  ai_confidence TEXT,
  human_score NUMERIC,
  human_actor UUID,
  human_decided_at TIMESTAMPTZ,
  override_reason TEXT
);

CREATE TABLE technical.seals (
  id UUID PRIMARY KEY,
  tender_id UUID,
  envelope TEXT,
  merkle_root TEXT,
  leaf_count INTEGER,
  snapshot_json JSONB,
  signature TEXT, -- Ed25519
  signed_by UUID,
  signed_at TIMESTAMPTZ,
  prev_seal_id UUID
);
