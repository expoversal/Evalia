# Positioning: reconciling the EVA research with Victor's decisions

Status: 29 October 2026. Sources: [`research/2026-10-29-eva-governance-bar.md`](research/2026-10-29-eva-governance-bar.md) (Victor's research report) and Victor's decisions recorded in [`04-v1-scope.md`](04-v1-scope.md), section 9.

The research report was written for an earlier model, in which Evalia is an independent service and a Chartered Civil Engineer signs its findings. Victor has since decided that Evalia is software that clients run themselves. The table shows how each point is resolved.

| Point | Research report | Victor's decision | Resolution |
|---|---|---|---|
| Operator | Independent third party engaged by the owner | Software run by the client; Evalia's staff take no part | **Client-run software.** Evalia sits inside the client's own accountability chain, as EVA does inside JTC's. |
| Scores or findings | Findings by default; scores only on written request, because an outsider should not score | EVA-like: proposed scores with reasoning | **Both, in a fixed order.** Every output is a cited finding first. Scores for quantitative criteria are computed by code from those findings, using rules the client configured and signed off. Qualitative scores are off by default. Evalia never recommends an award. The report itself accepts scoring by the owner's own tool. |
| Sequence | Adopt EVA's: context, who is assessed, criteria validation, then submissions | — | **Adopted.** No submission is read until the client has signed off the criteria. |
| Signature | The Chartered Civil Engineer signs | The client is responsible; nobody from Evalia takes part | **The client's responsible evaluator signs.** The founder's chartered status is a credential for the pitch, not a step in the product. |
| Governance layer | The moat: citations, retention, accept/reject/modify log, disclosure clause, no-training terms, "not assessed" list, published metrics | — | **Adopted in full** as product features. The demo shows citations, the decision log and the "not assessed" list. |
| Conflicts | Per-procurement declaration of no relationship with any bidder | Both sides may use Evalia under information controls | **Information controls stand** (`02-architecture.md`, section 6.4). **Interpretation:** the founder's history on the contractor side makes the separation worth stating plainly in the pitch. |
| Markets | US, Gulf, Europe; Singapore as reference only | US first; Africa, the Middle East and Central Asia as a niche | **US first, then the less developed markets.** The Gulf falls within the Middle East. Whether Europe is a target is open. |
| Use of EVA in the pitch | Precedent, not proof of a market; cite BT; no JTC branding; never "EVA for X" | — | **Adopted.** Lead with error and defensibility (EVA's catch; the Trax case), not with man-hours. Present JTC's two-to-three-month figure only as a projection. |
| Demand | No evidence that anyone buys this | — | **Open.** The discovery test measures willingness to pay. |

## Demo storyline that follows

1. **Context.** One fictional US tender: a light-industrial building.
2. **Tenderers.** Three fictional bidders.
3. **Criteria.** EVA-style parameters for "relevant completed projects": keywords, a year range, a minimum contract value, a minimum performance rating, prime-contractor status, points per project and a maximum count. Plus a safety criterion and bid compliance items. The evaluator signs off the criteria before any bid is opened.
4. **Submissions.** The three bids are read, and every extracted fact is cited to a page and checked against it.
5. **Findings.** Three kinds of finding:
   - which projects qualify and which do not, and why (Fact: computed from cited data);
   - a claimed rating that the attached owner evaluation contradicts (the EVA-type catch);
   - a missing bid bond and an arithmetic error in the bid schedule.
6. **Review.** The evaluator accepts, rejects or modifies each finding, giving a reason for anything other than acceptance.
7. **Output.** A draft evaluation with scores computed by code, the decision log, the "not assessed" list and an acknowledgement of AI use.
