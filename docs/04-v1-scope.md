# Version one scope: three supported tender evaluations for the discovery test

Status: proposal for review, revised 29 October 2026 after Victor's decisions (section 9). Once approved, this document is authoritative. Anything not listed under "In scope" is out of scope until Victor approves a change, and approved changes are recorded in section 11.

## 1. Objective

Support **three real construction tender evaluations**, carried out by the clients' own evaluators using Evalia as software. For each, Evalia produces a draft evaluation that the evaluators review and finalise. The test examines one proposition:

> A draft evaluation that maps each submission against the client's criteria, with proposed scores whose reasoning and evidence are explicit, lets evaluators finish faster and catch issues they would otherwise miss.

**Fact.** The Business Times article on EVA (text supplied by Victor on 29 October 2026) locates EVA's value in two places:
- workload: about 34,000 man-hours a year across JTC's construction tenders;
- catching inconsistencies: for example, performance ratings that the supporting documents did not substantiate.

**Interpretation:** the discovery test should therefore measure both, against the client's usual process.

The client is responsible for the evaluation. Evalia proposes; the client's evaluators decide and own the result. Nobody from Evalia takes part.

Version one is the smallest system that clients' evaluators can operate themselves to complete those three evaluations. It is not a general product release.

## 2. What the draft evaluation contains

One draft evaluation per tender, covering every submission received:

1. **Summary for the evaluation panel.** Proposed ranking on quality, the five to ten most consequential findings, and open clarification questions.
2. **Compliance matrix.** Each mandatory and technical requirement against each submission: status, verified quotes with page references, and gaps. **Interpretation:** for US public works awarded to the lowest responsive and responsible bidder, this matrix is the evaluation.
3. **Proposed scores**, where the procurement uses scoring. For each criterion and each submission:
   - a proposed score against defined anchors, with reasoning and evidence;
   - the criteria are the client's own if supplied, otherwise the pack's defaults as confirmed by the client;
   - weighted totals are computed deterministically.
4. **Substantiation.** Claims in a submission (performance ratings, track record, certifications, key personnel) checked against the supporting documents submitted with it.
5. **Price integrity.** Errors and alterations in the pricing schedule, and their combined price effect, presented separately where the client evaluates price after quality:
   - arithmetic errors;
   - omitted or altered items;
   - changes to allowances and provisional sums;
   - zero-rated and "included" items.
6. **Qualifications and departures.** Every exclusion, assumption, qualification and departure from the conditions of contract, quoted and cited.
7. **Bonding, insurance and programme.** Bid, performance and payment bonds and insurances against the requirements; completion and milestone dates against the contract.
8. **Rate review.** Two modes, each labelled in the draft: against the other submissions, when there are four or more; and against the client's pre-tender estimate, when the client supplies one. With neither, the draft says the review was not possible.
9. **Clarification questions** for each bidder.
10. **Method and limitations.** Documents received, checks run and not run, unreadable pages, and how AI was used.
11. **Appendix.** Finding register with document, page and quote; the evaluators' decision log; the hash of the run record.

Each finding states its basis:

- **Fact.** A verified quote or a deterministic computation. Example: "Item 3.2.4: 40 CY × $180 = $7,200; stated $7,400."
- **Interpretation.** A judgement, including every proposed score. Example: "Methodology scores 6 of 10: it addresses traffic management and noise but not the interface with the occupied building next door (pp. 14 to 18)."

## 3. In scope

| # | Capability | Acceptance criterion |
|---|---|---|
| 1 | **Operable by the client's evaluators without help from Evalia**, as a local application on the evaluator's own computer with a browser-based interface (decided under question A, section 9) | A pilot evaluator installs it, completes set-up, review and output on a synthetic tender, and uninstalls it, without assistance |
| 2 | Engagement set-up: the evaluator registers tender documents and submissions, assigning each file a document type | No path to customer data in code or the repository; data stays where the customer keeps it |
| 3 | Ingestion of text-layer PDF, XLSX and DOCX, with page-level provenance | Every page either yields text or appears in the limitations list |
| 4 | Evaluation framework: the client's criteria, weights and anchors if supplied; otherwise the construction pack's defaults, confirmed or edited by the client | No proposed score is produced until the client has confirmed the criteria |
| 5 | Requirement extraction from tender documents (model-assisted), curated by the evaluator | 100% threshold preservation on the curated set (deterministic gate) |
| 6 | Compliance resolution for mandatory and technical requirements | Every status other than `not_addressed` or `not_applicable` carries at least one verified quote; every `not_addressed` states where the system looked |
| 7 | Proposed scores (SCR-01) with reasoning and verified evidence | Every proposed score cites evidence; weighted totals computed by code |
| 8 | Substantiation check (SUB-01) | Each claim and its supporting evidence quoted from both documents, or the absence of support stated |
| 9 | Pricing-schedule checks BQ-01 to BQ-06 (see `02-architecture.md`, section 6.2), for US unit-price and lump-sum bid forms | 100% recall on synthetic submissions with injected errors |
| 10 | Rate review (BQ-07): against peers (four or more submissions) and against the client's pre-tender estimate where supplied | Mode labelled; when neither is possible, the draft says so |
| 11 | Qualifications and departures register (QX-01, CON-01) | Every entry quoted and verified; the evaluator confirms completeness |
| 12 | Bonds, insurance (SEC-01) and programme dates (PRG-01) | Comparisons deterministic once the evaluator confirms the values |
| 13 | Evaluator review with a decision log | No finding or score reaches the output unless accepted or amended; every change carries a reason |
| 14 | Technical-before-price sequence, where the client's procedure requires it | Price documents are not ingested until the technical evaluation is confirmed; the run record shows the order |
| 15 | DOCX and Markdown output from a template in the construction pack | Matches section 2; every finding labelled and cited |
| 16 | LLM gateway with residency enforcement, caching and provenance (`03-llm-layer.md`, section 12) | A call that breaks the engagement's policy is refused; outputs regenerate from cache |
| 17 | Run record for each run | Hashes of all inputs and outputs, versions, model identifiers, cost |
| 18 | Synthetic golden set: US-style tenders with injected gaps, price errors and unsubstantiated claims | Generated by script; visibly fictitious; committed to the repository |
| 19 | United States overlay | Standard forms, bonding and licensing rules checked against current official sources |

## 4. Out of scope for version one

- **Bidder profile.** Follows version one (see `02-architecture.md`, section 6.4).
- **Award decisions.** The client decides. Combining quality and price by the client's formula is deferred.
- **A full multi-user web platform.** Accounts, roles, single sign-on and hosting for many organisations are excluded. The minimum interface that item 1 needs is in scope.
- **DeepSeek's integrity apparatus.** Cryptographic sealing, hash-chained audit ledgers, write-once export, HSM key custody, quorum unseal and external anchoring are excluded.
- **OCR of scanned documents.** Affected pages are listed as limitations.
- **Schedule files and drawings.** Primavera P6 and Microsoft Project files are not parsed; drawings and CAD are not analysed.
- **Languages other than English.** These are needed for the target markets beyond the United States and are planned after version one.
- **Hosting.** Evalia does not host customer documents in version one.
- **Overlays other than the United States.** The multilateral development bank overlay is recommended as the second.

## 5. Workflow for one tender

All manual steps are performed by the client's evaluators.

```
1  register tender documents and submissions; set residency policy
2  confirm evaluation criteria, weights and anchors (client's own, or pack defaults)
3  ingest                → text and tables, page provenance
4  extract requirements  → proposed requirements (model-assisted)
5  evaluator curates requirements; threshold gate must pass
6  resolve               → compliance matrix, substantiation, qualifications, departures
7  score                 → proposed scores with reasoning and evidence
8  evaluators accept, amend or reject every finding and score (reasons recorded)
9  [price stage] check   → pricing, bonding and programme findings; review as in step 8
10 produce output        → draft evaluation (DOCX, Markdown), run record
11 responsible evaluator signs off (recorded in the run record)
```

Step 9 runs after step 8 where the client separates technical from price evaluation; otherwise it can run alongside step 6.

## 6. Quality gates for each evaluation

1. Every cited quote is verified on its cited page (automated).
2. Every threshold in the curated requirements matches its source sentence (automated).
3. Every finding and score in the output is `accepted` or `amended`, and every change has a reason (automated).
4. Every finding carries a basis label (automated).
5. Weighted totals recompute exactly from the decided scores (automated).
6. The limitations section lists every page without text and every check not run (automated).
7. The client's responsible evaluator has signed off (recorded in the run record).

## 7. What the discovery test measures

Proposed measures; the choice is Victor's.

| Measure | How collected |
|---|---|
| Evaluator hours per tender, against the client's usual effort (EVA's benchmark: about 14 man-days per evaluator) | Time recorded in the software; client's estimate of its usual effort |
| Agreement between proposed and final scores, and the override rate by criterion | Decision log |
| Findings proposed against findings accepted, by check | Decision log |
| Issues the panel judged new to it, and material | Structured debrief |
| Price effect of pricing-schedule findings, as a share of each bid | Draft evaluation appendix |
| Model cost per tender | Run records |
| Points where evaluators needed help to operate the software | Debrief; support requests |
| Stated willingness to pay, and at what price | Debrief |

## 8. Milestones

Sequenced by exit criterion. Effort estimates are rough and should be revised after M1.

| Milestone | Exit criterion | Rough effort |
|---|---|---|
| M0 Scope approved | This document and `02-architecture.md` approved; question C in section 9 answered | — |
| M1 Skeleton and synthetic golden set | Engine skeleton, construction pack v0 with default criteria and US overlay stub, synthetic tenders with injected defects; tests on synthetic data only | 1 to 2 weeks |
| M2 Deterministic path | Ingestion, registration, BQ-01 to BQ-06, SEC-01, PRG-01, review with decision log, output template; 100% recall on injected pricing errors | 2 to 3 weeks |
| M3 Model-assisted path | Gateway (two adapters, residency, cache), requirement extraction with threshold gate, resolver, SUB-01, QX-01, CON-01, SCR-01; golden-set metrics for at least two model profiles | 3 to 4 weeks |
| M4 Local application | Item 1 met: a pilot evaluator installs and completes a synthetic tender unaided | 3 to 4 weeks |
| M5 First real evaluation | Evaluation 1 completed by a client's evaluators; debriefed | 1 to 2 weeks |
| M6 Evaluations 2 and 3 | Completed with fixes from evaluation 1; measures collected | 2 to 3 weeks |

**Speculation.** The total is roughly 12 to 18 weeks for one developer. The local application adds three to four weeks to the earlier estimate, because clients run the software themselves. The largest uncertainties are obtaining tenders with consent and the condition of real documents.

## 9. Decisions and open questions

### Decided on 29 October 2026

| # | Question | Decision | Consequence |
|---|---|---|---|
| 1 | Who are the clients? | All three kinds: public agencies, private owners and developers, and the consultants who evaluate for them. **Recorded point:** large agencies such as JTC run their own tools, but agencies in less developed markets (Africa, the Middle East, Central Asia) may not, and form a niche to target | Output must suit both public and private procedures; the market note is in `02-architecture.md`, section 1 |
| 2 | Will the client consent to processing all bidders' documents, and name permitted model providers? | Yes, required | Consent and provider choice are recorded in each engagement's settings before ingestion |
| 3 | Will clients share their evaluation framework and a past evaluation? | Not mandatory | The pack supplies default criteria and anchors; calibration against a past evaluation is optional |
| 4 | Which jurisdiction? | United States first; the aim is global, especially less developed markets | US overlay in version one; multilateral development bank overlay recommended second; other languages after version one |
| 5 | Will pre-tender estimates be supplied? | Revised: they may be; the estimate may be required for some tenders | Optional input. Rate review uses it when supplied, and peers when there are four or more submissions |
| 6 | Who works with Evalia, and who reviews the output? | Nobody from Evalia; the client's evaluators are the end users | Software must be operable unaided (item 1); the client signs off |
| 7 | Who is responsible for the evaluation? | The client | Output is a draft for the client's panel; wording makes the client's ownership explicit |
| 8 | Storage | Customers: wherever they choose. Victor's development and test material: OneDrive, confirmed (question B) | `CLAUDE.md`, section 3 |
| 9 | Bidder profile timing | After version one | Out of scope for version one (section 4) |
| — | Delivery model; serving both sides | Software operated by its users; both sides may use it under information controls | `02-architecture.md`, section 6.4; `CLAUDE.md`, section 4 |

**Note on question 5.** A pre-tender estimate is the client's own costed forecast of the works, prepared before tenders arrive. **Interpretation:** it is the only basis for a rate review when there are fewer than four submissions. It also lets the draft show each bid's departure from the client's expectation, which matters most where a single bid is received.

**Note on question 9.** This document reads Victor's "ok" as accepting the proposal that the bidder profile follows version one. If it was meant as preferring a bidder-side pilot first, sections 4 and 8 need revising.

### Decided after the first round (29 October 2026)

| # | Question | Decision |
|---|---|---|
| A | How do evaluators operate version one unaided? | A local application: it runs on the evaluator's own computer with a browser-based interface, and documents never leave the client. A guided workbook flow and a hosted service were rejected |
| B | Storage of Victor's development and test material | OneDrive, confirmed |

### Still open

**C. Which AI model providers may each discovery client's documents be sent to?** This decides the first model profile, and whether the self-hosted option is needed in version one. `03-llm-layer.md` sets out the options; the questions to put to each client are in section 10 of this document.

## 10. The model-provider question for clients

**Why it matters.** To read and judge submissions, Evalia sends passages of the tender documents to an AI model. Whoever runs that model receives those passages. A client must therefore decide where its bidders' confidential documents may go. Evalia records the answer in the engagement's settings and refuses any other destination (`03-llm-layer.md`, section 4).

| Option | What happens to the documents | Strengths | Weaknesses |
|---|---|---|---|
| 1. Commercial AI service hosted in the United States | Sent to the provider's servers, processed and, under suitable terms, not kept or used for training | Strongest models available (interpretation); no hardware; pay per use | Documents leave the client's country; the provider is a US company |
| 2. Commercial AI service hosted in a chosen region (for example the EU, through a major cloud provider) | Processed in that region | Similar quality to option 1; meets many residency rules | Regions on offer vary by provider and model; a US-owned provider may still be subject to US legal process |
| 3. Open-weight model run on the client's own computer or server | Never leave the client | Strongest confidentiality; no per-use fee; works where data must stay in the country | Needs a capable machine with a graphics processor; smaller models are likely to be less accurate (speculation, to be measured on the golden set) |

**Questions to put to each discovery client:**

1. May tender documents be processed by an external AI service at all?
2. If so, must processing stay in a particular country or region, and which?
3. Are any providers, or providers of any nationality, excluded?
4. Do the client's rules require a contract with the provider: a data-processing agreement, no training on the data, deletion after use?
5. If no external service is allowed: does the client have a computer with a suitable graphics processor, or a server, that could run a model?

**Recommendation for version one.** Build two routes: a US-hosted commercial service, and a self-hosted model reached through the same interface. Add region-specific hosted services as clients require them. The local application uses whichever route the engagement permits.

## 11. Change log

| Date | Change | Approved by |
|---|---|---|
| 29 October 2026 | Initial proposal (scrutiny reports for owners and lenders) | Superseded |
| 29 October 2026 | Repositioned as EVA-style evaluation support: proposed scores, substantiation check, decision log, technical-before-price sequence | Victor (positioning) |
| 29 October 2026 | Victor's answers recorded: all client types with a less-developed-market niche; United States first; frameworks optional; no pre-tender estimates; client-operated software with no Evalia staff involved; client responsible; both sides may use Evalia; operator interface added to scope | Pending approval of the whole document |
| 29 October 2026 | Pre-tender estimate becomes an optional input (rate review in two modes); local application chosen; OneDrive confirmed for test material; model-provider questions for clients added | Pending approval of the whole document |
| 29 October 2026 | The demo becomes a prototype of the whole evaluation, end to end, breadth before depth: engagement, reading the request for proposal, framework sign-off, receipt and opening, responsiveness, technical, commercial, contract deviations, integrity, clarifications, consolidation with weight sensitivity, report with panel approval, and the tenderer's pre-submission view. Where a stage is not yet built properly, a deterministic stand-in runs and says so. The Streamlit interface is replaced by one self-contained page built from the pipeline's output. Departure to note: the demo compares rates across three tenders, against the four-or-more rule in section 2, item 8 | Victor (instruction of 29 October 2026); whole document still pending |
| 29 October 2026 | Prototype extended from five further tender documents supplied by Victor, six in all (`docs/06-check-catalogue.md`): contradictions in the tender documents, tender security, addenda, words against figures, prices in the technical tender, licences and certificates, financial standing, domestic preference, technical threshold, award-method comparison, due diligence, and award notices with standstill | Victor (instruction of 29 October 2026); whole document still pending |
