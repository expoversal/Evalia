# Proposed architecture

Status: proposal for review, 29 October 2026. No product code exists yet. Claims are labelled **Fact**, **Interpretation** or **Speculation** where the distinction matters. Recommendations are marked as such.

## 1. Purpose and constraints

Evalia helps a client evaluate the tenders it has received, as JTC Corporation's EVA does for JTC. The client may be a public agency, a private owner or developer, or the consultant (quantity surveyor or project manager) who evaluates tenders on the owner's behalf. Evalia reads each submission, maps what it finds against the client's evaluation criteria, and produces a draft evaluation: a compliance matrix, proposed scores with explicit reasoning, and findings the evaluators should examine. Examples include price errors, departures from the contract and claims the supporting documents do not substantiate. The evaluators review the logic rather than reconstruct it, and they decide.

**Fact.** According to the Business Times article on EVA (text supplied by Victor on 29 October 2026), JTC's construction tenders involve about eight evaluators, about 14 man-days each, about 30 documents per tenderer and about 40 tenders a year: some 34,000 man-hours annually. **Fact (computation):** 8 × 14 × 40 = 4,480 man-days, or 33,600 hours at 7.5 hours a day, which is consistent with the article's figure. The same article reports that EVA flagged a tenderer's performance ratings that its supporting documents did not substantiate.

Evalia is software that its users run themselves. Evalia's own staff take no part in any evaluation (decided on 29 October 2026). One engine serves two kinds of user: the evaluating client and, after version one, a bidder checking its own submission for compliance before lodging it. Section 6.4 sets out the profiles and how they are kept apart.

**Market (recorded on 29 October 2026).** Evalia aims at all three kinds of client: public agencies, private owners and developers, and the consultants who evaluate for them. **Interpretation:** large, well-funded agencies such as JTC build their own tools. Agencies in less developed markets (Africa, the Middle East and Central Asia) are less likely to, and they form a niche Evalia should target. The first jurisdiction is the United States; the aim is global.

Constraints that shape the design:

1. **Evaluators decide.** Evalia proposes findings and scores; no finding or score reaches the evaluation report until a named evaluator has accepted or amended it, with a reason recorded for every change.
2. **Traceable.** Every finding cites the document, the page and, where text is relied on, a verbatim quote that the system has verified against the source.
3. **Epistemically labelled.** Every finding states whether it is a **Fact** (a verified quote or a deterministic computation) or an **Interpretation** (a judgement, whether the model's or the evaluator's).
4. **Confidential.** Tender and bid data never enter the repository. They live in the engagement data folder (section 7).
5. **Model-agnostic and residency-aware.** Any model call goes through one gateway that enforces the engagement's data-residency policy ([`03-llm-layer.md`](03-llm-layer.md)).
6. **Industry-neutral core.** Construction knowledge lives in a rubric pack, so that a later pack (for example IT services or facilities management) does not require changes to the engine.

## 2. Design principles

1. **Deterministic before probabilistic.** Arithmetic, presence, dates, thresholds and set differences are code. The model is used only for extraction and judgement under uncertainty.
2. **The model proposes; verification disposes.** Model output is a proposal. It is checked mechanically (schema validity, quote verification, threshold preservation) before an evaluator sees it, and the evaluator decides.
3. **Data first, code second, in packs.** A pack is mostly declarative: taxonomy, criteria, prompts and report template. Code appears only where a check cannot be expressed as data.
4. **Review is a state, not a screen.** Each finding carries a review state. Version one records it in a spreadsheet; a later version may add a user interface over the same data.
5. **Reproducible runs.** Each run writes a record of input hashes, pack version, prompt hashes, model identifiers and output hashes, so that a report can be traced to exactly what produced it.
6. **Fail closed.** A missing residency policy, an unverifiable quote or an invalid model response becomes a visible finding or an error, never a silent default.

## 3. Layered view

```
                 ┌───────────────────────────────────────────────┐
                 │  Local application (v1): browser interface    │
                 │  on the evaluator's machine; ingest · extract │
                 │  · resolve · score · check · review · report  │
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
| Requirement store | Requirements extracted from tender documents, curated by the evaluator | Fields: id, source document, page, clause reference, verbatim source sentence, normalised text, category, mandatory flag, condition, verification type, thresholds. |
| Threshold checker | Confirms that every number, unit and currency in a source sentence survives into the normalised requirement | Deterministic; a hard gate. Fixes the defect found in DeepSeek fragment 021. |
| Retrieval | Finds candidate passages in a submission for a requirement | Version one: section navigation from headings plus BM25 lexical search. Dense embeddings are optional, added only if measurement shows a gain. |
| Resolver | Proposes a status for each requirement and submission, with quotes | Statuses: `met`, `partly_met`, `not_met`, `not_addressed`, `not_applicable`, plus the flag `needs_clarification`. Uses DeepSeek's absence protocol. |
| Quote verifier | Confirms that each quote appears verbatim, after whitespace normalisation, on the cited page | Matches on page and span, not document, which fixes the defect found in fragment 008. A failed quote is removed and the finding flagged. |
| Check framework | Runs deterministic checks supplied by packs and turns their results into findings | A check declares typed inputs (for example "priced BQ rows" or "tender BQ rows"), its parameters and its output. |
| Findings model | One record per observation | Fields include: id, check or requirement, submission, severity, **basis (Fact or Interpretation)**, evidence (document, page, quote, verified flag), computed values, rationale, confidence, provenance (check version, model, prompt hash) and review state. |
| Review | Exports findings to a review workbook and imports the evaluators' decisions | States: `proposed`, `accepted`, `amended`, `rejected`. Amending or rejecting needs a reason. Only `accepted` and `amended` findings reach a report. |
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
| Pre-tender estimate or cost plan (client supplied) | Reference rates and totals | Rate review; single-bid benchmarking |

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
| SUB-01 | Claims substantiated: stated performance ratings, track record, certifications and personnel checked against the supporting documents submitted | Resolver across documents, verified quotes from both the claim and the support | I | ✓ |
| CAP-01 | Key personnel against stated minimums | Extraction plus comparison | F/I | ✓ where the client's criteria require it |
| CAP-02 | Track record against comparability rules | Resolver | I | ✓ where the client's criteria require it |
| FIN-01 | Financial capacity ratios from audited accounts | Extraction plus deterministic ratios | F/I | Later |
| SCR-01 | Proposed scores against the client's criteria, with anchors, reasoning and evidence | Resolver; weighting and totals computed deterministically | I | ✓ |

**Interpretation.** SCR-01 and SUB-01 are what make Evalia comparable with EVA: a scored output whose reasoning the evaluator can check, and the inconsistencies a pressed evaluator misses. BQ-01 to BQ-06, QX-01 and CON-01 add what a construction client also needs: errors and departures that change the contract's price or risk, as facts or quote-backed observations an evaluator can confirm quickly.

### 6.3 Jurisdiction overlays

The core pack uses neutral terms. In particular, it speaks of a *pricing schedule*: a British-style bill of quantities, a US unit-price bid schedule or schedule of values, and a priced activity schedule are all forms of it. Overlays supply local vocabulary, standard forms, clause numbering and registries.

Order of overlays (the first decided on 29 October 2026, the second a recommendation):

1. **United States (version one).** Candidate content, all to be verified against current sources before use: AIA and EJCDC standard forms; federal procurement under the Federal Acquisition Regulation; bid, performance and payment bonds under the Miller Act and its state equivalents; state contractor licensing. **Interpretation:** US public works are often awarded to the lowest responsive and responsible bidder. For those tenders the compliance (responsiveness) review matters more than scoring, which applies to best-value and design-build procurements.
2. **Multilateral development bank tenders (recommended second).** **Interpretation:** many public works tenders in Africa, the Middle East and Central Asia are financed by the World Bank, the African Development Bank, the Asian Development Bank or similar lenders. These use the banks' standard bidding documents, largely built on FIDIC conditions, so one overlay built on them would reach many countries at once. Verify against each bank's current procurement framework.
3. **Others as demand appears:** FIDIC used privately, the United Kingdom (JCT, NEC4), Singapore (PSSCOC, BCA).

Treat every registry and statutory rule as unverified until it has been checked against the issuing body's current publication. **Fact:** the Singapore details in the DeepSeek transcript include at least one doubtful item (section 3 of [`01-designed-vs-built.md`](01-designed-vs-built.md)).

**Interpretation.** Markets beyond the United States raise three further needs:
- submissions in French, Arabic, Russian, Portuguese and other languages;
- data-localisation laws that may require in-country processing, which makes the self-hosted model option more important;
- unreliable connectivity, which favours software that runs locally.

### 6.4 Profiles

The engine and the pack are the same in each profile. What changes is whose criteria apply, what the output is, and who may see what.

- **Evaluator profile (version one).** The client, or its consultant, evaluates several submissions. Output: compliance matrix, proposed scores with reasoning, findings, clarification questions for each bidder, and the price adjustments implied by errors and omissions. Technical evaluation can be completed before price is examined where the client's procedure requires it (section 8).
- **Bidder profile (after version one).** A bidder checks its own draft submission against the tender's published requirements before lodging it. Output: a compliance gap list with references. It does not score.
- **Lender's adviser profile (possible, later).** One selected bid reviewed for price robustness, risk transferred through qualifications, the security package and programme against financing milestones.

**Serving both sides (decided on 29 October 2026).** Evalia may serve evaluating clients and bidders, including on the same tender. It is software that each party runs for itself, and Evalia's staff take part in neither side's work. The controls therefore concern information:

1. **Each engagement is isolated.** No document, extracted text, model cache, calibration setting or worked example passes from one engagement to another.
2. **The bidder profile uses only the published tender documents.** It never uses an evaluating client's interpretations of its criteria, its anchors, its past evaluations or its decisions.
3. **The bidder profile checks compliance and does not score.** Bidders therefore cannot tune their wording to the scoring the evaluator sees.
4. **Evalia's staff have no access to customers' engagement data.** Any support access needs the customer's explicit, logged permission for that engagement.

**Interpretation.** Compliance checks by bidders should help evaluating clients, who then receive fewer bids that must be rejected for avoidable defects.

## 7. Data layout and confidentiality

The engine locates engagement data through the environment variable `EVALIA_DATA_DIR`. On Victor's machine that is `C:\Users\Victor\OneDrive\Evalia-data`. The repository never contains, or hard-codes, this path's contents.

In customer use, the software runs on the customer's own machines or infrastructure, and `EVALIA_DATA_DIR` points to the customer's storage. Victor's OneDrive folder holds development and test material only. Where customers keep their data is their decision.

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
- **Decision (29 October 2026).** OneDrive is accepted for Victor's development and test material. **Interpretation:** OneDrive is a cloud service, so any real tender documents held there for testing still need the owner's consent.
- Tests use synthetic fixtures only, held in the repository under `tests/fixtures/synthetic/` and generated by script, so that they are visibly artificial.

## 8. Evidential integrity, proportionately

An evaluation tool must let the client show how each score was reached and who changed it. It does not need DeepSeek's cryptographic sealing, hash-chained ledger or anchoring apparatus to do so. **Recommendation:**

- For each run, the run record lists the SHA-256 hash of every input and output file, with the engine and pack versions. The report's appendix prints the hash of the run record.
- Every evaluator decision is recorded with the proposed value, the final value, the evaluator, the time and the reason. The record is kept with the engagement and included in the report's appendix.
- Where the client's procedure separates technical from price evaluation, the price documents are not ingested until the evaluators have confirmed the technical evaluation, and the run record shows that sequence. This is a procedural control, not a cryptographic one.

**Interpretation:** this gives a client the traceability its governance requires, at a fraction of the cost and risk. Stronger controls (trusted timestamps, tamper-evident logs) can be added if a public-sector client's rules demand them, and should then be built and tested from first principles, not from the transcript.

## 9. Technology choices

All are recommendations, open to review.

| Concern | Recommendation | Reason | Alternative |
|---|---|---|---|
| Language | Python 3.12 or later | Document-processing ecosystem; matches the transcript's ideas | None preferred |
| Data models | Pydantic v2 | Validation and JSON Schema for structured model output | dataclasses with jsonschema |
| User interface | Local application: a Python service bound to the user's own machine only, with a browser interface, packaged as a Windows and macOS installer | Documents stay on the client's machine; works with poor connectivity; one codebase | A desktop toolkit (for example Qt); a hosted web service (rejected for version one) |
| Command line (developer use) | Typer | Small and typed | argparse |
| PDF text | pdfplumber or pypdfium2 | Permissive licences; character positions available | PyMuPDF (AGPL: needs a licence review); Docling (heavy dependencies; evaluate later for tables) |
| Spreadsheets | openpyxl | Priced BQs often arrive as XLSX | pandas over openpyxl |
| Word output | docxtpl over python-docx | Template-driven DOCX that a non-programmer can edit | Pandoc |
| Lexical search | rank-bm25 or SQLite FTS5 | No server needed | Tantivy |
| Local storage | Files plus SQLite where queries help | Nothing to operate in v1 | DuckDB; PostgreSQL later, for multi-user use |
| Tests | pytest with synthetic fixtures | Standard | — |

Version one has no hosted server, no PostgreSQL and no vector database. The local application's service listens only on the user's own machine.

## 10. What is taken from the DeepSeek design, and what is not

| Taken (re-implemented, not copied) | Not taken |
|---|---|
| Quote verification, matched on page and span | Two-envelope sealing, Merkle seals, envelope-scoped access control |
| Deterministic BQ arithmetic, extended to five checks | Hash-chained audit ledger, checkpoints, write-once export |
| Threshold-preservation gate, written for the first time | Award engine as written (defective, section 5 of the audit). Combining quality and price by the client's own stated formula is a deterministic calculation that may be added later; the award decision stays with the client |
| Status taxonomy and absence protocol (prompt B2) | HSM custody, quorum unseal, FROST key generation |
| Two-pass extraction: cheap screening, then strong structuring, if measurement supports it | RFC 3161, Rekor and Bitcoin anchoring |
| Calibration metrics and synthetic gap injection | Next.js evaluator UI (deferred, not rejected) |
| Fixed context structure across bidders | Operations runbook beyond what a small team needs |

## 11. Questions answered and still open

Answered on 29 October 2026:
- **Clients:** all three kinds, with less developed markets as a niche (section 1).
- **First jurisdiction:** the United States (section 6.3).
- **Client evaluation frameworks** are welcome but not required, so the pack must supply default construction criteria and anchors, which the client confirms or edits before scoring.
- **Delivery model:** Evalia is software operated by its users.

Also answered: evaluators operate version one through a local application; Victor's test material is kept in OneDrive; customers keep their data where they choose; a pre-tender estimate is an optional input.

Still open:
1. Which model providers may each client's documents be sent to? This decides the model profile (see [`03-llm-layer.md`](03-llm-layer.md) and [`04-v1-scope.md`](04-v1-scope.md), section 10).
