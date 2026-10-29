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

## Running the demo

The demo uses one fictional tender and three fictional bids (`tests/fixtures/synthetic/`).

```bash
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` elsewhere), then:

```bash
pip install -e ".[ai,dev]"
```

```bash
streamlit run app/streamlit_app.py
```

The application opens in the browser on your own machine. Without an AI model it reads the bids' standard forms deterministically. To use an AI model, set `EVALIA_MODEL` (the model identifier) and `EVALIA_ANTHROPIC_API_KEY` before starting it; the model then reads the bids, and every quote it returns is checked against the page it cites. Engagement files are written to `EVALIA_DATA_DIR` (by default `~/.evalia-demo`).

To regenerate the fictional documents and run the tests:

```bash
python scripts/make_synthetic_tender.py
```

```bash
python -m pytest
```

