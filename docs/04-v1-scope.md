# Version one scope: three supported tender evaluations for the discovery test

Status: proposal for review, revised 29 October 2026 after Victor's decisions (section 9). Once approved, this document is authoritative. Anything not listed under "In scope" is out of scope until Victor approves a change, and approved changes are recorded in section 10.

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
8. **Rate review.** Outliers against the other submissions, when there are four or more. With fewer, the draft says the review was not possible. No pre-tender estimates will be supplied in version one.
9. **Clarification questions** for each bidder.
10. **Method and limitations.** Documents received, checks run and not run, unreadable pages, and how AI was used.
11. **Appendix.** Finding register with document, page and quote; the evaluators' decision log; the hash of the run record.

Each finding states its basis:

- **Fact.** A verified quote or a deterministic computation. Example: "Item 3.2.4: 40 CY × $180 = $7,200; stated $7,400."
- **Interpretation.** A judgement, including every proposed score. Example: "Methodology scores 6 of 10: it addresses traffic management and noise but not the interface with the occupied building next door (pp. 14 to 18)."

## 3. In scope

| # | Capability | Acceptance criterion |
|---|---|---|
| 1 | **Operable by the client's evaluators without help from Evalia**, in the form decided under open question A (section 9) | A pilot evaluator completes set-up, review and output on a synthetic tender without assistance |
| 2 | Engagement set-up: the evaluator registers tender documents and submissions, assigning each file a document type | No path to customer data in code or the repository; data stays where the customer keeps it |
| 3 | Ingestion of text-layer PDF, XLSX and DOCX, with page-level provenance | Every page either yields text or appears in the limitations list |
| 4 | Evaluation framework: the client's criteria, weights and anchors if supplied; otherwise the construction pack's defaults, confirmed or edited by the client | No proposed score is produced until the client has confirmed the criteria |
| 5 | Requirement extraction from tender documents (model-assisted), curated by the evaluator | 100% threshold preservation on the curated set (deterministic gate) |
| 6 | Compliance resolution for mandatory and technical requirements | Every status other than `not_addressed` or `not_applicable` carries at least one verified quote; every `not_addressed` states where the system looked |
| 7 | Proposed scores (SCR-01) with reasoning and verified evidence | Every proposed score cites evidence; weighted totals computed by code |
| 8 | Substantiation check (SUB-01) | Each claim and its supporting evidence quoted from both documents, or the absence of support stated |
| 9 | Pricing-schedule checks BQ-01 to BQ-06 (see `02-architecture.md`, section 6.2), for US unit-price and lump-sum bid forms | 100% recall on synthetic submissions with injected errors |
| 10 | Rate review against peers (BQ-07), four or more submissions | When fewer, the draft states that the review was not possible |
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
- **Rate review against pre-tender estimates.** Excluded by the decision in section 9.
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
| M0 Scope approved | This document and `02-architecture.md` approved; open questions A to C in section 9 answered | — |
| M1 Skeleton and synthetic golden set | Engine skeleton, construction pack v0 with default criteria and US overlay stub, synthetic tenders with injected defects; tests on synthetic data only | 1 to 2 weeks |
| M2 Deterministic path | Ingestion, registration, BQ-01 to BQ-06, SEC-01, PRG-01, review with decision log, output template; 100% recall on injected pricing errors | 2 to 3 weeks |
| M3 Model-assisted path | Gateway (two adapters, residency, cache), requirement extraction with threshold gate, resolver, SUB-01, QX-01, CON-01, SCR-01; golden-set metrics for at least two model profiles | 3 to 4 weeks |
| M4 Operator interface | Item 1 met: a pilot evaluator completes a synthetic tender unaided | 2 to 4 weeks, depending on the answer to question A |
| M5 First real evaluation | Evaluation 1 completed by a client's evaluators; debriefed | 1 to 2 weeks |
| M6 Evaluations 2 and 3 | Completed with fixes from evaluation 1; measures collected | 2 to 3 weeks |

**Speculation.** The total is roughly 11 to 18 weeks for one developer. The operator interface adds two to four weeks to the previous estimate, because clients now run the software themselves. The largest uncertainties are obtaining tenders with consent and the condition of real documents.

## 9. Decisions and open questions

### Decided on 29 October 2026

| # | Question | Decision | Consequence |
|---|---|---|---|
| 1 | Who are the clients? | All three kinds: public agencies, private owners and developers, and the consultants who evaluate for them. **Recorded point:** large agencies such as JTC run their own tools, but agencies in less developed markets (Africa, the Middle East, Central Asia) may not, and form a niche to target | Output must suit both public and private procedures; the market note is in `02-architecture.md`, section 1 |
| 2 | Will the client consent to processing all bidders' documents, and name permitted model providers? | Yes, required | Consent and provider choice are recorded in each engagement's settings before ingestion |
| 3 | Will clients share their evaluation framework and a past evaluation? | Not mandatory | The pack supplies default criteria and anchors; calibration against a past evaluation is optional |
| 4 | Which jurisdiction? | United States first; the aim is global, especially less developed markets | US overlay in version one; multilateral development bank overlay recommended second; other languages after version one |
| 5 | Will pre-tender estimates be supplied? | No | Rate review against peers only (four or more submissions) |
| 6 | Who works with Evalia, and who reviews the output? | Nobody from Evalia; the client's evaluators are the end users | Software must be operable unaided (item 1); the client signs off |
| 7 | Who is responsible for the evaluation? | The client | Output is a draft for the client's panel; wording makes the client's ownership explicit |
| 8 | Storage | To be confirmed in early stages | See open question B |
| 9 | Bidder profile timing | After version one | Out of scope for version one (section 4) |
| — | Delivery model; serving both sides | Software operated by its users; both sides may use it under information controls | `02-architecture.md`, section 6.4; `CLAUDE.md`, section 4 |

**Note on question 5.** A pre-tender estimate is the client's own costed forecast of the works, prepared before tenders arrive. **Interpretation:** without one, a tender with fewer than four submissions gets no rate review. Clients that do have an estimate could later supply it as an optional input.

**Note on question 9.** This document reads Victor's "ok" as accepting the proposal that the bidder profile follows version one. If it was meant as preferring a bidder-side pilot first, sections 4 and 8 need revising.

### Still open

**A. How do evaluators operate version one unaided?** Three options:

| Option | For | Against |
|---|---|---|
| Guided workbook flow: drop files in a folder, run one launcher, review spreadsheets | Cheapest to build | Fragile for non-technical users; poor fit with "operable unaided" |
| Local application: runs on the evaluator's own machine, with a simple browser interface on that machine | Data never leaves the client; works offline apart from model calls; suits data-localisation laws and the self-hosted model option | Installation and updates on client machines |
| Hosted service | Easiest for users | Evalia becomes custodian of every bidder's confidential documents, with the security, residency and contractual burden that follows; conflicts with keeping staff away from customer data |

**Recommendation:** a local application. **Interpretation:** it fits the target markets (data-localisation rules, unreliable connectivity) and the rule that Evalia's staff never see customer data. It also keeps the discovery test free of hosting obligations.

**B. Where does data live?** For customers, wherever they choose (their machine or their storage). For Victor's development and test material, OneDrive is to be confirmed.

**C. Which model providers may the three discovery clients accept?** This decides the first model profile, and whether the self-hosted option is needed in version one.

## 10. Change log

| Date | Change | Approved by |
|---|---|---|
| 29 October 2026 | Initial proposal (scrutiny reports for owners and lenders) | Superseded |
| 29 October 2026 | Repositioned as EVA-style evaluation support: proposed scores, substantiation check, decision log, technical-before-price sequence | Victor (positioning) |
| 29 October 2026 | Victor's answers recorded: all client types with a less-developed-market niche; United States first; frameworks optional; no pre-tender estimates; client-operated software with no Evalia staff involved; client responsible; both sides may use Evalia; operator interface added to scope | Pending approval of the whole document |
