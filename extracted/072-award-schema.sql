CREATE SCHEMA IF NOT EXISTS award;

-- The award service role can ONLY call this function. No direct table access.
CREATE ROLE award_role;
GRANT USAGE ON SCHEMA award TO award_role;

-- Return type is the union of both envelopes in a single, structured shape.
CREATE TYPE award.bidder_package AS (
  bidder_id         UUID,
  bidder_name       TEXT,
  -- technical
  compliance        JSONB,           -- [{clause_ref, mandatory, human_status, evidence}]
  criterion_scores  JSONB,           -- [{code, weight, human_score}]
  gates_passed      BOOLEAN,
  -- commercial
  bq_issues         JSONB,
  alt_flags         JSONB,
  evaluated_price   NUMERIC
);

-- SECURITY DEFINER function: runs as owner, checks both seals itself.
-- award_role does not need direct SELECT on technical.* or commercial.*.
CREATE OR REPLACE FUNCTION award.read_after_both_sealed(p_tender_id UUID)
RETURNS SETOF award.bidder_package
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = award, pg_catalog
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM technical.seals
    WHERE tender_id = p_tender_id AND revoked_at IS NULL
  ) THEN
    RAISE EXCEPTION 'technical envelope not sealed for tender %', p_tender_id
      USING ERRCODE = '42501';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM commercial.seals
    WHERE tender_id = p_tender_id AND revoked_at IS NULL
  ) THEN
    RAISE EXCEPTION 'commercial envelope not sealed for tender %', p_tender_id
      USING ERRCODE = '42501';
  END IF;

  RETURN QUERY
  SELECT
    b.id,
    b.name,
    -- compliance
    COALESCE(
      (SELECT jsonb_agg(jsonb_build_object(
                'clause_ref', r.clause_ref,
                'mandatory',  r.mandatory,
                'status',     COALESCE(cr.human_status, cr.ai_status),
                'evidence',   cr.ai_evidence,
                'gap_note',   cr.ai_gap_note))
         FROM technical.compliance_rows cr
         JOIN core.requirements r ON r.id = cr.requirement_id
        WHERE cr.bidder_id = b.id AND cr.tender_id = p_tender_id),
      '[]'::jsonb),
    -- criterion scores
    COALESCE(
      (SELECT jsonb_agg(jsonb_build_object(
                'code',         rc.code,
                'weight',       rc.weight,
                'human_score',  cs.human_score,
                'ai_score',     cs.ai_score))
         FROM technical.criterion_scores cs
         JOIN core.rubric_criteria rc ON rc.id = cs.criterion_id
        WHERE cs.bidder_id = b.id
          AND cs.tender_id = p_tender_id
          AND rc.envelope = 'technical'),
      '[]'::jsonb),
    -- gates
    NOT EXISTS (
      SELECT 1 FROM technical.compliance_rows cr2
      JOIN core.requirements r2 ON r2.id = cr2.requirement_id
      WHERE cr2.bidder_id = b.id
        AND cr2.tender_id = p_tender_id
        AND r2.mandatory
        AND r2.category = 'gate'
        AND COALESCE(cr2.human_status, cr2.ai_status)
            IN ('non_compliant','not_addressed')
    ),
    -- commercial
    COALESCE(
      (SELECT jsonb_agg(jsonb_build_object(
                'issue_type', issue_type,
                'item_code',  item_code,
                'detail',     detail))
         FROM commercial.bq_checks
        WHERE bidder_id = b.id AND tender_id = p_tender_id),
      '[]'::jsonb),
    COALESCE(
      (SELECT jsonb_agg(jsonb_build_object(
                'item_code', item_code,
                'rate',      rate,
                'median',    median_rate,
                'pct',       pct_of_median))
         FROM commercial.alt_flags
        WHERE bidder_id = b.id AND tender_id = p_tender_id),
      '[]'::jsonb),
    -- evaluated_price — the gross submitted price, from the BQ total row
    (SELECT (detail->>'total')::numeric
       FROM commercial.bq_checks
      WHERE bidder_id = b.id
        AND tender_id = p_tender_id
        AND issue_type = 'total'
      LIMIT 1)
  FROM core.bidders b
  WHERE b.tender_id = p_tender_id;
END;
$$;

REVOKE ALL ON FUNCTION award.read_after_both_sealed(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION award.read_after_both_sealed(UUID) TO award_role;
