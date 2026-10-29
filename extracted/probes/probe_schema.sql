-- Audit probes for the extracted SQL schema (fragments 041-078). Synthetic data only. See README.md.
\set ON_ERROR_STOP 0
\echo '--- P1 setup: one tender, users, two bidders, one mandatory document requirement'
INSERT INTO core.users(id,email,display_name,role) VALUES
 ('00000000-0000-0000-0000-000000000001','lead@x','Lead','evaluation_lead'),
 ('00000000-0000-0000-0000-000000000002','tech@x','Tech','technical_evaluator');
INSERT INTO core.tenders(id,reference,title) VALUES ('10000000-0000-0000-0000-000000000001','T-1','Test');
INSERT INTO core.bidders(id,tender_id,name,bundle_key) VALUES
 ('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','Bidder A','a'),
 ('20000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000001','Bidder B','b');
INSERT INTO core.requirements(id,tender_id,clause_ref,requirement_text,mandatory,category,verification_type) VALUES
 ('30000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','ITT 4.1','Submit bid security',true,'document','document_present');
INSERT INTO technical.compliance_rows(tender_id,bidder_id,requirement_id,ai_status,ai_confidence,ai_model,ai_prompt_hash,human_status) VALUES
 ('10000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000001','30000000-0000-0000-0000-000000000001','compliant','high','m','h','compliant'),
 ('10000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000002','30000000-0000-0000-0000-000000000001','not_addressed','high','m','h','not_addressed');
\echo '--- P2 reject_sealed_writes trigger on DELETE with no seal (expect success)'
BEGIN; DELETE FROM technical.compliance_rows WHERE bidder_id='20000000-0000-0000-0000-000000000002'; ROLLBACK;
\echo '--- P3 seal both envelopes, then try a write (expect trigger exception)'
INSERT INTO technical.seals(tender_id,merkle_root,leaf_count,snapshot,signature,signer_key_id,signed_by) VALUES
 ('10000000-0000-0000-0000-000000000001','r',2,'{}','s','k','00000000-0000-0000-0000-000000000001');
INSERT INTO commercial.seals(tender_id,merkle_root,leaf_count,snapshot,signature,signer_key_id,signed_by) VALUES
 ('10000000-0000-0000-0000-000000000001','r',0,'{}','s','k','00000000-0000-0000-0000-000000000001');
UPDATE technical.compliance_rows SET human_status='compliant' WHERE bidder_id='20000000-0000-0000-0000-000000000002';
\echo '--- P4 award.read_after_both_sealed: bidder B is not_addressed on a mandatory requirement'
SELECT bidder_name, gates_passed, evaluated_price FROM award.read_after_both_sealed('10000000-0000-0000-0000-000000000001') ORDER BY 1;
\echo '--- P5 app_role revokes the technical seal directly (bypasses co-signed unseal)'
SET ROLE app_role;
UPDATE technical.seals SET revoked_at = now(), revoke_reason = 'no co-signer' WHERE tender_id='10000000-0000-0000-0000-000000000001';
UPDATE technical.compliance_rows SET human_status='compliant' WHERE bidder_id='20000000-0000-0000-0000-000000000002';
SELECT bidder_id, human_status FROM technical.compliance_rows ORDER BY 1;
RESET ROLE;
\echo '--- P6 app_role attempts UPDATE on audit.ledger (expect permission denied)'
INSERT INTO audit.ledger(tender_id,action,prev_hash,hash) VALUES ('10000000-0000-0000-0000-000000000001','view','0','h1');
SET ROLE app_role; UPDATE audit.ledger SET action='x'; RESET ROLE;
\echo '--- P7 superuser bypass of the append-only claim'
ALTER TABLE audit.ledger DISABLE TRIGGER audit_no_update;
UPDATE audit.ledger SET ts = ts - interval '30 days';
ALTER TABLE audit.ledger ENABLE TRIGGER audit_no_update;
TRUNCATE audit.ledger;
SELECT count(*) AS ledger_rows_after_truncate FROM audit.ledger;
\echo '--- P8 ops/02-verify-chain.sh calls audit.verify_chain() in SQL'
SELECT audit.verify_chain(id) FROM core.tenders;
\echo '--- P9 sample_seals(): signed_at LIKE on timestamptz'
SELECT id FROM technical.seals WHERE signed_at LIKE '2026-04%' AND revoked_at IS NULL;
\echo '--- P10 rotate.py: append_audit with tender_id "*"'
SELECT '*'::uuid;
\echo '--- P11 replay_ledger.py DDL'
CREATE TABLE IF NOT EXISTS audit_witness.ledger (id UUID, hash TEXT, PRIMARY KEY (hash));
CREATE SCHEMA IF NOT EXISTS audit_witness;
CREATE TABLE IF NOT EXISTS audit_witness.ledger (id UUID, tender_id UUID, ts TIMESTAMPTZ, hash TEXT, PRIMARY KEY (hash));
CREATE INDEX IF NOT EXISTS ON audit_witness.ledger (tender_id, ts);
\echo '--- P12 coverage endpoint against commercial envelope'
SELECT count(*) FROM commercial.compliance_rows;
SELECT count(*) FROM commercial.criterion_scores;
\echo '--- P13 award.runs table used by award/service.py'
SELECT count(*) FROM award.runs;
\echo '--- P14 audit.exports table used by audit/export.py'
SELECT count(*) FROM audit.exports;
\echo '--- P15 technical.key_transitions used by rotate.py'
SELECT count(*) FROM technical.key_transitions;
