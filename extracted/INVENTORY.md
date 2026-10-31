# Code fragment inventory

This directory holds every code fragment in [`docs/deepseek-source.md`](../docs/deepseek-source.md), extracted verbatim, one file per fragment, together with a verdict on whether each fragment runs. The fragments are reference material only. None of them is Evalia code, and none should be copied into Evalia without being re-derived and tested (see [`CLAUDE.md`](../CLAUDE.md)).

Companion documents: [`docs/01-designed-vs-built.md`](../docs/01-designed-vs-built.md) (audit findings), [`docs/02-architecture.md`](../docs/02-architecture.md), [`docs/03-llm-layer.md`](../docs/03-llm-layer.md), [`docs/04-v1-scope.md`](../docs/04-v1-scope.md).

## Headline results

- **Fact.** The transcript contains 130 code fragments, amounting to 4,213 source lines. Of these, 19 sit inside DeepSeek's visible reasoning and are drafts that the final answers supersede.
- **Fact.** Of the 49 Python fragments in DeepSeek's final answers, 9 run as written, 7 run once trivial omissions are supplied (a missing standard import, or a definition given elsewhere in the transcript), 19 depend on code, tables or services that the transcript never defines, and 14 fail for reasons beyond missing context.
- **Fact.** Three of the nine Python fragments that run as written are type or policy definitions. Of the six that do real work, four have defects confirmed by test: the audit ledger (053), the award formulas (073), the award report (076) and the offline verifier (082). Only the rate-outlier function (015) and the Merkle sealing module (050) run as written and behave as described.
- **Fact.** All 10 SQL fragments in the final answers that define schema (010, 041 to 045, 052, 072, 074 and 078) execute on PostgreSQL 16.15. The probes nonetheless confirmed logic defects in the schema. The application role can revoke a seal without co-signature (P5). The award function passes bidders that failed a mandatory requirement and returns no price for any bidder (P4). A superuser can rewrite or truncate the "append-only" ledger (P7).
- **Fact.** The four TSX components parse, but they cannot be built: there is no Next.js project, and the shared API client `@/lib/api` is never written.
- **Fact.** Every shell command for the distributed key generation ceremony calls a `frost-dkg` command-line tool that does not exist in the repository it is said to come from.
- **Fact.** DeepSeek stated "I've written real, compilable code" (source line 1956). The results above show that this claim does not hold for most of the Python.
- **Fact.** Four Markdown fragments (105, 109, 113, 114) are invented example records with invented staff names, tender references and register entries, and one names a real audit firm. They are not records of events and must never be cited as such.

## Method

1. **Locating fragments.** The source is a copy of a chat transcript with no Markdown code fences. A code block appears as a bare language label (`python`, `sql`, `yaml`, `tsx`, `bash`, `json`, `markdown`, `text`) on its own line, followed by a blank line and the code. The search found 123 unindented labels and 9 indented ones inside list items. Two of the unindented "labels" (source lines 802 and 6218, both `go`) are user turns, not code. That leaves 130 fragments.
2. **Setting boundaries.** Each fragment ends where the transcript's prose resumes. Boundaries were set by hand after reading the full transcript, then checked mechanically by printing the last line of each fragment and the first line after it. Indented fragments were de-indented; no other change was made.
3. **Draft or answer.** DeepSeek's visible reasoning is part of the transcript. Fragments inside it are marked "draft".
4. **Testing.** Tests ran in an isolated environment on 29 October 2026: Python 3.13 with the dependencies the fragments import, PostgreSQL 16.15, and the TypeScript 6.0 parser.
   - Python: parsed with `ast`, undefined names listed with pyflakes, and behaviour probed where the fragment does substantive work.
   - SQL: executed in transcript order on a fresh database, then probed with test data.
   - Shell: `bash -n` syntax checks. No shell script was executed, because each one calls infrastructure that does not exist.
   - YAML and JSON: parsed.
   - TSX: parsed for syntax errors only.
5. **Probe identifiers.** Codes such as P008c, L2 and V4 refer to probes in [`probes/`](probes/). Running them reproduces every behavioural claim in the table.

## Verdict key

| Verdict | Meaning |
|---|---|
| Yes | Executes as written. Where a probe exists, the note records whether it also behaves as the transcript claims. |
| Yes, after trivial fixes | Executes once a missing standard import, or a definition given elsewhere in the transcript, is supplied. |
| Executes | SQL that executes on PostgreSQL 16.15. Behavioural defects are noted separately. |
| Parses | YAML, JSON or TSX that is syntactically valid. Nothing in the transcript consumes the data files, and the TSX cannot be built. |
| Not run | Shell with valid syntax that depends on tools or infrastructure that do not exist. |
| No: incomplete | Depends on functions, objects, tables or services that the transcript never defines. |
| No: defective | Fails or gives wrong results for reasons beyond missing context: invented library APIs, syntax errors, runtime errors or logic errors. |
| No: fails | SQL that fails on PostgreSQL 16.15. |
| Not code | Diagram, prompt, checklist, file layout or illustrative terminal output. |
| Not code: fictional record | Example record containing invented people, dates or identifiers. |

## Counts by language and verdict

| Verdict | python | sql | tsx | bash | yaml | json | text | markdown | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Yes | 10 |  |  | 1 |  |  |  |  | 11 |
| Yes, after trivial fixes | 8 |  |  |  |  |  |  |  | 8 |
| Executes |  | 15 |  |  |  |  |  |  | 15 |
| Parses |  |  | 4 |  | 3 | 2 |  |  | 9 |
| Not run |  |  |  | 4 |  |  |  |  | 4 |
| No: incomplete | 24 |  |  |  |  |  |  |  | 24 |
| No: defective | 14 |  |  | 12 |  |  |  |  | 26 |
| No: fails |  | 3 |  |  |  |  |  |  | 3 |
| Not code |  |  |  | 1 |  |  | 25 |  | 26 |
| Not code: fictional record |  |  |  |  |  |  |  | 4 | 4 |
| **Total** | 56 | 18 | 4 | 18 | 3 | 2 | 25 | 4 | **130** |

## Fragment table

Source lines refer to `docs/deepseek-source.md`. Turn numbers follow the conversation (see `docs/01-designed-vs-built.md`, section 2).

| # | File | Source lines | Turn | Draft? | Section | What it is | Runs? | Evidence and notes |
|---:|---|---|---:|---|---|---|---|---|
| 1 | [`001-pip-install-jtc-client.sh`](001-pip-install-jtc-client.sh) | 32-32 | 1 |  | Reply 1 | pip install command for jtc-client | Yes | Installs jtc-client 0.1.0 from PyPI. The package describes itself as a client for ‘Judges That Code’ tool services and does not mention JTC Corporation or Singapore. It is unrelated to EVA. |
| 2 | [`002-rubric-draft.yaml`](002-rubric-draft.yaml) | 161-178 | 3 | draft | Reasoning | Rubric YAML, first draft | Parses | Superseded by 005. |
| 3 | [`003-models-draft.py`](003-models-draft.py) | 183-199 | 3 | draft | Reasoning | Evidence/CriterionScore models, first draft | Yes | Model definitions only; `Field` is imported but unused. Superseded by 006. |
| 4 | [`004-architecture-diagram.txt`](004-architecture-diagram.txt) | 239-248 | 3 |  | §2 Architecture | Pipeline architecture diagram | Not code | Diagram. |
| 5 | [`005-rubric-v3.yaml`](005-rubric-v3.yaml) | 256-280 | 3 |  | §3 Data model | rubric_v3.yaml (generic rubric) | Parses | No fragment loads or validates a rubric file. Rules such as `audited_equity >= 0.3 * contract_value` are free text with no evaluator. The scored weights total 70, not 100. |
| 6 | [`006-criterion-score-models.py`](006-criterion-score-models.py) | 285-300 | 3 |  | §3 Data model | Evidence and CriterionScore Pydantic models | Yes | Pydantic definitions only. |
| 7 | [`007-score-criterion.py`](007-score-criterion.py) | 307-322 | 3 |  | §4 Scoring pipeline | score_criterion() | No: incomplete | `SCORING_PROMPT`, `render_chunks`, the retriever and `llm.structured()` are never defined. The code hard-codes one vendor’s model name. |
| 8 | [`008-verify-evidence.py`](008-verify-evidence.py) | 327-344 | 3 |  | §4 Scoring pipeline | verify_evidence() quote check | Yes, after trivial fixes | Needs `CriterionScore` from 006. It rejects an invented quote (P008b). It keeps only the last chunk per document, so it also rejects a genuine quote from an earlier chunk of the same document (P008c). Page numbers are not checked. |
| 9 | [`009-aggregate-with-gates.py`](009-aggregate-with-gates.py) | 349-365 | 3 |  | §5 Aggregation | aggregate() with gates | No: incomplete | `evaluate_gates()` is never defined (P009a). With a stub, a scored criterion whose score is `None`, which the schema permits, raises TypeError (P009b). |
| 10 | [`010-score-audit-table.sql`](010-score-audit-table.sql) | 377-387 | 3 |  | §6 HITL and audit | score_audit table | Executes | Superseded by 044. |
| 11 | [`011-construction-rubric.yaml`](011-construction-rubric.yaml) | 539-614 | 4 |  | §2 Construction rubric | construction_rubric.yaml (Singapore-flavoured) | Parses | No code reads the `sub_criteria`, `formula`, `checks`, `must_address` or `check: registry_lookup` fields, and no registry lookup exists. Singapore-specific (BCA, PSSCOC, WSH). |
| 12 | [`012-requirement-model.py`](012-requirement-model.py) | 629-638 | 4 |  | §3 Compliance matrix | Requirement model and extract_requirements() stub | Yes, after trivial fixes | Needs `BaseModel` and `Literal` imports. `extract_requirements()` is an empty stub. |
| 13 | [`013-build-matrix.py`](013-build-matrix.py) | 643-659 | 4 |  | §3 Compliance matrix | ComplianceRow model and build_matrix() | No: incomplete | `bid_doc_ids` is undefined and the LLM call passes a literal Ellipsis. Its `ComplianceRow` lacks the `confidence` and `evaluator_flag` fields that 025 sets (P025). |
| 14 | [`014-check-bq.py`](014-check-bq.py) | 667-684 | 4 |  | §4 BQ | BQRow model and check_bq() | Yes, after trivial fixes | Needs a `BaseModel` import. Detects extension errors (P014). The summation, omission, unit-mismatch and provisional-sum checks claimed in the prose are not implemented. The function takes neither a stated total nor the tender BQ. |
| 15 | [`015-flag-abnormal-rates.py`](015-flag-abnormal-rates.py) | 704-727 | 4 |  | §5 ALT detection | flag_abnormal_rates() | Yes | Flags a rate at 50% of the median among five bidders (P015a). It returns nothing with fewer than four bidders (P015b), so it is silent on a three-bid tender and on a single bid. |
| 16 | [`016-clause-chunk.py`](016-clause-chunk.py) | 937-948 | 5 |  | A.1 Chunking | ClauseChunk dataclass | Yes | Dataclass definition only. |
| 17 | [`017-chunk-by-clause.py`](017-chunk-by-clause.py) | 953-985 | 5 |  | A.1 Chunking | chunk_by_clause() with Docling | No: defective | Calls Docling methods that do not exist (`iterate_blocks`, `path_to`, `parent_clause_of`); docling-core 2.105.0 offers `iterate_items`. Three helper functions are never defined. |
| 18 | [`018-two-pass-outline.txt`](018-two-pass-outline.txt) | 1001-1003 | 5 |  | A.2 Two-pass extraction | Two-pass outline | Not code | Outline. |
| 19 | [`019-prompt-1a-candidate-detection.txt`](019-prompt-1a-candidate-detection.txt) | 1008-1046 | 5 |  | A.2 Prompt 1a | Prompt 1a: candidate detection | Not code | Prompt. Fragment 007 fills prompts with `str.format()`. Here that raises KeyError because the literal JSON braces are not escaped (P019). |
| 20 | [`020-prompt-1b-structured-extraction.txt`](020-prompt-1b-structured-extraction.txt) | 1052-1104 | 5 |  | A.2 Prompt 1b | Prompt 1b: structured extraction | Not code | Prompt; `str.format()` raises KeyError (P020). |
| 21 | [`021-dedup-requirements.py`](021-dedup-requirements.py) | 1111-1146 | 5 |  | A.3 Dedup | canonical_id() and dedup() | Yes, after trivial fixes | Needs `import re` (P021a). `canonical_id()` replaces every number with `#`, so requirements that differ only in threshold are merged. A S$10 million and a S$1 million turnover requirement become one record carrying the S$10 million text (P021b), which breaks the transcript’s own 100% threshold-preservation gate. `embed_fn` is accepted but never used. |
| 22 | [`022-bid-index.py`](022-bid-index.py) | 1191-1197 | 5 |  | B.2 Bid index | BidIndex dataclass | No: incomplete | `SectionChunk` and `VectorStore` are never defined; `BM25Okapi` is not imported. |
| 23 | [`023-prompt-b1-navigation.txt`](023-prompt-b1-navigation.txt) | 1213-1236 | 5 |  | B.3 Prompt B1 | Prompt B1: navigation | Not code | Prompt; `str.format()` raises KeyError (P023). |
| 24 | [`024-prompt-b2-compliance-resolver.txt`](024-prompt-b2-compliance-resolver.txt) | 1243-1327 | 5 |  | B.3 Prompt B2 | Prompt B2: compliance resolver | Not code | Prompt; `str.format()` raises KeyError (P024). Interpretation: its status definitions and absence protocol are the most reusable content in the transcript. |
| 25 | [`025-verify-and-sanitise.py`](025-verify-and-sanitise.py) | 1342-1366 | 5 |  | B.4 Post-processing | verify_and_sanitise() | No: defective | With the `ComplianceRow` model from 013, it raises ValueError on its first assignment to `evaluator_flag`, a field that model lacks (P025). |
| 26 | [`026-matrix-metrics.py`](026-matrix-metrics.py) | 1387-1393 | 5 |  | B.7 Calibration | MatrixMetrics dataclass | Yes, after trivial fixes | Needs a `dataclass` import. No fragment computes these metrics. |
| 27 | [`027-arch-recap-draft.txt`](027-arch-recap-draft.txt) | 1522-1527 | 6 | draft | Reasoning | Architecture recap, draft | Not code | Draft diagram. |
| 28 | [`028-schema-core-draft.sql`](028-schema-core-draft.sql) | 1532-1586 | 6 | draft | Reasoning | core schema, draft | Executes | Draft; superseded by 041. |
| 29 | [`029-schema-technical-draft.sql`](029-schema-technical-draft.sql) | 1591-1635 | 6 | draft | Reasoning | technical schema, draft | Executes | Draft; superseded by 042. |
| 30 | [`030-sealing-draft.py`](030-sealing-draft.py) | 1641-1689 | 6 | draft | Reasoning | Merkle sealing, draft | No: incomplete | Draft; `_utcnow_iso()` is undefined. Superseded by 050. |
| 31 | [`031-rbac-draft.py`](031-rbac-draft.py) | 1694-1720 | 6 | draft | Reasoning | RBAC middleware, draft | No: incomplete | Draft; superseded by 046 and 048. |
| 32 | [`032-require-envelope-draft.py`](032-require-envelope-draft.py) | 1725-1733 | 6 | draft | Reasoning | require_envelope() with seal check, draft | No: incomplete | Draft; superseded by 048. |
| 33 | [`033-audit-ledger-draft.sql`](033-audit-ledger-draft.sql) | 1738-1753 | 6 | draft | Reasoning | audit.ledger, draft | Executes | Draft; superseded by 044. |
| 34 | [`034-revoke-draft.sql`](034-revoke-draft.sql) | 1758-1758 | 6 | draft | Reasoning | REVOKE on audit.ledger, draft | No: fails | Revokes from `app_role`, which is first created in 045. It executed in the test only because 045 had already created the role on the same cluster. |
| 35 | [`035-immutable-trigger-draft.sql`](035-immutable-trigger-draft.sql) | 1763-1769 | 6 | draft | Reasoning | audit.immutable() trigger, draft | Executes | Draft; superseded by 044. |
| 36 | [`036-matrix-api-draft.py`](036-matrix-api-draft.py) | 1774-1797 | 6 | draft | Reasoning | Matrix API, draft | No: incomplete | Draft; superseded by 055. |
| 37 | [`037-override-draft.py`](037-override-draft.py) | 1802-1824 | 6 | draft | Reasoning | Override endpoint, draft | No: incomplete | Draft; superseded by 057. |
| 38 | [`038-append-audit-draft.py`](038-append-audit-draft.py) | 1853-1877 | 6 | draft | Reasoning | append_audit(), draft | Yes, after trivial fixes | Draft; needs `hashlib` and `json`. Superseded by 053. |
| 39 | [`039-sealing-workflow-draft.txt`](039-sealing-workflow-draft.txt) | 1882-1893 | 6 | draft | Reasoning | Sealing workflow, draft | Not code | Draft workflow. |
| 40 | [`040-architecture-envelopes.txt`](040-architecture-envelopes.txt) | 1960-1977 | 6 |  | Architecture | Envelope architecture diagram | Not code | Diagram. |
| 41 | [`041-schema-core.sql`](041-schema-core.sql) | 1992-2061 | 6 |  | Part 1 Schema | core schema | Executes |  |
| 42 | [`042-schema-technical.sql`](042-schema-technical.sql) | 2066-2131 | 6 |  | Part 1 Schema | technical schema | Executes |  |
| 43 | [`043-schema-commercial.sql`](043-schema-commercial.sql) | 2136-2172 | 6 |  | Part 1 Schema | commercial schema | Executes | Creates no `commercial.compliance_rows` or `commercial.criterion_scores`, although 055, 057, 064, 071 and the UI query the commercial envelope in that shape (P12). |
| 44 | [`044-schema-audit-ledger.sql`](044-schema-audit-ledger.sql) | 2177-2201 | 6 |  | Part 1 Schema | audit.ledger with immutability trigger | Executes | The application role cannot update the ledger (P6). A superuser can disable the trigger, rewrite rows and truncate the table (P7). The draft’s claim that the trigger stops a superuser is false. |
| 45 | [`045-roles-and-grants.sql`](045-roles-and-grants.sql) | 2206-2220 | 6 |  | Part 1 Schema | app_role and sealer_role grants | Executes | Grants `app_role` UPDATE and DELETE on both seal tables. Acting as `app_role`, the probe revoked a seal and rewrote a sealed compliance row without any co-signature (P5). |
| 46 | [`046-auth-policy.py`](046-auth-policy.py) | 2226-2259 | 6 |  | Part 2.1 | app/auth/policy.py | Yes | Policy tables only. |
| 47 | [`047-auth-jwt.py`](047-auth-jwt.py) | 2270-2291 | 6 |  | Part 2.2 | app/auth/jwt.py | Yes, after trivial fixes | `AuthError` is never defined. The issue/verify round trip works (P047). |
| 48 | [`048-auth-deps.py`](048-auth-deps.py) | 2296-2345 | 6 |  | Part 2.3 | app/auth/deps.py | No: incomplete | `settings` and `db` are never defined. The `require_read()` logic is exercised in P055. |
| 49 | [`049-auth-switch.py`](049-auth-switch.py) | 2361-2381 | 6 |  | Part 2.4 | app/auth/switch.py | No: incomplete | Thirteen names are never defined. |
| 50 | [`050-sealing-merkle.py`](050-sealing-merkle.py) | 2387-2455 | 6 |  | Part 3.1 | app/sealing/merkle.py | Yes | Seals sign and verify, and an altered snapshot fails (P050b, P050c). Leaves and nodes are hashed without domain separation, and odd layers duplicate the last node, so `[a,b,c]` and `[a,b,c,c]` share a root (P050a). Only the signed leaf count prevents confusion. |
| 51 | [`051-sealing-routes.py`](051-sealing-routes.py) | 2461-2551 | 6 |  | Part 3.2 | app/sealing/routes.py | No: incomplete | `_flatten_for_merkle()` and `kms` are never defined. The route skips the coverage check the workflow requires before sealing. It runs on the API’s connection, not the separate sealer role set up in 045. |
| 52 | [`052-reject-sealed-writes.sql`](052-reject-sealed-writes.sql) | 2558-2577 | 6 |  | Part 3.3 | technical.reject_sealed_writes() trigger | Executes | Blocks writes after sealing (P3). It is attached only to `technical.compliance_rows`; the comment promises the same trigger on three more tables, which is never written. |
| 53 | [`053-audit-ledger.py`](053-audit-ledger.py) | 2584-2622 | 6 |  | Part 4.1 | app/audit/ledger.py | Yes | Run against PostgreSQL through asyncpg, with three defects. Any entry with a before/after payload fails later verification, because JSONB comes back as text (L2). Two overlapping transactions break the chain (L3). The timestamp is outside the hash, so it can be changed undetected (L4). |
| 54 | [`054-audit-verify.py`](054-audit-verify.py) | 2627-2660 | 6 |  | Part 4.2 | app/audit/verify.py | Yes, after trivial fixes | Needs `GENESIS`, `db` and imports. Reports false tampering in L2 and L3, and misses L4. |
| 55 | [`055-api-matrix.py`](055-api-matrix.py) | 2679-2721 | 6 |  | Part 5.1 | app/api/matrix.py | No: defective | `Depends(require_read('dynamic'))` rejects every role with 403, the auditor included, before the handler runs (P055). |
| 56 | [`056-api-row.py`](056-api-row.py) | 2726-2744 | 6 |  | Part 5.2 | get_row() endpoint | No: incomplete | Returns `ai_evidence` as a JSON string, because asyncpg decodes JSONB as `str`, whereas 060 expects an array. |
| 57 | [`057-api-override.py`](057-api-override.py) | 2749-2788 | 6 |  | Part 5.3 | override_row() endpoint | No: incomplete | The optimistic lock compares `ai_proposed_at`, which no override changes, so two concurrent overrides both succeed. The testing checklist’s 409 claim is false. An empty reason is accepted, despite the checklist’s 400. An acceptance is logged as an override. |
| 58 | [`058-api-unseal.py`](058-api-unseal.py) | 2793-2832 | 6 |  | Part 5.4 | unseal() endpoint, co-signed | No: incomplete | Superseded by 092. The co-signer is recorded only inside free text. |
| 59 | [`059-matrix-page.tsx`](059-matrix-page.tsx) | 2839-3029 | 6 |  | Part 6 | Matrix page (Next.js) | Parses | No Next.js project exists and `@/lib/api` is never written, so it cannot be built. |
| 60 | [`060-row-page.tsx`](060-row-page.tsx) | 3037-3234 | 6 |  | Part 7 | Row page / evidence viewer (Next.js) | Parses | Cannot be built. Expects `ai_evidence` as an array, but 056 returns a string. |
| 61 | [`061-pdf-viewer.tsx`](061-pdf-viewer.tsx) | 3239-3301 | 6 |  | Part 7 | components/PdfViewer.tsx | Parses | Cannot be built. Opens one bundle per bidder and ignores the evidence `doc_id`. Interpretation: the `.min.js` worker path does not match current pdf.js releases, which ship `.mjs` workers. |
| 62 | [`062-override-modal.tsx`](062-override-modal.tsx) | 3309-3418 | 6 |  | Part 8 | components/OverrideModal.tsx | Parses | Cannot be built. Sends acceptances through the override endpoint. |
| 63 | [`063-seal-workflow.txt`](063-seal-workflow.txt) | 3425-3436 | 6 |  | Part 9.1 | Sealing workflow | Not code | Workflow. |
| 64 | [`064-coverage-v1.py`](064-coverage-v1.py) | 3441-3453 | 6 |  | Part 9.1 | coverage() endpoint, first version | No: defective | Same `require_read('dynamic')` dependency as 055: 403 for every role. Superseded by 071. |
| 65 | [`065-seal-chain.txt`](065-seal-chain.txt) | 3473-3474 | 6 |  | Part 9.2 | Seal chain illustration | Not code | Illustration. |
| 66 | [`066-deployment-topology.txt`](066-deployment-topology.txt) | 3491-3494 | 6 |  | Part 10.2 | Deployment topology | Not code | Topology. |
| 67 | [`067-award-function-draft.sql`](067-award-function-draft.sql) | 3616-3629 | 7 | draft | Reasoning | award.read_after_both_sealed(), draft | No: fails | Draft. The placeholder `RETURNS TABLE(...)` is a syntax error. Superseded by 072. |
| 68 | [`068-manifest-draft.txt`](068-manifest-draft.txt) | 3698-3708 | 7 | draft | Reasoning | Export manifest, draft | Not code | Draft manifest. |
| 69 | [`069-lcp-draft.txt`](069-lcp-draft.txt) | 3811-3811 | 7 | draft | Reasoning | Lowest compliant price, draft | Not code | Draft formula. |
| 70 | [`070-reconstruction-draft.txt`](070-reconstruction-draft.txt) | 3910-3911 | 7 | draft | Reasoning | State reconstruction, draft | Not code | Draft pseudo-code. |
| 71 | [`071-api-coverage.py`](071-api-coverage.py) | 3960-3989 | 7 |  | A.1 | app/api/coverage.py | No: incomplete | Queries `commercial.compliance_rows` and `commercial.criterion_scores`, which do not exist (P12). |
| 72 | [`072-award-schema.sql`](072-award-schema.sql) | 3997-4112 | 7 |  | A.2 | award schema, role and SECURITY DEFINER function | Executes | Two logic defects (P4). `gates_passed` is true unless a requirement has category `gate`, which no extractor ever produces, so a bidder that failed a mandatory requirement passes. `evaluated_price` comes from `bq_checks` rows of type `total`, which nothing writes, so every price is NULL and every bidder is ineligible. |
| 73 | [`073-award-formulas.py`](073-award-formulas.py) | 4120-4253 | 7 |  | A.3 | award/formulas.py (LCP, QFM, PQM) | Yes | Ranks identical bids 1 and 2 rather than both 1, so the tie flag in 075 can never fire (P073a, P073b). Unreviewed criteria count as zero (P073c). The QFM formula is labelled ‘Singapore MOF style’, but DeepSeek’s own reasoning says the formula varies, and it cites no source. |
| 74 | [`074-award-config.sql`](074-award-config.sql) | 4258-4264 | 7 |  | A.3 | award.config table | Executes | The prose calls this table `core.award_config`; the SQL creates `award.config`. |
| 75 | [`075-award-service.py`](075-award-service.py) | 4272-4354 | 7 |  | A.4 | award/service.py | No: incomplete | `award.runs` is never created (P13), and `award_role` has no INSERT grant. The report hash is never written into the report. |
| 76 | [`076-award-report.py`](076-award-report.py) | 4360-4428 | 7 |  | A.5 | award/report.py (ReportLab PDF) | Yes | Renders a PDF from a report dictionary. The hash line is blank because `report_hash` is never set. The currency is hard-coded to SGD. |
| 77 | [`077-award-confirm.py`](077-award-confirm.py) | 4436-4465 | 7 |  | A.6 | confirm_award() endpoint | No: incomplete | Sets the tender to `awarded` even when `accepted` is false. Despite the prose, it does not check that the confirming officer differs from the officer who ran the computation. |
| 78 | [`078-audit-checkpoints.sql`](078-audit-checkpoints.sql) | 4488-4502 | 7 |  | B.1 | audit.checkpoints table | Executes |  |
| 79 | [`079-audit-checkpoint.py`](079-audit-checkpoint.py) | 4506-4531 | 7 |  | B.1 | audit/checkpoint.py | No: incomplete | `kms`, `settings`, `db` and imports are missing. |
| 80 | [`080-audit-export.py`](080-audit-export.py) | 4538-4676 | 7 |  | B.2 | audit/export.py (WORM export) | No: defective | `manifest_path` is undefined. `gzip.open()` does not accept `mtime` and raises TypeError. The previous manifest is sought in the wrong directory, so manifests never chain and 082 rejects every multi-day bundle (V4). `audit.exports` is never created (P14). |
| 81 | [`081-manifest-format.json`](081-manifest-format.json) | 4681-4704 | 7 |  | B.3 | Manifest format | Parses |  |
| 82 | [`082-verify-audit.py`](082-verify-audit.py) | 4712-4911 | 7 |  | B.4 | tools/verify_audit.py (offline verifier) | Yes | Run as a command-line tool on synthetic bundles. It passes a consistent bundle (V1) and catches an edited field (V3). It accepts a timestamp moved back 31 days (V2) and a bundle whose latest day is deleted (V5). It checks seal signatures but does not recompute seal Merkle roots from the snapshots. |
| 83 | [`083-verify-audit-transcript.txt`](083-verify-audit-transcript.txt) | 4916-4921 | 7 |  | B.4 | Verifier terminal transcript | Not code | Illustrative output, not a recorded run. |
| 84 | [`084-replay-ledger.py`](084-replay-ledger.py) | 4946-4977 | 7 |  | B.5 | tools/replay_ledger.py | No: defective | Never creates the `audit_witness` schema. `CREATE INDEX IF NOT EXISTS` without an index name is a PostgreSQL syntax error (P11). |
| 85 | [`085-reconstruct-decisions.sql`](085-reconstruct-decisions.sql) | 4982-4993 | 7 |  | B.5 | Reconstruct decisions from ledger | No: fails | `audit_witness.ledger` exists only if 084 works, and 084 does not. |
| 86 | [`086-tampering-playbook.sh`](086-tampering-playbook.sh) | 5001-5016 | 7 |  | B.6 | Tampering playbook commands | No: defective | Shell syntax error at the `<tender-id>` placeholder. Calls `tools/compare_chain_heads.py` and an SQL function `audit.verify_chain()`, neither of which is ever written. |
| 87 | [`087-key-hierarchy.txt`](087-key-hierarchy.txt) | 5359-5373 | 8 |  | A.2 | Key hierarchy diagram | Not code | Diagram. |
| 88 | [`088-seal-signing-flow.txt`](088-seal-signing-flow.txt) | 5400-5413 | 8 |  | A.4 | Seal signing flow | Not code | Workflow. |
| 89 | [`089-sealing-ceremony.py`](089-sealing-ceremony.py) | 5418-5520 | 8 |  | A.4 | app/sealing/ceremony.py | No: defective | `os` is not imported. It signs with ECDSA_SHA_256, while every verifier in the transcript expects Ed25519. It signs a JSON challenge, while 050, 082 and 106 verify a pipe-delimited message, so a seal made this way fails every verifier. |
| 90 | [`090-kms-key-policy.json`](090-kms-key-policy.json) | 5525-5557 | 8 |  | A.4 | AWS KMS key policy | Parses | Not applied to AWS. Interpretation, untested: the MFA condition is unlikely to hold for a service role, and a policy with no administrative statement may trip the KMS lockout safety check. |
| 91 | [`091-unseal-ceremony.py`](091-unseal-ceremony.py) | 5575-5667 | 8 |  | A.5 | app/sealing/unseal_ceremony.py (FROST) | No: defective | Imports `frost_ed25519`, which is not on PyPI (P091), and the class names are invented. `executive_contribute()` returns only round-one commitments, so no signature share is ever produced; FROST signing needs two rounds. |
| 92 | [`092-api-unseal-threshold.py`](092-api-unseal-threshold.py) | 5694-5728 | 8 |  | A.5 | unseal() endpoint, threshold version | No: incomplete | Eight helper functions are never defined. |
| 93 | [`093-seal-key-rotate.py`](093-seal-key-rotate.py) | 5735-5780 | 8 |  | A.6 | app/sealing/rotate.py | No: defective | Writes tender_id `'*'` into a UUID column, which PostgreSQL rejects (P10). `technical.key_transitions` is never created (P15). |
| 94 | [`094-verify-seal-across-rotations.py`](094-verify-seal-across-rotations.py) | 5785-5804 | 8 |  | A.6 | verify_seal_across_rotations() | No: incomplete | Interpretation from reading: it returns True when no transition record exists, so a key the root never authorised passes. |
| 95 | [`095-anchor-rfc3161.py`](095-anchor-rfc3161.py) | 5879-5897 | 8 |  | B.3 | anchor/rfc3161.py | No: defective | `base64` is not imported. rfc3161ng’s `timestamp()` returns bytes, so `tsr.tsa_certs` raises AttributeError. It makes a blocking network call inside an async function. |
| 96 | [`096-anchor-rfc3161-verify.py`](096-anchor-rfc3161-verify.py) | 5902-5916 | 8 |  | B.3 | verify_timestamp() | No: defective | Imports are missing. It checks the message imprint and reads the time, but never verifies the TSA signature or certificate chain, so a forged token would pass. From reading; not executed. |
| 97 | [`097-anchor-rekor.py`](097-anchor-rekor.py) | 5924-5978 | 8 |  | B.4 | anchor/rekor.py | No: defective | The verifier imports `sigstore_rekor_verify`, which is not on PyPI (P097). It reads `proof['log_public_key']`, which the anchoring function never stores. |
| 98 | [`098-anchor-opentimestamps.py`](098-anchor-opentimestamps.py) | 5986-6019 | 8 |  | B.5 | anchor/opentimestamps.py | No: incomplete | Needs the `ots` command-line tool. The opentimestamps-client documentation says verification needs a local Bitcoin Core node, contradicting the claim that verification is offline. |
| 99 | [`099-bundle-layout.txt`](099-bundle-layout.txt) | 6027-6035 | 8 |  | B.6 | Audit bundle layout | Not code | Layout. |
| 100 | [`100-verify-audit-anchors.py`](100-verify-audit-anchors.py) | 6040-6079 | 8 |  | B.6 | tools/verify_audit.py additions (anchors) | No: incomplete | Imports the `anchor.*` modules (095 to 098) and inherits their defects. |
| 101 | [`101-verify-audit-anchors-transcript.txt`](101-verify-audit-anchors-transcript.txt) | 6084-6091 | 8 |  | B.6 | Verifier terminal transcript with anchors | Not code | Illustrative output, not a recorded run. |
| 102 | [`102-runbook-layout.txt`](102-runbook-layout.txt) | 6321-6340 | 9 |  | A.0 | Runbook file layout | Not code | Layout. |
| 103 | [`103-ops-daily-verify-export.sh`](103-ops-daily-verify-export.sh) | 6416-6433 | 9 |  | A.4.1 | ops/daily/01-verify-export.sh | Not run | Shell syntax is valid. Needs an AWS CLI, an S3 bucket and an alert webhook that do not exist. |
| 104 | [`104-ops-daily-verify-chain.sh`](104-ops-daily-verify-chain.sh) | 6438-6450 | 9 |  | A.4.2 | ops/daily/02-verify-chain.sh | No: defective | Calls an SQL function `audit.verify_chain()` that does not exist (P8); `verify_chain` is a Python function in 054. |
| 105 | [`105-ops-log-example.md`](105-ops-log-example.md) | 6469-6478 | 9 |  | A.4.4 | Example daily operations log (fictional) | Not code: fictional record | Invented staff names and tender references. |
| 106 | [`106-ops-weekly-reverify-seals.py`](106-ops-weekly-reverify-seals.py) | 6485-6518 | 9 |  | A.5.1 | ops/weekly/reverify_seals.py | No: incomplete | `_flatten_for_merkle()` and four other names are never defined. Builds SQL with `%` string formatting. |
| 107 | [`107-ops-weekly-anchor-reconcile.sh`](107-ops-weekly-anchor-reconcile.sh) | 6526-6544 | 9 |  | A.5.2 | ops/weekly/02-anchor-reconcile.sh | Not run | Calls `tools/verify_rekor.py`, which is never written. |
| 108 | [`108-ops-monthly-access-review.sql`](108-ops-monthly-access-review.sql) | 6562-6570 | 9 |  | A.6.1 | ops/monthly/access-review.sql | Executes |  |
| 109 | [`109-access-review-attestation-example.md`](109-access-review-attestation-example.md) | 6577-6596 | 9 |  | A.6.1 | Example access review attestation (fictional) | Not code: fictional record | Invented attestation naming invented staff, with a real audit firm cast as auditor. |
| 110 | [`110-sample-seals.py`](110-sample-seals.py) | 6618-6624 | 9 |  | A.6.2 | sample_seals() | No: defective | `signed_at LIKE '2026-04%'` fails on a timestamptz column (P9). Builds SQL with an f-string. |
| 111 | [`111-escalation-chain.txt`](111-escalation-chain.txt) | 6838-6841 | 9 |  | A.9.6 | Escalation chain | Not code | Escalation chain. |
| 112 | [`112-ops-verify-deploy.sh`](112-ops-verify-deploy.sh) | 7054-7086 | 9 |  | A.11.1 | ops/change/verify-deploy.sh | No: defective | Step 1 calls the non-existent `audit.verify_chain()` (P8). Step 3 calls `tools/verify_anchors.py`, which is never written. Step 5 sleeps for an hour inside the deployment script. |
| 113 | [`113-change-log-example.md`](113-change-log-example.md) | 7094-7111 | 9 |  | A.11.2 | Example change log entry (fictional) | Not code: fictional record | Invented change-log entry. |
| 114 | [`114-chain-of-custody-example.md`](114-chain-of-custody-example.md) | 7129-7148 | 9 |  | A.12.2 | Example chain of custody record (fictional) | Not code: fictional record | Invented chain-of-custody record citing an invented register entry (GEBIZ-PK-2026-004). |
| 115 | [`115-build-frost-dkg.sh`](115-build-frost-dkg.sh) | 7280-7286 | 9 |  | B.3 | Build frost-dkg ceremony tool | No: defective | The ZcashFoundation/frost repository has no `frost-dkg` directory and no `v2.0.0` tag; its tags are per crate, such as `frost-core/v2.0.0`. DKG exists only as a library module (`frost-core` `keys::dkg`). |
| 116 | [`116-dkg-pre-ceremony-checklist.txt`](116-dkg-pre-ceremony-checklist.txt) | 7325-7348 | 9 |  | B.4.3 | DKG pre-ceremony checklist | Not code | Checklist. |
| 117 | [`117-dkg-round1.sh`](117-dkg-round1.sh) | 7380-7385 | 9 |  | B.5.2 | frost-dkg round1 | No: defective | The `frost-dkg` command-line tool does not exist (see 115). |
| 118 | [`118-dkg-round1-hash.sh`](118-dkg-round1-hash.sh) | 7394-7394 | 9 |  | B.5.2 | Hash round 1 output | Not run | Standard command; hashes a file the non-existent tool would produce. |
| 119 | [`119-dkg-round1-merge.sh`](119-dkg-round1-merge.sh) | 7405-7407 | 9 |  | B.5.2 | frost-dkg coordinator round1-merge | No: defective | `frost-dkg` does not exist (see 115). |
| 120 | [`120-dkg-round2.sh`](120-dkg-round2.sh) | 7419-7423 | 9 |  | B.5.3 | frost-dkg round2 | No: defective | `frost-dkg` does not exist (see 115). |
| 121 | [`121-dkg-round2-verify.sh`](121-dkg-round2-verify.sh) | 7442-7445 | 9 |  | B.5.3 | frost-dkg round2-verify | No: defective | `frost-dkg` does not exist (see 115). |
| 122 | [`122-dkg-round2-complain.sh`](122-dkg-round2-complain.sh) | 7450-7453 | 9 |  | B.5.3 | frost-dkg round2-complain | No: defective | `frost-dkg` does not exist (see 115). |
| 123 | [`123-dkg-finalize.sh`](123-dkg-finalize.sh) | 7465-7469 | 9 |  | B.5.4 | frost-dkg finalize | No: defective | `frost-dkg` does not exist (see 115). |
| 124 | [`124-dkg-verify-group.sh`](124-dkg-verify-group.sh) | 7486-7488 | 9 |  | B.5.4 | frost-dkg verify-group | No: defective | `frost-dkg` does not exist (see 115). |
| 125 | [`125-dkg-store-share.sh`](125-dkg-store-share.sh) | 7496-7496 | 9 |  | B.5.5 | frost-dkg store-share | No: defective | `frost-dkg` does not exist (see 115). |
| 126 | [`126-dkg-wipe.sh`](126-dkg-wipe.sh) | 7503-7503 | 9 |  | B.5.5 | shred ceremony files | Not run | Standard command; deletes files the non-existent tool would produce. |
| 127 | [`127-dkg-group-key-record.txt`](127-dkg-group-key-record.txt) | 7512-7513 | 9 |  | B.5.5 | Group key record | Not code | Record template. |
| 128 | [`128-frost-ceremony.py`](128-frost-ceremony.py) | 7535-7666 | 9 |  | B.6 | tools/frost_ceremony.py | No: defective | Raises ValueError on import, because dataclass field `round2_hashes` has a mutable default (P128). It also calls the non-existent `frost-dkg` tool. |
| 129 | [`129-dkg-rehearsal-checklist.txt`](129-dkg-rehearsal-checklist.txt) | 7710-7729 | 9 |  | B.9 | DKG rehearsal checklist | Not code | Checklist. |
| 130 | [`130-trust-chain.txt`](130-trust-chain.txt) | 7753-7753 | 9 |  | B.10 | Trust chain | Not code | Diagram. |

## Inline snippets not extracted

A few commands appear inline in the prose rather than as labelled blocks. They are noted here for completeness and were not extracted:

- `\df+ award.read_after_both_sealed` (source line 4114): a psql meta-command.
- `pg_dump --schema=audit > /tmp/incident-<timestamp>.sql` and `aws s3 sync s3://audit-worm-prod/audit/<tender>/ ...` (lines 6742 to 6744): incident-response steps with placeholders.
- `UPDATE core.users SET session_revoked_at=now() WHERE id=<user>` (line 6808): **Fact.** No `session_revoked_at` column exists in `core.users` (fragment 041).
- `sudo shutdown -h now` (line 6928).

## Reproducing the checks

See [`probes/README.md`](probes/README.md).
