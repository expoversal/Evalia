# Proposed architecture

Status: proposal for review, 29 October 2026. No product code exists yet. Claims are labelled **Fact**, **Interpretation** or **Speculation** where the distinction matters. Recommendations are marked as such.

## 1. Purpose and constraints

Evalia scrutinises construction bids on behalf of a party outside the procurement: the owner who will sign the contract, or the lender who will fund it. It does not award contracts. It produces a scrutiny report that tells its reader, with page references, what each bid complies with, what it fails, what it changes, and where its price or programme needs questioning.

Constraints that shape the design:

1. **Advisory output, human-reviewed.** No finding reaches a report until a named analyst has accepted or amended it.
2. **Traceable.** Every finding cites the document, the page and, where text is relied on, a verbatim quote that the system has verified against the source.
3. **Epistemically labelled.** Every finding states whether it is a **Fact** (a verified quote or a deterministic computation) or an **Interpretation** (a judgement, whether the model's or the analyst's).
4. **Confidential.** Tender and bid data never enter the repository. They live in the engagement data folder (section 7).
5. **Model-agnostic and residency-aware.** Any model call goes through one gateway that enforces the engagement's data-residency policy ([`03-llm-layer.md`](03-llm-layer.md)).
6. **Industry-neutral core.** Construction knowledge lives in a rubric pack, so that a later pack (for example IT services or facilities management) does not require changes to the engine.

## 2. Design principles

1. **Deterministic before probabilistic.** Arithmetic, presence, dates, thresholds and set differences are code. The model is used only for extraction and judgement under uncertainty.
2. **The model proposes; verification disposes.** Model output is a proposal. It is checked mechanically (schema validity, quote verification, threshold preservation) before an analyst sees it, and the analyst decides.
3. **Data first, code second, in packs.** A pack is mostly declarative: taxonomy, criteria, prompts and report template. Code appears only where a check cannot be expressed as data.
4. **Review is a state, not a screen.** Each finding carries a review state. Version one records it in a spreadsheet; a later version may add a user interface over the same data.
5. **Reproducible runs.** Each run writes a record of input hashes, pack version, prompt hashes, model identifiers and output hashes, so that a report can be traced to exactly what produced it.
6. **Fail closed.** A missing residency policy, an unverifiable quote or an invalid model response becomes a visible finding or an error, never a silent default.

## 3. Layered view

```
                 ┌───────────────────────────────────────────────┐
                 │  Command-line interface (v1)                  │
                 │  ingest · extract · resolve · check · review  │
                 │  · report                                     │
                 └───────────────────────┬───────────────────────┘
                                         │
   ┌──────────────────────────┐   ┌──────▼─────────────────────────────┐
   │  Rubric packs            │   │  Engine (industry-neutral)         │
   │  packs/construction/     │──▶│  case model · ingestion ·          │
   │   taxonomy, criteria,    │   │  provenance · requirements ·       │
   │   checks, prompts,       │   │  retrieval · resolver · check      │
   │   report template,       │   │  framework · findings · review ·   │
   │   jurisdiction overlays  │   │  report composer · run record      │
   └──────────────────────────┘   └──────┬───────────────┬─────────────┘
         packs depend on the engine;     │               │
         the engine never imports a pack │               │
                                  ┌──────▼──────┐  ┌─────▼────────────────┐
                                  │ LLM gateway │  │ Engagement data      │
                                  │ (residency  │  │ folder               │
                                  │  enforced)  │  │ EVALIA_DATA_DIR      │
                                  └─────────────┘  │ (outside the repo)   │
                                                   └──────────────────────┘
```

## 4. Engine components

Each component is industry-neutral. Construction terms such as "bill of quantities" or "liquidated damages" do not appear in the engine; they arrive from the pack as document types, categories and check parameters.

| Component | Responsibility | Notes |
|---|---|---|
| Case model | Engagement → package (one tender's documents) → submissions (one per bidder) → documents → pages and spans | Every document is identified by its SHA-256 hash, not its file name. |
| Ingestion | Converts PDF (text layer), XLSX and DOCX into page text with character offsets, plus tables as rows | Adapter interface; OCR is a later adapter. A page that yields no text is reported, not skipped. |
| Document register | Maps each file to a document type from the pack's taxonomy | Version one: a hand-edited `register.yaml` per engagement. Automatic classification is deferred. |
| Requirement store | Requirements extracted from tender documents, curated by the analyst | Fields: id, source document, page, clause reference, verbatim source sentence, normalised text, category, mandatory flag, condition, verification type, thresholds. |
| Threshold checker | Confirms that every number, unit and currency in a source sentence survives into the normalised requirement | Deterministic; a hard gate. Fixes the defect found in DeepSeek fragment 021. |
| Retrieval | Finds candidate passages in a submission for a requirement | Version one: section navigation from headings plus BM25 lexical search. Dense embeddings are optional, added only if measurement shows a gain. |
| Resolver | Proposes a status for each requirement and submission, with quotes | Statuses: `met`, `partly_met`, `not_met`, `not_addressed`, `not_applicable`, plus the flag `needs_clarification`. Uses DeepSeek's absence protocol. |
| Quote verifier | Confirms that each quote appears verbatim, after whitespace normalisation, on the cited page | Matches on page and span, not document, which fixes the defect found in fragment 008. A failed quote is removed and the finding flagged. |
| Check framework | Runs deterministic checks supplied by packs and turns their results into findings | A check declares typed inputs (for example "priced BQ rows" or "tender BQ rows"), its parameters and its output. |
| Findings model | One record per observation | Fields include: id, check or requirement, submission, severity, **basis (Fact or Interpretation)**, evidence (document, page, quote, verified flag), computed values, rationale, confidence, provenance (check version, model, prompt hash) and review state. |
| Review | Exports findings to a review workbook and imports the analyst's decisions | States: `proposed`, `accepted`, `amended`, `rejected`. Amending or rejecting needs a reason. Only `accepted` and `amended` findings reach a report. |
| Report composer | Builds a report model from reviewed findings and renders it through the pack's template | DOCX for the reader, Markdown for diffing. Includes methodology, limitations and a disclosure that AI was used. |
| Run record | Writes a JSON manifest for each run | Input hashes, pack version, engine version, model profile, prompt and schema hashes, output hashes, timings and cost. Stored in the data folder. |

## 5. The pack contract

A pack is a directory with a manifest. Illustrative layout:

```
packs/construction/
  pack.yaml                 name, version, engine compatibility, overlays
  taxonomy/documents.yaml   document types and the evidence each can supply
  taxonomy/categories.yaml  requirement categories
  criteria/*.yaml           criteria with anchors (for later scoring)
  checks/                   check definitions (YAML) and their code (Python)
  prompts/*.md.j2           extraction and resolution prompts
  templates/report.docx     report template
  overlays/sg.yaml, uk.yaml, fidic.yaml
  glossary.yaml
```

Rules for packs:

- **Recommendation.** Prompts use Jinja2 with strict undefined variables, not `str.format()`. **Fact:** every DeepSeek prompt breaks under `str.format()` because its JSON examples contain unescaped braces (probes P019 to P024).
- Every check declares whether its output basis is **Fact** (deterministic) or **Interpretation** (model or rule-of-thumb judgement). The engine refuses a check that does not declare it.
- Packs are versioned with semantic versioning. A report records the pack version and the overlays used.
- Packs import the engine's public API only. The engine never imports a pack. **Recommendation:** enforce this with an import-boundary test once code exists.

## 6. The construction rubric pack, version 0

### 6.1 Document taxonomy

| Document type | Typical content | Used by |
|---|---|---|
| Instructions to tenderers | Submission requirements, evaluation basis | Requirement extraction |
| Conditions of contract and amendments | Risk allocation, liquidated damages, payment, time bars, security | Departures check |
| Specification and employer's requirements | Technical obligations | Requirement extraction |
| Tender BQ or pricing schedule | Items, quantities, units, provisional sums | BQ checks (reference) |
| Form of tender | Price, validity, signature | Completeness checks |
| Priced BQ | Bidder's rates and amounts | BQ checks |
| Tender qualifications and clarifications letter | Exclusions, assumptions, departures | Qualifications register |
| Programme | Durations, milestones, logic | Programme checks |
| Method statement | Sequence, temporary works, site constraints | Programme consistency, compliance |
| Organisation chart and CVs | Key personnel | Capability checks |
| Track record | Comparable projects | Capability checks |
| Financial statements | Turnover, equity, liquidity | Financial capacity |
| Securities and insurances | Bonds, guarantees, policies | Security package check |
| Engineer's estimate or cost plan (owner or lender supplied) | Reference rates and totals | Single-bid benchmarking |

### 6.2 Check catalogue

"v1" marks the checks proposed for version one (see [`04-v1-scope.md`](04-v1-scope.md)). Basis: **F** = Fact (deterministic), **I** = Interpretation.

| ID | Check | Method | Basis | v1 |
|---|---|---|---|---|
| BQ-01 | Extension errors (quantity × rate ≠ amount) | Deterministic | F | ✓ |
| BQ-02 | Page, section and summary totals carried forward correctly; collection pages agree with the form of tender | Deterministic | F | ✓ |
| BQ-03 | Items omitted, added or renumbered against the tender BQ | Deterministic set difference | F | ✓ |
| BQ-04 | Quantities or units altered against the tender BQ | Deterministic | F | ✓ |
| BQ-05 | Provisional sums, prime-cost sums and contingencies altered, and their share of the price | Deterministic | F | ✓ |
| BQ-06 | Items left blank, at zero, or marked "included" | Deterministic, with model help where descriptions are free text | F | ✓ |
| BQ-07 | Rate outliers against peers (four or more bids) or against a reference estimate | Statistical | I | ✓ |
| BQ-08 | Front-loading: early-activity rates against peers or the reference | Statistical | I | Later |
| CMP-01 | Mandatory submission requirements met (documents, signatures, validity) | Deterministic presence plus resolver | F/I | ✓ |
| CMP-02 | Technical requirements addressed | Resolver with verified quotes | I | ✓ (scope limited per engagement) |
| QX-01 | Register of qualifications, exclusions, assumptions and departures | Model extraction, verified quotes | F (quote) / I (effect) | ✓ |
| CON-01 | Departures from the conditions of contract: liquidated damages and their cap, retention, payment terms, time bars, design responsibility | Resolver against the contract's key terms | I | ✓ |
| SEC-01 | Bonds, guarantees and insurances against the requirements | Extraction plus deterministic comparison | F/I | ✓ |
| PRG-01 | Programme completion and sectional dates against the contract dates | Extraction plus deterministic comparison | F | ✓ |
| PRG-02 | Programme consistent with the method statement and named resources | Resolver | I | Later |
| CAP-01 | Key personnel against stated minimums | Extraction plus comparison | F/I | Later |
| CAP-02 | Track record against comparability rules | Resolver | I | Later |
| FIN-01 | Financial capacity ratios from audited accounts | Extraction plus deterministic ratios | F/I | Later |
| SCR-01 | Criterion scoring with anchors | Resolver | I | Later (scrutiny reports need not score) |

**Interpretation.** Owners and lenders gain most from BQ-01 to BQ-06, QX-01 and CON-01. Errors and departures change the contract's price or risk, and their findings are either facts or quote-backed observations that an analyst can confirm quickly.

### 6.3 Jurisdiction overlays

The core pack uses neutral terms. Overlays supply local vocabulary, clause numbering and registries: Singapore (PSSCOC, BCA workheads and grades), United Kingdom (JCT, NEC4), international (FIDIC), United States (AIA A201, bonding). **Recommendation:** build only the overlay that matches the discovery-test packages, and treat every registry rule as unverified until it has been checked against the issuing body's current publication. **Fact:** the Singapore details in the DeepSeek transcript include at least one doubtful item (section 3 of [`01-designed-vs-built.md`](01-designed-vs-built.md)).

### 6.4 Audience profiles

Both audiences get the same checks with a different emphasis in the report:

- **Owner profile.** Bid-by-bid comparison, a list of clarification questions for each bidder, and the price adjustments implied by errors and omissions.
- **Lender profile.** One bid, often after selection: robustness of the price against the budget or reference estimate, risk transferred back to the employer through qualifications and departures, adequacy of the security package, and programme against financing milestones.

## 7. Data layout and confidentiality

The engine locates engagement data through the environment variable `EVALIA_DATA_DIR`. On Victor's machine that is `C:\Users\Victor\OneDrive\Evalia-data`. The repository never contains, or hard-codes, this path's contents.

```
%EVALIA_DATA_DIR%\
  engagements\
    <engagement-id>\
      engagement.yaml        audience, jurisdiction, residency policy, model profile
      inputs\                original files, untouched
      register.yaml          file → document type, bidder
      work\                  extracted text, tables, indexes
      llm-cache\             requests and responses (contain tender text)
      review\                review workbooks
      reports\               DOCX and Markdown reports
      runs\                  run records
```

- **Fact.** Model caches, review workbooks and run records contain tender text or bidder names, so they belong in the data folder, not the repository.
- **Interpretation.** OneDrive is itself a cloud service. Whether storing a client's bids there meets the client's confidentiality terms is a question for each engagement, and `engagement.yaml` should record the answer.
- Tests use synthetic fixtures only, held in the repository under `tests/fixtures/synthetic/` and generated by script, so that they are visibly artificial.

## 8. Evidential integrity, proportionately

Evalia does not need DeepSeek's sealing, ledger or anchoring apparatus. **Recommendation:** for each report, the run record lists the SHA-256 hash of every input file and every output file, together with the engine and pack versions. The report's appendix prints the hash of the run record. That lets an engagement later show which documents a report was based on. Trusted timestamping can be added if a customer asks for it. **Interpretation:** this meets a scrutiny tool's need for traceability, at a fraction of the cost and risk.

## 9. Technology choices

All are recommendations, open to review.

| Concern | Recommendation | Reason | Alternative |
|---|---|---|---|
| Language | Python 3.12 or later | Document-processing ecosystem; matches the transcript's ideas | None preferred |
| Data models | Pydantic v2 | Validation and JSON Schema for structured model output | dataclasses with jsonschema |
| Command line | Typer | Small and typed | argparse |
| PDF text | pdfplumber or pypdfium2 | Permissive licences; character positions available | PyMuPDF (AGPL: needs a licence review); Docling (heavy dependencies; evaluate later for tables) |
| Spreadsheets | openpyxl | Priced BQs often arrive as XLSX | pandas over openpyxl |
| Word output | docxtpl over python-docx | Template-driven DOCX that a non-programmer can edit | Pandoc |
| Lexical search | rank-bm25 or SQLite FTS5 | No server needed | Tantivy |
| Local storage | Files plus SQLite where queries help | Nothing to operate in v1 | DuckDB; PostgreSQL later, for multi-user use |
| Tests | pytest with synthetic fixtures | Standard | — |

Version one has no web server, no PostgreSQL and no vector database.

## 10. What is taken from the DeepSeek design, and what is not

| Taken (re-implemented, not copied) | Not taken |
|---|---|
| Quote verification, matched on page and span | Two-envelope sealing, Merkle seals, envelope-scoped access control |
| Deterministic BQ arithmetic, extended to five checks | Hash-chained audit ledger, checkpoints, write-once export |
| Threshold-preservation gate, written for the first time | Award engine (LCP, QFM, PQM) |
| Status taxonomy and absence protocol (prompt B2) | HSM custody, quorum unseal, FROST key generation |
| Two-pass extraction: cheap screening, then strong structuring, if measurement supports it | RFC 3161, Rekor and Bitcoin anchoring |
| Calibration metrics and synthetic gap injection | Next.js evaluator UI (deferred, not rejected) |
| Fixed context structure across bidders | Operations runbook beyond what a small team needs |

## 11. Open questions

1. Will the discovery-test packages be owner cases (several bids), lender cases (one bid) or both? This decides whether BQ-07 needs the reference-estimate mode in v1.
2. Which jurisdiction do the packages come from? This decides the single overlay to build.
3. Will reference estimates be available? Without them, single-bid price scrutiny is limited to arithmetic and qualifications.
4. Does any discovery client restrict which model providers may see its data? This decides the model profile for v1 (see [`03-llm-layer.md`](03-llm-layer.md)).
5. Is OneDrive acceptable storage under the discovery clients' confidentiality terms?
