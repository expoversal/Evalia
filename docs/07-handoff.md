# Handoff: state of the work on 29 October 2026

This note lets another assistant (for example Claude Cowork) or a collaborator pick up the work without the original conversation. Read `CLAUDE.md` first: its rules bind any assistant working on Evalia, including the rule that tender data never enters the repository or a model without Victor's explicit authorisation.

## Where things are

| Item | Location |
|---|---|
| Code and documents | GitHub `expoversal/Evalia`, branch `claude/optimistic-shannon-bzbmhe` |
| Pull request (draft) | https://github.com/expoversal/Evalia/pull/1 |
| Interactive prototype (public, GitHub Pages) | https://expoversal.github.io/Evalia/ |
| Project rules | `CLAUDE.md` |
| Scope and change log | `docs/04-v1-scope.md`, sections 9 to 11 |
| Positioning and demo storyline | `docs/05-positioning.md` |
| Checks required by real tenders, and what the prototype covers | `docs/06-check-catalogue.md` |

## What exists

- An audit of the original DeepSeek design conversation (`docs/01-designed-vs-built.md`, `extracted/`).
- The architecture: an industry-neutral engine (`evalia/engine/`) and a construction pack (`packs/construction/`). Model calls go only through the gateway (`evalia/engine/llm.py`).
- A prototype of the whole evaluation in 13 stages, on one fictional request for proposal and three fictional tenders (`tests/fixtures/synthetic/`), from engagement to the panel-approved report, plus a tenderer's pre-submission view.
- **Fact.** `python -m pytest` gives 30 passed on 29 October 2026, and a scripted browser walkthrough of all 13 stages reported no errors.

## Decisions taken by Victor (29 October 2026)

- Evalia helps clients evaluate tenders, as JTC's EVA does. Bidders may use the same engine to check their own drafts, and the two sides' information never meets.
- Evalia is software that clients run themselves; Evalia's staff take no part.
- The United States comes first; the aim is global, with less developed markets as a niche.
- Delivery is a local application. Development and test material lives in Victor's OneDrive folder, found through `EVALIA_DATA_DIR`.
- For the Y Combinator application (due 2 November 2026), the demo shows the whole process, breadth before depth, even where parts are stand-ins.

## Open questions

- Which model providers each client accepts (`docs/04-v1-scope.md`, section 10).
- Approval of the whole scope document.
- Positioning points awaiting confirmation: proposed scores against findings only; who signs; whether Europe is a target market.

## Next steps

1. Draft the video script: four or five moments that make the case. Candidates:
   - contradictions found in the tender documents before opening;
   - a claimed rating contradicted by the owner's own evaluation;
   - the commercial walk from stated offer to evaluated price;
   - shared ownership and identical rates across two tenderers;
   - the panel-approved report.
2. Configure a product model key (`EVALIA_MODEL`, `EVALIA_ANTHROPIC_API_KEY`) and test the two model readings that are stand-ins today: requirement coverage and risk-head classification.
3. Record on 1 November 2026; submit on 2 November 2026.

## How to run it

```bash
pip install -e ".[ai,dev]"
```

```bash
python scripts/make_synthetic_tender.py
```

```bash
python scripts/build_demo.py
```

Then open `build/evalia-prototype.html` in a browser.

## Confidential material

Victor supplied six real tender documents as design research. They are not in the repository, and `docs/06-check-catalogue.md` describes them by type only. Any assistant that is to read them again needs Victor's explicit authorisation for that purpose.
