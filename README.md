# Evalia

Evalia helps clients evaluate construction tenders. It proposes compliance findings and scores, with explicit reasoning and cited evidence, and the client's evaluators decide. A proof-of-concept demo is under construction.

| Document | What it covers |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Project rules: writing style, labels, confidential data, architecture |
| [`docs/01-designed-vs-built.md`](docs/01-designed-vs-built.md) | Audit of the original DeepSeek design conversation |
| [`docs/02-architecture.md`](docs/02-architecture.md) | Proposed architecture: industry-neutral engine and construction rubric pack |
| [`docs/03-llm-layer.md`](docs/03-llm-layer.md) | Model-agnostic LLM layer for US-hosted, EU-hosted and self-hosted models |
| [`docs/04-v1-scope.md`](docs/04-v1-scope.md) | Version one: three supported tender evaluations for the discovery test |
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
| Tender documents | Extracts the requirements register from the request for proposal, each entry quoted and checked against its page | Deterministic reader for the fictional format |
| Framework | Proposes streams, weights, criteria, contract baseline, risk heads and thresholds; the client signs off before opening | Construction pack defaults (`packs/construction/framework.yaml`) |
| Receipt and opening | Receipt time against the deadline; document fingerprints | Code |
| Responsiveness | Signature, power of attorney, validity, required forms, pricing structure, provisional sums, anti-collusion certificate, qualifications outside the deviations form | Code; phrase search for qualifications |
| Technical | Requirement coverage of each methodology; programme, safety record, experience checked against owners' evaluations, key personnel | Code, except requirement coverage: a keyword stand-in for a model reading. Methodology is scored by the evaluator |
| Commercial | Arithmetic under the tender's correction rule, provisional sums restored, evaluated price, rate comparison, cash-flow front-loading, estimate comparison, split against combined award | Code |
| Contract | Deviations register against the contract particulars, risk head, materiality, quantified at the evaluated price | Code, with a risk-head table standing in for a model classification |
| Integrity | Litigation and termination disclosures; identical rates and shared subcontractors across tenders | Code |
| Clarifications, consolidation, report | Draft questions and letters; scores from decided findings only; weight sensitivity; report with the panel chair's approval | Code, in the page |
| Tenderer's view | The same checks on a tenderer's own draft, without any comparison with other tenders or scores | Code |

The model-based readers (`packs/construction/extract.py`) go through the LLM gateway and are tested with a stand-in model only; no product API key has been configured yet.
