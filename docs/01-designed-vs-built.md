# Audit: what was designed and what was built

Audit of [`docs/deepseek-source.md`](deepseek-source.md), carried out on 29 October 2026. Claims are labelled **Fact** (verifiable from the transcript, the repository or a test recorded in [`extracted/INVENTORY.md`](../extracted/INVENTORY.md)), **Interpretation** (a judgement drawn from facts) or **Speculation** (a hypothesis not yet supported).

## 1. Summary

- **Fact.** Nothing was built. Before this audit, the repository held the transcript, a `.gitignore` and a `.gitattributes` file, and no code. The transcript contains no sign that any fragment was ever executed. The conversation ends with the user's message "both" (source line 7787), which has no reply.
- **Fact.** DeepSeek produced 130 code fragments in chat (4,213 lines), all now extracted under [`extracted/`](../extracted/). Of the 49 Python fragments in its final answers, 9 run as written and 33 do not run at all. Of the six fragments that run and do real work, four have defects confirmed by test. All of the schema SQL executes, but its logic contains defects that undermine the properties it was designed to guarantee (section 4).
- **Fact.** By character count, 19% of the transcript covers evaluation itself: rubrics, requirement extraction, compliance resolution and bill of quantities (BQ) checks (turns 3 to 5). Another 78% covers integrity infrastructure, written after the user typed "build all": envelope sealing, audit ledgers, award computation, hardware key custody, blockchain anchoring, an operations runbook and a threshold-key ceremony (turns 6 to 9).
- **Interpretation (revised 29 October 2026).** The transcript's framing, a procuring entity evaluating the bids it has received, matches Evalia's intended role more closely than this audit first assumed: Victor has confirmed that Evalia should work like EVA, helping clients evaluate tenders. What does not fit is the scale of the integrity apparatus. Cryptographic sealing, quorum ceremonies and blockchain anchoring answer the needs of a public body defending awards in litigation, not of a version one supporting three evaluations; a plain decision log and a technical-before-price sequence meet the need proportionately. Meanwhile the parts that carry an evaluation (requirement extraction, compliance resolution with verified quotes, proposed scores, deterministic price checks) are the least developed in code, and the substantiation check that EVA's own reported example relies on is absent (section 6).
- **Interpretation.** The transcript's most useful content is its principles, not its code. Six principles stand out: verify every quoted piece of evidence against the source; keep arithmetic and presence checks out of the model; preserve thresholds verbatim; distinguish "not addressed" from "non-compliant"; force the model to say where it looked before declaring something absent; and measure false negatives on mandatory requirements. Section 5 lists what to keep.

## 2. Conversation structure

| Turn | User message | DeepSeek's response | Source lines | Share of characters |
|---:|---|---|---|---:|
| 1 | "can we download or access Singapore's JTC built its own LLM evaluator?" | Points to the `jtc-client` package on PyPI | 1 to 44 | 1.9% |
| 2 | Clarifies: JTC Corporation's EVA, reported April 2026 | EVA is internal; not available | 45 to 67 | 1.2% |
| 3 | "can you help me to copy or develop a similar system but universal?" | Generic architecture, rubric YAML, scoring pipeline, quote verification | 68 to 431 | 4.2% |
| 4 | "construction" | Construction rubric, compliance matrix, BQ checks, abnormally low tender detection, two-envelope discipline | 432 to 801 | 5.7% |
| 5 | "go" | Requirement extraction and compliance prompts, deduplication, calibration | 802 to 1433 | 9.2% |
| 6 | "build all" | Database schema, role-based access control, sealing, audit ledger, API, React UI | 1434 to 3529 | 22.6% |
| 7 | "continue. all" | Award engine, checkpoints, audit export to write-once storage, offline verifier | 3530 to 5046 | 17.6% |
| 8 | "can you go with both a and b?" | Hardware security module (HSM) key custody, quorum unseal, external anchoring | 5047 to 6217 | 16.2% |
| 9 | "go" | Operations runbook; FROST distributed key generation ceremony | 6218 to 7786 | 21.5% |
| 10 | "both" | No reply | 7787 | 0.0% |

- **Fact.** From turn 4 onwards, the user's inputs total 16 words. Every expansion of scope came from DeepSeek, which closed each answer by offering a deeper layer.
- **Fact.** DeepSeek never asked who would use the system, whether the user evaluates bids as a procuring entity or scrutinises them for someone else, which jurisdiction applies, or what data would be available.
- **Fact.** DeepSeek assumed Singapore's public-sector context throughout: the BCA contractor registry, PSSCOC conditions, GeBIZ, the Quality-Fee Method and CSA cloud tiers.
- **Interpretation.** A one-word prompt answered by ever-deeper offers produced architecture by momentum. Section 7 records the lessons, which [`CLAUDE.md`](../CLAUDE.md) now encodes.

## 3. Reliability of the factual claims in the source

| Claim in transcript | Status |
|---|---|
| `jtc-client` on PyPI is a client for a JTC-built evaluator (turn 1) | **Fact.** The package exists (version 0.1.0). Its own description says it is a client for "Judges That Code" tool services, and it does not mention JTC Corporation or Singapore. **Interpretation:** it is unrelated to EVA, and turn 1 conflated two meanings of "JTC". |
| EVA was reported by The Business Times on 15 April 2026 (user's statement) | **Partly resolved.** Victor supplied the article's text and its URL on 29 October 2026; the URL places it in the newspaper's Design, AI and Tech Awards section. A search found a DPEX Network repost that the search summary dates to 7 April 2026, and DeepSeek's own search result (source line 52) carries the title with "DAITA 2026". The publication date is still not settled; the article could not be fetched from this session. |
| EVA workload figures and capabilities | **Fact (as reported).** The article text states about eight evaluators per construction tender, about 14 man-days each, some 30 documents per tenderer, about 40 tenders a year and about 34,000 man-hours a year; that EVA extracts details and performs initial scoring against JTC's criteria, with its reasoning explicit; that it flagged performance ratings the supporting documents did not substantiate; and that evaluators keep full authority. These are the article's claims, not independently verified. **Fact (computation):** 8 × 14 × 40 = 4,480 man-days, or 33,600 hours at 7.5 hours a day, consistent with the article's total. |
| EVA was co-created with project, contract and procurement staff, and is designed to transfer to consultancy and IT tenders (turn 2) | **Unverified.** These claims reach us only through DeepSeek's paraphrase of an article it read. |
| BCA CW01 grades run "A1 to C2" (source line 474) | **Unverified.** The auditor's recollection is that the CW01 range extends to C3. Check against BCA's current Contractors Registration System schedule before use. |
| Quality-Fee Method is "Singapore MOF style" with fee score 100 × lowest/bidder and 70/30 weights (fragment 073) | **Unsupported.** DeepSeek's reasoning (source line 3817 onwards) says that "the exact formula varies" and that it chose one; no source is cited. |
| An offline verifier needs nothing but the bundle and a public key (turns 7 and 8) | **False for the OpenTimestamps layer.** The opentimestamps-client documentation says verification needs a local Bitcoin Core node. |
| FROST tooling: `frost-ed25519` Python library, `frost-dkg` command-line tool, tag `v2.0.0` (turns 8 and 9) | **False.** No such Python package exists on PyPI. The ZcashFoundation/frost repository has no `frost-dkg` tool and tags its releases per crate (for example `frost-core/v2.0.0`). Distributed key generation exists only as a Rust library module. |
| Operations log, access attestation, change log, chain of custody (fragments 105, 109, 113, 114) | **Fiction.** These are invented examples with invented names and identifiers; one casts a real audit firm as auditor. They must never be treated as evidence. |

## 4. Designed against built, by component

"Built" means present in this repository as working code. **Fact.** No component is built. The "Code in transcript" column shows how far DeepSeek went; the "Test result" column shows whether that code works.

| Component | Where designed | Code in transcript | Test result | Relevant to Evalia v1? |
|---|---|---|---|---|
| Rubric as data (generic and construction) | Turn 3 §3; turn 4 §2 | YAML 005, 011 | Parses; no loader, validator or rule evaluator exists | Yes, redesigned as a pack (see `02-architecture.md`) |
| Document ingestion (PDF, DOCX, XLSX, OCR) | Turn 3 §2; turn 4 §1 | None beyond 017 | 017 calls Docling methods that do not exist | Yes |
| Clause-aware chunking | Turn 5 A.1 | 016, 017 | Defective (invented API) | Yes |
| Requirement extraction, two passes | Turn 5 A.2 | Prompts 019, 020; stub 012 | Prompts only. Filling them with `str.format()`, as 007 does, raises KeyError | Yes |
| Requirement deduplication | Turn 5 A.3 | 021 | Merges requirements that differ only in threshold (S$10m with S$1m) | Yes, redesigned |
| Threshold-preservation gate ("build before anything else") | Turn 5 A.5 | None | Never written | Yes |
| Bid indexing (sections, dense, BM25, clause echo, table of contents) | Turn 5 B.2 | 022 | Incomplete | Partly |
| Navigate-then-extract compliance resolver | Turn 5 B.3 | Prompts 023, 024 | Prompts only | Yes |
| Quote verification | Turn 3 §4; turn 5 B.4 | 008, 025 | 008 rejects genuine quotes when a document spans several chunks; 025 is incompatible with the model in 013 | Yes, redesigned |
| Criterion scoring with anchors | Turn 3 §4; turn 4 §2 | 007, 009 | Incomplete; 009 crashes when a score is absent | Yes, redesigned (SCR-01) |
| BQ arithmetic checks | Turn 4 §4 | 014 | Extension errors only; the other four checks claimed are not implemented | Yes |
| Abnormally low rate detection | Turn 4 §5 | 015 | Runs; silent with fewer than four bids | Yes, with a reference-estimate mode |
| Programme credibility | Turn 4 §6 | None | Never written | Yes, narrow |
| Calibration harness, synthetic gap injection | Turn 3 §7; turn 4 §8; turn 5 B.7 | 026 (data class only) | Metrics never computed | Yes |
| Evaluator UI (matrix, evidence viewer, override) | Turn 6 Parts 6 to 8 | TSX 059 to 062 | Parses; cannot be built | No (v1 uses a review spreadsheet) |
| API (matrix, row, override, coverage) | Turn 6 Part 5; turn 7 A.1 | 055 to 058, 064, 071 | Matrix and first coverage endpoints refuse every role; commercial tables missing | No |
| Role-based access and envelope scoping | Turn 6 Part 2 | 046 to 049 | Policy runs; dependencies incomplete | No |
| Two-envelope schema | Turn 6 Part 1 | 041 to 045 | Executes; the application role can revoke seals unaided | No |
| Sealing (Merkle tree, Ed25519) | Turn 6 Part 3 | 050 to 052 | Core runs; route incomplete; trigger covers one table of four | No |
| Hash-chained audit ledger | Turn 6 Part 4 | 044, 053, 054 | Three defects confirmed on PostgreSQL (L2, L3, L4) | No; v1 keeps a decision log and run record |
| Award engine (lowest compliant price, QFM, price-quality) | Turn 7 A.2 to A.6 | 072 to 077 | Gate and price logic broken; ties mis-ranked; rejection still marks the tender awarded | No (the client decides the award; its price-quality formula may be computed later) |
| Checkpoints, write-once export, offline verifier, replay | Turn 7 B | 078 to 086 | Export defective; verifier misses timestamp edits and truncation; replay has a syntax error | No |
| HSM custody, signing ceremony, KMS policy | Turn 8 A.1 to A.4 | 088 to 090 | Signature scheme inconsistent with every verifier | No |
| Quorum unseal (FROST) | Turn 8 A.5 | 091, 092 | Library does not exist; protocol omits round two | No |
| Seal-key rotation | Turn 8 A.6 | 093, 094 | Defective | No |
| External anchoring (RFC 3161, Rekor, OpenTimestamps) | Turn 8 B | 095 to 101 | None works as written; the TSA signature is never verified | No |
| Operations runbook | Turn 9 A | 102 to 114 | Scripts call functions and tools never written; example records fictional | No |
| FROST distributed key generation ceremony | Turn 9 B | 115 to 129 | The tool does not exist | No |
| Model abstraction (LiteLLM mentioned) | Turn 3 | None; 007 hard-codes one model | Never written | Yes (see `03-llm-layer.md`) |
| Draft evaluation for the client's panel | Not designed | Only the award PDF (076) | Not applicable | Yes, the v1 deliverable |
| Substantiation check (claims against supporting documents) | Not designed | None | Not applicable | Yes (SUB-01) |

## 5. Defects with the greatest consequence

Ranked by the damage each would do if the code were adopted. Each is a **Fact** established by the probe cited.

1. **The audit chain reports tampering where there is none.** Every ledger entry that carries a before/after payload fails verification after a round trip through PostgreSQL, because asyncpg returns JSONB as text (L2). Overrides, the events auditors care about most, are exactly the entries that carry payloads. Two overlapping transactions also break the chain (L3).
2. **Timestamps are not protected.** Neither the ledger hash nor the export Merkle root covers the timestamp. A superuser moved an entry back 31 days and both verifiers still passed (L4, V2). This defeats the transcript's central claim, that "technical scores were fixed before anyone saw prices" can be proved.
3. **One application credential can unseal.** Fragment 045 grants the application role UPDATE on the seal tables. Acting as that role, the probe revoked a seal and rewrote a sealed compliance row without any co-signature (P5). The two-person unseal, quorum ceremony and HSM custody are all bypassed by one SQL statement.
4. **The award function cannot produce a lawful result.** A bidder that failed a mandatory requirement still passes the gate check, and every bidder's price is NULL, so every bidder is ineligible (P4). Identical bids are ranked 1 and 2 instead of tied (P073a).
5. **Deduplication destroys thresholds.** Requirements that differ only in amount are merged (P021b). The transcript itself calls threshold preservation the one gate that must reach 100%.
6. **Quote verification rejects genuine evidence.** When a document spans several retrieved chunks, only the last chunk is checked (P008c). In practice that is most cases, so verified evidence would be discarded and confidence lowered at random.
7. **The core review screen is unreachable.** The matrix endpoint refuses every role, the auditor included (P055).
8. **The export never chains, and the verifier rejects its output.** Fragment 080 crashes before writing (`manifest_path` is undefined, and `gzip.open` rejects `mtime`). Once those are fixed, it still writes manifests that 082 rejects from the second day onwards (V4).
9. **The seal ceremony and the verifiers disagree on the signature scheme.** The production signing path uses ECDSA over a JSON challenge, while every verifier expects Ed25519 over a pipe-delimited string (089).
10. **The anchoring layer verifies nothing.** The RFC 3161 check never verifies the timestamp authority's signature (096). The Rekor check depends on a package that does not exist (097). OpenTimestamps verification needs a Bitcoin node (098).

**Interpretation.** These are not cosmetic faults. Defects 1 to 3 invert the purpose of the integrity layer: it would raise false alarms on honest activity while missing deliberate backdating and unaided unsealing. Code of this kind must not be reused without independent re-derivation and adversarial testing. [`CLAUDE.md`](../CLAUDE.md) makes that a rule.

## 6. What to keep, and what is missing for Evalia

### Worth keeping (Interpretation)

| Idea | Source | Why it survives |
|---|---|---|
| Every quote must be found verbatim in the cited source, or it is dropped and the finding flagged | Turn 3 §4; turn 5 B.4 | It is cheap and model-independent, and it stops the commonest failure: invented citations. It must be re-implemented to match page and span, not document. |
| Arithmetic, presence and date checks are deterministic code, never model output | Turn 4 §1, §4 | It protects against confident wrong numbers. |
| Thresholds preserved verbatim, with a hard gate | Turn 5 A.5 | It prevents comparing against the wrong amount. It needs real code, which the transcript never wrote. |
| Status taxonomy that separates `not_addressed` from `non_compliant`, plus `needs_clarification` | Turn 5 B.3 | The statuses carry different consequences for the reader. |
| Absence protocol: before declaring something absent, state what was reviewed and where | Prompt B2 (fragment 024) | It makes false negatives visible to the human reviewer. |
| Rubric anchors at fixed score points instead of free-text guidance | Turn 4 §2 | It improves consistency and makes calibration possible. |
| Calibration metrics led by the false-negative rate on mandatory requirements, with synthetic gap injection | Turn 5 B.7 | It measures the costly error directly. |
| Failure-mode catalogue | Turn 5, end of B.7 | It is a useful onboarding checklist. |
| Fixed context structure for every bidder on a given requirement | Turn 5 B.5 | It makes results comparable across bidders. |

### Discarded for Evalia (Interpretation)

The following are set aside: two-envelope cryptographic sealing, role-based envelope scoping, the award engine as written, HSM custody, quorum unseal, threshold key generation, blockchain and transparency-log anchoring, write-once audit export and most of the runbook. **Interpretation:** these exceed what three supported evaluations need, and the code for them is defective. What remains of the underlying need (show who changed which score and why; keep price unseen until the technical evaluation is confirmed, where the client requires it) is met by a decision log, a run record and a procedural sequence. See [`02-architecture.md`](02-architecture.md), section 8.

### Missing from the transcript but valuable to evaluators (Interpretation)

The transcript evaluates bids for compliance and merit. An evaluation panel also needs to know whether claims are supported, and what a bid changes, hides or under-prices. None of the following is designed:

- **Substantiation.** Claims in a submission (performance ratings, track record, certifications) checked against its supporting documents. This is the example EVA's own coverage gives of what the tool catches.

- **Qualifications, exclusions, assumptions and departures.** A register of every point where a bidder alters scope, risk or the conditions of contract: caps on liquidated damages, time bars, payment terms, design responsibility, ground risk.
- **Security package.** Bonds, parent-company guarantees and insurances, compared with the requirements.
- **Rate loading and front-loading.** Early-activity rates inflated against later ones, which matters to the client's cash flow.
- **Provisional and prime-cost sums.** Their share of the price, and whether a bidder has altered them.
- **Rate review with few bids.** Peer-based outlier tests need at least four bids (fragment 015); with fewer, rates must be compared with the client's pre-tender estimate.
- **Programme against contract dates.** Completion and sectional dates, float, and consistency with the method statement and resources.
- **Draft evaluation for the panel.** A document the panel can review, with each finding and proposed score labelled as fact or interpretation and tied to a page. The transcript's only report is an award table (076).

## 7. Lessons for how Evalia is built

- **Fact.** From turn 4 onwards, scope grew on 16 words of user input, and no scoping question was asked. **Rule adopted:** confirm the purpose, the user and the out-of-scope list before designing, and keep [`04-v1-scope.md`](04-v1-scope.md) authoritative.
- **Fact.** Code was presented as "real, compilable" without having been run. **Rule adopted:** no claim that code works unless it has been executed, with the command and result recorded.
- **Fact.** Invented library APIs (Docling, FROST, Rekor) were presented as real. **Rule adopted:** before code relies on a third-party API, verify it against the installed package or its source.
- **Fact.** Fictional example records were formatted exactly like real ones. **Rule adopted:** examples are visibly marked as fictional, and the repository never contains realistic-looking records.

These rules are in [`CLAUDE.md`](../CLAUDE.md).
