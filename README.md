# Evalia

**AI reads the bids. Your panel decides.** Evalia is faster, fairer, consistent AI tender evaluation, starting with construction tenders, and built so that the evaluation holds up when challenged. It proposes findings and scores against the published criteria, each quoted to its page; code checks every quote and number; and the client's evaluators decide every finding, with their reasons kept.

**Status, 1 November 2026.** A working prototype runs a complete thirteen-stage evaluation on fictional documents: [open the prototype](https://expoversal.github.io/Evalia/). Fact: it makes no call to a language model yet. Every reading is deterministic code standing in for the model; the model gateway, prompts and output schemas are built and tested against a stand-in, but not connected.

| Document | What it covers |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Project rules: writing style, labels, confidential data, architecture |
| [`docs/01-designed-vs-built.md`](docs/01-designed-vs-built.md) | Audit of the original DeepSeek design conversation |
| [`docs/02-architecture.md`](docs/02-architecture.md) | Proposed architecture: industry-neutral engine and construction rubric pack |
| [`docs/03-llm-layer.md`](docs/03-llm-layer.md) | Model-agnostic LLM layer for US-hosted, EU-hosted and self-hosted models |
| [`docs/04-v1-scope.md`](docs/04-v1-scope.md) | Version one: three supported tender evaluations for the discovery test |
| [`docs/06-check-catalogue.md`](docs/06-check-catalogue.md) | What six real tenders require of an evaluation, and what the prototype covers |
| [`docs/07-handoff.md`](docs/07-handoff.md) | State of the work, decisions and next steps, for whoever picks it up |
| [`extracted/INVENTORY.md`](extracted/INVENTORY.md) | Every code fragment in the source conversation, and whether it runs |
| [`docs/deepseek-source.md`](docs/deepseek-source.md) | The source conversation (reference only) |

Tender and bid data are never stored in this repository. See `CLAUDE.md`, section 3.

## Running the prototype

The prototype runs the whole evaluation on one fictional request for proposal and three fictional tenders (`tests/fixtures/synthetic/`).

```bash
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` elsewhere), then:

```bash
pip install -e ".[ai,dev]"
```

```bash
python scripts/make_synthetic_tender.py
```

```bash
python scripts/build_demo.py
```

Open `build/evalia-prototype.html` in a browser. Everything runs on your own machine; decisions are kept in the browser and can be downloaded as a decision record. Add `#demo` to the address to show demonstration-only shortcuts that accept the remaining findings in a stage.

To run the tests:

```bash
python -m pytest
```

## What the prototype covers

| Stage | What Evalia does | How |
|---|---|---|
| Tender documents | Extracts the requirements register from the request for proposal, each entry quoted and checked against its page; flags requirements the document states with different values | Deterministic reader for the fictional format |
| Framework | Proposes streams, weights, criteria, contract baseline, risk heads and thresholds; the client signs off before opening | Construction pack defaults (`packs/construction/framework.yaml`) |
| Receipt and opening | Receipt time against the deadline; document fingerprints | Code |
| Responsiveness | Signature, power of attorney, validity, tender security, addenda, required forms, pricing structure, provisional sums, anti-collusion certificate, prices in the technical tender, qualifications outside the deviations form | Code; phrase search for qualifications |
| Technical | Requirement coverage of each methodology; programme, safety record, experience checked against owners' evaluations, key personnel | Code, except requirement coverage: a keyword stand-in for a model reading. Methodology is scored by the evaluator |
| Commercial | Arithmetic under the tender's correction rule, words against figures, provisional sums restored, evaluated price, domestic preference, rate comparison, cash-flow front-loading, estimate comparison, split against combined award | Code |
| Contract | Deviations register against the contract particulars, risk head, materiality, quantified at the evaluated price | Code, with a risk-head table standing in for a model classification |
| Qualification and integrity | Licence class and expiry, tax clearance, turnover against the price, litigation and terminations; identical rates and shared subcontractors across tenders | Code |
| Clarifications, consolidation, award, report | Draft questions and letters; technical threshold; scores from decided findings only; weight sensitivity; weighted against lowest-price award; due diligence; award notices and standstill; report with the panel chair's approval | Code, in the page |
| Tenderer's view | The same checks on a tenderer's own draft, without any comparison with other tenders or scores | Code |

The model-based readers (`packs/construction/extract.py`) go through the LLM gateway and are tested with a stand-in model only; no product API key has been configured yet.
