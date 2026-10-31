CREATE OR REPLACE FUNCTION award.read_after_both_sealed(p_tender_id UUID)
RETURNS TABLE(...) 
SECURITY DEFINER
AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM technical.seals WHERE tender_id = p_tender_id AND revoked_at IS NULL) THEN
    RAISE EXCEPTION 'technical envelope not sealed';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM commercial.seals WHERE tender_id = p_tender_id AND revoked_at IS NULL) THEN
    RAISE EXCEPTION 'commercial envelope not sealed';
  END IF;
  -- return data
END;
$$ LANGUAGE plpgsql;
