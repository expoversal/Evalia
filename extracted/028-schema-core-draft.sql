-- shared
CREATE SCHEMA core;
CREATE SCHEMA technical;
CREATE SCHEMA commercial;
CREATE SCHEMA audit;

-- core
CREATE TABLE core.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  display_name TEXT,
  role TEXT, -- technical_evaluator, commercial_evaluator, evaluation_lead, procurement_officer, auditor, admin
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE core.tenders (
  id UUID PRIMARY KEY,
  reference TEXT,
  title TEXT,
  rubric_id UUID,
  state TEXT, -- draft, open, sealed_technical, sealed_commercial, awarded
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE core.bidders (
  id UUID PRIMARY KEY,
  tender_id UUID REFERENCES core.tenders(id),
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE core.requirements (
  id UUID PRIMARY KEY,
  tender_id UUID,
  clause_ref TEXT,
  requirement_text TEXT,
  mandatory BOOLEAN,
  category TEXT,
  conditional BOOLEAN,
  condition TEXT,
  verification_type TEXT,
  evidence_expected TEXT[]
);

CREATE TABLE core.rubric_criteria (
  id UUID PRIMARY KEY,
  tender_id UUID,
  code TEXT, -- C1, C2, C3...
  name TEXT,
  weight NUMERIC,
  scale_min NUMERIC, scale_max NUMERIC,
  anchors JSONB,
  envelope TEXT -- technical or commercial
);
