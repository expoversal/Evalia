CREATE TABLE audit.checkpoints (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  tender_id      UUID NOT NULL,
  head_id        UUID NOT NULL,          -- audit.ledger.id at checkpoint time
  head_hash      TEXT NOT NULL,          -- audit.ledger.hash of head_id
  entry_count    BIGINT NOT NULL,
  signature      TEXT NOT NULL,          -- Ed25519 over (tender|head_hash|count|created_at)
  signer_key_id  TEXT NOT NULL,
  prev_checkpoint_id UUID REFERENCES audit.checkpoints(id)
);
-- append-only
CREATE TRIGGER audit_checkpoints_no_update
  BEFORE UPDATE OR DELETE ON audit.checkpoints
  FOR EACH ROW EXECUTE FUNCTION audit.immutable();
