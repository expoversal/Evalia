-- ─────────────────────────────────────────────────────────
-- Schemas
-- ─────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS technical;
CREATE SCHEMA IF NOT EXISTS commercial;
CREATE SCHEMA IF NOT EXISTS audit;

-- ─────────────────────────────────────────────────────────
-- core: shared, non-envelope data
-- ─────────────────────────────────────────────────────────
CREATE TABLE core.users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  display_name  TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN (
                  'technical_evaluator','commercial_evaluator',
                  'evaluation_lead','procurement_officer',
                  'auditor','admin')),
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE core.tenders (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reference     TEXT UNIQUE NOT NULL,
  title         TEXT NOT NULL,
  -- state machine: draft -> open -> tech_sealed -> commercial_sealed -> awarded
  state         TEXT NOT NULL DEFAULT 'draft' CHECK (state IN (
                  'draft','open','tech_sealed','commercial_sealed','awarded')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE core.bidders (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id     UUID NOT NULL REFERENCES core.tenders(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  -- storage key for the bid PDF bundle; the storage bucket is access-controlled
  bundle_key    TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE core.requirements (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id          UUID NOT NULL REFERENCES core.tenders(id) ON DELETE CASCADE,
  clause_ref         TEXT NOT NULL,
  requirement_text   TEXT NOT NULL,
  mandatory          BOOLEAN NOT NULL DEFAULT TRUE,
  category           TEXT NOT NULL,
  conditional        BOOLEAN NOT NULL DEFAULT FALSE,
  condition          TEXT,
  verification_type  TEXT NOT NULL,
  evidence_expected  TEXT[] NOT NULL DEFAULT '{}',
  cross_refs         TEXT[] NOT NULL DEFAULT '{}',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tender_id, clause_ref)
);

CREATE TABLE core.rubric_criteria (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tender_id     UUID NOT NULL REFERENCES core.tenders(id) ON DELETE CASCADE,
  code          TEXT NOT NULL,          -- C1, C2, ...
  name          TEXT NOT NULL,
  weight        NUMERIC NOT NULL,
  scale_min     NUMERIC NOT NULL DEFAULT 0,
  scale_max     NUMERIC NOT NULL DEFAULT 10,
  anchors       JSONB NOT NULL DEFAULT '{}',
  envelope      TEXT NOT NULL CHECK (envelope IN ('technical','commercial')),
  UNIQUE (tender_id, code)
);
