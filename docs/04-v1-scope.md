# Version one scope: three supported tender evaluations for the discovery test

Status: proposal for review, revised 29 October 2026 after Victor confirmed that Evalia should work like EVA. Once approved, this document is authoritative. Anything not listed under "In scope" is out of scope until Victor approves a change, and approved changes are recorded in section 10.

## 1. Objective

Support **three real construction tender evaluations** for prospective clients, producing for each a draft evaluation that the client's evaluators review and finalise. The test examines one proposition:

> A draft evaluation that maps each submission against the client's own criteria, with proposed scores whose reasoning and evidence are explicit, lets evaluators finish faster and catch issues they would otherwise miss.

**Fact.** EVA's reported value lies in the same two places: workload (about 34,000 man-hours a year across JTC's construction tenders) and catching inconsistencies such as performance ratings the supporting documents did not substantiate (Business Times article, text supplied by Victor on 29 October 2026). **Interpretation:** Evalia's discovery test should therefore measure both, against the client's usual process.

Version one is the smallest system that can support those three evaluations to a professional standard. It is not a product release.

## 2. What the draft evaluation contains

One draft evaluation per tender, covering every submission received:

1. **Summary for the evaluation panel.** Proposed ranking on quality, the five to ten most consequential findings, and the open clarification questions.
2. **Compliance matrix.** Each mandatory and technical requirement against each submission: status, verified quotes with page references, and gaps.
3. **Proposed scores.** For each criterion in the client's evaluation framework and each submission: a proposed score against defined anchors, the reasoning, and the evidence. Weighted totals are computed deterministically.
4. **Substantiation.** Claims in a submission (performance ratings, track record, certifications, key personnel) checked against the supporting documents submitted with it.
5. **Price integrity.** Arithmetic errors, omitted or altered items, provisional sums, zero-rated and "included" items, and their combined price effect, presented separately where the client's procedure evaluates price after quality.
6. **Qualifications and departures.** Every exclusion, assumption, qualification and departure from the conditions of contract, quoted and cited.
7. **Security and programme.** Bonds, guarantees and insurances against the requirements; completion and sectional dates against the contract.
8. **Rate review.** Outliers against other submissions (four or more) or against the client's pre-tender estimate.
9. **Clarification questions** for each bidder.
10. **Method and limitations.** Documents received, checks run and not run, unreadable pages, and how AI was used.
11. **Appendix.** Finding register with document, page and quote; the evaluators' decision log; the hash of the run record.

Each finding states its basis:

- **Fact.** A verified quote or a deterministic computation. Example: "Item 3.2.4: 40 m³ × S$180 = S$7,200; stated S$7,400."
- **Interpretation.** A judgement, including every proposed score. Example: "Methodology scores 6 of 10: it addresses traffic management and noise but not the interface with the occupied building next door (p.14 to 18)."

## 3. In scope

| # | Capability | Acceptance criterion |
|---|---|---|
| 1 | Engagement set-up from `engagement.yaml` and `register.yaml` in `EVALIA_DATA_DIR` | Runs without any path to client data in code or the repository |
| 2 | Ingestion of text-layer PDF, XLSX and DOCX, with page-level provenance | Every page either yields text or appears in the limitations list |
| 3 | The client's evaluation framework captured as pack data: criteria, weights, anchors | Every criterion has anchors agreed with the client before scoring starts |
| 4 | Requirement extraction from tender documents (model-assisted), curated by the evaluator | 100% threshold preservation on the curated set (deterministic gate) |
| 5 | Compliance resolution for mandatory and technical requirements | Every status other than `not_addressed` or `not_applicable` carries at least one verified quote; every `not_addressed` states where the system looked |
| 6 | Proposed scores (SCR-01) with reasoning and verified evidence | Every proposed score cites evidence; weighted totals computed by code |
| 7 | Substantiation check (SUB-01) | Each claim and its supporting evidence quoted from both documents, or the absence of support stated |
| 8 | Price checks BQ-01 to BQ-06 (see `02-architecture.md`, section 6.2) | 100% recall on synthetic submissions with injected errors |
| 9 | Rate review (BQ-07): against other submissions when there are four or more, otherwise against the client's estimate | Mode labelled; when neither is possible, the evaluation says so |
| 10 | Qualifications and departures register (QX-01, CON-01) | Every entry quoted and verified; evaluator confirms completeness |
| 11 | Security package (SEC-01) and programme dates (PRG-01) | Comparisons deterministic once values are confirmed |
| 12 | Evaluator review round trip, with a decision log | No finding or score reaches the evaluation unless accepted or amended; every change carries a reason |
| 13 | Technical-before-price sequence, where the client's procedure requires it | Price documents are not ingested until the technical evaluation is confirmed; the run record shows the order |
| 14 | DOCX and Markdown output from a template in the construction pack | Matches section 2; every finding labelled and cited |
| 15 | LLM gateway with residency enforcement, caching and provenance (`03-llm-layer.md`, section 12) | A call that breaks the engagement's policy is refused; outputs regenerate from cache |
| 16 | Run record for each run | Hashes of all inputs and outputs, versions, model identifiers, cost |
| 17 | Synthetic golden set with injected gaps, errors and unsubstantiated claims | Generated by script; visibly fictitious; committed to the repository |
| 18 | One jurisdiction overlay, matching the discovery tenders | Registry and clause rules checked against current official sources |

## 4. Out of scope for version one

- **Bidder pre-submission profile.** Proposed for after version one (see `02-architecture.md`, section 6.4).
- **Award decisions.** Evalia proposes; the client decides. Combining quality and price by the client's formula is deferred.
- Web UI, multi-user accounts, role-based access control, single sign-on. Version one uses review workbooks; EVA's step-by-step interface is a later goal.
- Cryptographic sealing, hash-chained audit ledgers, write-once export, HSM key custody, quorum unseal, external anchoring.
- OCR of scanned documents. Affected pages are listed as limitations, or key figures are transcribed by hand and labelled as such.
- Parsing of Primavera P6 or Microsoft Project files; analysis of drawings or CAD.
- Submissions in languages other than English.
- PostgreSQL, vector databases and any server deployment.
- More than one jurisdiction overlay.

## 5. Workflow for one tender

```
1  set up engagement folder, engagement.yaml, register.yaml            (manual)
2  capture the client's criteria, weights and anchors                 (manual, agreed with client)
3  evalia ingest            → text and tables, page provenance
4  evalia extract-reqs      → requirements workbook (model-assisted)
5  evaluator curates requirements; threshold gate must pass           (manual)
6  evalia resolve           → compliance matrix, substantiation, qualifications, departures
7  evalia score             → proposed scores with reasoning and evidence
8  evalia review-export     → review workbook
9  evaluators accept, amend or reject every finding and score         (manual, reasons recorded)
10 [price stage] evalia check → price, security and programme findings; review as in 8 to 9
11 evalia report            → draft evaluation (DOCX, Markdown), run record
12 second reader checks the evaluation before release                 (manual)
```

Command names are illustrative. Step 10 runs after step 9 where the client separates technical from price evaluation; otherwise it can run alongside step 6.

## 6. Quality gates for each evaluation

1. Every cited quote is verified on its cited page (automated).
2. Every threshold in the curated requirements matches its source sentence (automated).
3. Every finding and score in the output is `accepted` or `amended`, and every change has a reason (automated).
4. Every finding carries a basis label (automated).
5. Weighted totals recompute exactly from the decided scores (automated).
6. The limitations section lists every page without text and every check not run (automated).
7. A second reader has signed off (manual; recorded in the run record).

## 7. What the discovery test measures

Proposed measures; the choice is Victor's.

| Measure | How collected |
|---|---|
| Evaluator hours per tender, against the client's usual effort (EVA's benchmark: about 14 man-days per evaluator) | Time logs; client's estimate of its usual effort |
| Agreement between proposed and final scores, and the override rate by criterion | Decision log |
| Findings proposed against findings accepted, by check | Review workbooks |
| Issues the panel judged new to it, and material | Structured debrief |
| Price effect of arithmetic and omission findings, as a share of each bid | Evaluation appendix |
| Model cost per tender | Run records |
| Stated willingness to pay, and at what price | Debrief |
| Errors found in Evalia's output after release | Panel feedback; second-reader notes |

## 8. Milestones

Sequenced by exit criterion. Effort estimates are rough and should be revised after M1.

| Milestone | Exit criterion | Rough effort |
|---|---|---|
| M0 Scope approved | This document and `02-architecture.md` approved; open questions in section 9 answered | — |
| M1 Skeleton and synthetic golden set | Engine skeleton, construction pack v0 stub, synthetic tenders with injected errors and unsubstantiated claims; tests on synthetic data only | 1 to 2 weeks |
| M2 Deterministic path | Ingestion, register, BQ-01 to BQ-06, SEC-01, PRG-01, review round trip with decision log, output template; 100% recall on injected price errors | 2 to 3 weeks |
| M3 Model-assisted path | Gateway (two adapters, residency, cache), requirement extraction with threshold gate, resolver, SUB-01, QX-01, CON-01, SCR-01; golden-set metrics for at least two model profiles | 3 to 4 weeks |
| M4 First real evaluation | Evaluation 1 supported, passed the quality gates, debriefed | 1 to 2 weeks |
| M5 Evaluations 2 and 3 | Delivered with fixes from evaluation 1; measures collected | 2 to 3 weeks |

**Speculation.** The total is roughly 9 to 14 weeks of one developer working with one construction evaluator. Scoring adds about a week to the earlier estimate. The largest uncertainties are obtaining tenders with consent and the condition of real documents.

## 9. Open questions to settle before M1

1. **Who are the three clients?** Public agencies, private owners or developers, or the consultants (quantity surveyors, project managers) who evaluate on their behalf? **Interpretation:** large agencies such as JTC build their own tools; consultants and private owners may be the more open market. This decides the output format.
2. **Which tenders, and on what terms?** The client must consent to Evalia processing every bidder's submission, and name the model providers it permits.
3. **Will clients share their evaluation framework and a past evaluation** against which proposed scores can be calibrated?
4. **Which jurisdiction?**
5. **Will pre-tender estimates be supplied?**
6. **Who is the evaluator working with Evalia, and who is the second reader?**
7. **Liability and wording.** How should the output be framed so that the client's panel clearly owns the evaluation?
8. **Storage.** Do the clients accept OneDrive as the location of their tender documents?
9. **Bidder profile.** Should it follow version one, or would a bidder-side pilot be easier to obtain first? **Interpretation:** a bidder can consent for its own submission alone, whereas an evaluation needs the client's consent covering every bidder's confidential documents.

## 10. Change log

| Date | Change | Approved by |
|---|---|---|
| 29 October 2026 | Initial proposal (scrutiny reports for owners and lenders) | Superseded |
| 29 October 2026 | Repositioned as EVA-style evaluation support: proposed scores, substantiation check, decision log, technical-before-price sequence; bidder profile proposed for later | Pending |
