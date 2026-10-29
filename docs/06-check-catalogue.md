# Check catalogue: what real tenders require, and what Evalia covers

Status: working note, 29 October 2026. It records what six real tender documents, supplied by Victor for design research, require of an evaluation, and which of those checks the prototype runs.

The documents themselves are tender data and are not stored in this repository (`CLAUDE.md`, section 3). They are described here only by type, and no names, figures or text from them are reproduced.

## 1. The reference documents

| Ref | Type | Procurement | Region |
|---|---|---|---|
| A | Request for proposal, interior fit-out works | Private developer, pre-qualified tenderers, technical and commercial volumes | Middle East |
| B | Invitation to tender, hotel furniture, fixtures and equipment, supply and install | Private developer, by invitation, two envelopes opened in two stages | Middle East |
| C | Request for proposal, temporary art installations (services, supply and works) | Public body, electronic two-envelope submission | Middle East |
| D | Instructions to tenderers, information technology supply in three lots | Public, under the EU external-action rules | Western Balkans |
| E | Design-and-build marine works, draft tender document | Grant-funded, restricted to pre-qualified firms | South Asia |
| F | Instructions to tenderers, public building works | Public, open national tender under a national standard document | East Africa |

## 2. What the sample shows

**Fact.** The six documents use four different award methods:

- Weighted price and quality scoring is not published in any of them. A, B and C list technical criteria without weights.
- D and E award to the lowest-priced tender that is compliant or substantially responsive. Nothing is scored.
- F applies a technical pass mark (60 of 80 points) with a cut-off for every criterion, and a financial-standing pass mark. It then awards to the lowest evaluated price, after a 10 per cent preference for indigenous-owned firms.
- C reserves price negotiation after evaluation. E negotiates down the ranking if the lowest tender is incomplete.

**Interpretation.** Evalia cannot assume weighted scoring. The checks that matter in every document are responsiveness, price integrity and qualification; scoring matters in a minority. This supports the positioning in `docs/05-positioning.md`: findings first, with scores only where the client uses them. The framework must let the client choose the award method. The prototype now shows the weighted and the lowest-price methods side by side.

**Fact.** Five of the six documents contradict themselves on at least one requirement:

- tender validity (120 days against 90 in B);
- contract signature (21 days against 14 in B);
- delay damages per day against per week (F);
- payment in 30 against 60 days (F);
- retention against the payment milestones (E);
- the guarantee release date (D);
- draft artefacts left in the text (C).

**Interpretation.** Checking the tender documents for consistency, before the framework is signed off, is a check that none of these employers appears to have run. It is cheap and deterministic, and it protects the client from a dispute about which value governs. The prototype now does it.

**Fact.** Most of the documents leave the decisive terms in annexes that were not supplied: conditions of contract, pricing schedules, specifications and selection thresholds (A, B, C, D and E).

**Interpretation.** Evalia should check that the tender dossier is complete before it reads any submission.

**Fact.** Precedence rules differ:
- C, D and E: words prevail over figures.
- B: figures prevail.
- D: the unit rate prevails over the extended total.
- F: the tender sum read out is final.
- E and B: the form of tender prevails over the bill total.
- The fictional demo tender: the lower of stated and corrected applies.

**Interpretation.** Each precedence rule must be configuration in the framework, not code.

## 3. The catalogue

The "seen in" column cites the reference documents. In the prototype column:
- "Built" means a deterministic check runs on the fictional documents and is covered by a test.
- "Stand-in" means a placeholder runs where a model reading is intended.
- "Not yet" means not built.

### Tender documents

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Internal contradictions | The same requirement stated with different values is flagged and resolved before sign-off | B, C, D, E, F | Built (validity, security validity) |
| Dossier completeness | Every annex the instructions cite is present | A, B, C, D, E | Built |
| Requirements register | Every requirement extracted with page and verified quote | All | Built |

### Receipt and opening

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Late receipt | Receipt time against the deadline; the panel decides where the rules give discretion | All | Built |
| One tender per tenderer | All tenders from a tenderer who submits twice are rejected | F | Built |
| Authority at opening | A representative's letter of authority is in order | E | Built (from the opening record) |

### Responsiveness

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Required documents | Set difference between required and submitted forms | All | Built |
| Documents per entity | Each joint-venture member, subcontractor and capacity provider supplies its own set | D, F | Built (subcontractors' tax clearance) |
| Signature and authority | Letter of tender signed; power of attorney present | All | Built |
| Validity period | At least the period required | All | Built |
| Tender security | Amount, validity beyond the tender validity, instrument type, currency | B, D, E, F | Built (amount, validity) |
| Addenda acknowledged | Set difference between addenda issued and acknowledged | B, E, F | Built |
| No prices in the technical envelope | Currency scan of the technical volume | B, C | Built |
| Page limits | Pages per section within the limit | B, C | Built |
| Alternatives | Considered only alongside a compliant base tender, or not at all | A, B, D, E, F | Built (presence) |
| Qualifications outside the deviations form | Not considered; the tenderer is asked to confirm or withdraw | A, B | Built |
| Site visit | Certificate present, where the visit is mandatory | C, F | Built |

### Technical

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Requirement coverage | Each requirement addressed, not demonstrated, or contradicted, with the quote | All | Stand-in (keyword matcher) |
| Programme | Duration within the completion period | All | Built |
| Key personnel | Roles named with minimum experience | B, E, F | Built |
| Experience | Thresholds checked against owners' own evaluations, not claims | B, C, F | Built |
| Technical threshold | Pass mark and cut-off per criterion before commercial opening | F | Built |
| Equipment | Required items and quantities, owned or leased | F | Built |
| Specification values | Offered values against the specified minimums and maximums | E | Built |
| Local workforce quota | Percentage of nationals in the team at least the quota | B, C | Built |

### Commercial

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Extensions and totals | Quantity times rate; bill and summary totals | All | Built |
| Correction rule | Applied as the tender states it | All | Built (lower of stated and corrected) |
| Words against figures | Applied with the tender's precedence | B, C, D, E | Built (words prevail) |
| Form of tender against the priced bill | Totals agree; the stated precedence applies | B, E | Built |
| Structure and unpriced items | Items and quantities as issued; blank or zero rates flagged | B, D, E, F | Built |
| Provisional sums | Carried at the employer's amounts; normalised | A, F | Built |
| Lots and discounts | Cheapest award across lots, with conditional discounts | A, D | Built |
| Currency and taxes | Single currency; taxes shown as required | C, D, E, F | Built |
| Rate consistency | Outliers against the median; front-loading; identical items priced alike | F | Built (outliers, front-loading) |
| Domestic preference | Margin added for comparison only | F | Built |
| Abnormally low price | Against the pre-tender estimate | None explicitly | Built |

### Contract

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Deviations register | Each proposed change against the particulars, by risk head, quantified | A, B | Built; risk head is a stand-in |

### Qualification and integrity

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Licences and certificates | Class as required; valid on the submission date | B, C, E, F | Built |
| Financial standing | Turnover as a multiple of the price; liquid assets | F (B and D require evidence only) | Built (turnover) |
| Accounts | Years covered; latest not older than allowed | B, F | Built (years covered) |
| Litigation and terminations | Disclosed matters above a threshold | A, B, F | Built |
| Conflicts and ownership | Declarations present; beneficial owners disclosed; owners shared across tenderers | B, D, F | Built |
| Joint-venture shares | Each partner and the lead meet minimum shares | F | Built |
| Cross-tender indicators | Identical rates, shared subcontractors | None (Evalia's addition) | Built |

### Decide and award

| Check | Rule enforced | Seen in | Prototype |
|---|---|---|---|
| Clarifications | Questions cannot change price or substance | All | Built (draft letters) |
| Award method | Weighted, or lowest evaluated price among compliant tenders | All | Built (both compared) |
| Due diligence | Verification of the preferred tenderer before award | D, F | Built (checklist) |
| Notification and standstill | All tenderers notified; no signature before the standstill ends | F, demo tender | Built |
| Negotiation | Only where the rules allow it, and recorded | C, E | Built (the rule is shown at award; no negotiation record yet) |

## 4. What this means for version one

**Fact.** Every check in the catalogue now runs in the prototype on the fictional documents (29 October 2026: `python -m pytest`, 30 passed). Several run in a narrower form than the catalogue describes; the "Prototype" column says how.

**Interpretation.**
- The remaining work is depth, not breadth: wider document matrices per entity, negotiation records, and readers for real document layouts.
- The two stand-ins (requirement coverage and risk-head classification) are where a model earns its place. They should be the first model readings tested on real documents, once a product key is configured.
- The variety of precedence rules and award methods argues for one framework file per tender, proposed from the tender documents and signed off by the client. That is the design the prototype now follows.

**Speculation.** Contradictions inside tender documents may be a stronger entry point for clients than the scoring itself, because they are found before any tender is opened and carry no evaluation risk. A conversation with two or three procurement managers would test this.
