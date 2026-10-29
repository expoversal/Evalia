# Evalia

Evalia helps clients evaluate construction tenders, in the manner of JTC Corporation's EVA: it proposes compliance findings and scores with explicit reasoning and evidence, and the client's evaluators decide. It is at the design stage, and no product code has been written yet.

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
