CREATE OR REPLACE FUNCTION technical.reject_sealed_writes() RETURNS trigger AS $$
DECLARE
  sealed BOOLEAN;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM technical.seals
    WHERE tender_id = COALESCE(NEW.tender_id, OLD.tender_id)
      AND revoked_at IS NULL
  ) INTO sealed;
  IF sealed THEN
    RAISE EXCEPTION 'technical envelope is sealed; no writes permitted';
  END IF;
  RETURN COALESCE(NEW, OLD);
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER technical_no_write_when_sealed
  BEFORE INSERT OR UPDATE OR DELETE ON technical.compliance_rows
  FOR EACH ROW EXECUTE FUNCTION technical.reject_sealed_writes();

-- same trigger on technical.criterion_scores, commercial.bq_checks, commercial.alt_flags
