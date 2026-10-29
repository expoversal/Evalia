# Model-agnostic LLM layer

Status: proposal for review, 29 October 2026. No code exists yet. Claims about providers are labelled. Hosting regions, retention terms and model availability change often, so each must be confirmed against the provider's current terms before an engagement relies on it.

## 1. Requirements

1. **Model-agnostic.** No engine or pack code depends on a particular vendor's SDK or model name.
2. **Three hosting classes:** US-hosted APIs, EU-hosted APIs, and self-hosted open-weight models.
3. **Residency enforced, not advised.** Each engagement declares where its data may be processed. The gateway refuses any call that would break the declaration.
4. **Structured output** validated against a schema, with failures surfaced rather than hidden.
5. **Reproducible.** Every call is recorded, and a report can be regenerated from cached responses.
6. **Measured.** Every profile is evaluated on the same golden set before it is used on client data.
7. **No training on client data,** and retention kept to the minimum the provider offers.

## 2. Structure

The layer separates **what is asked** from **who answers** and **how the request travels**.

```
 Engine / pack ──▶ Task ──▶ Router ──▶ Profile ──▶ Adapter ──▶ Provider endpoint
                    │         │          │            │
   e.g. "requirement.extract" │   model, endpoint,   transport: Anthropic Messages,
        "compliance.resolve"  │   region, params,    OpenAI-compatible, Bedrock
        "qualification.extract"   residency class    Converse, Gemini, local
                              │
                    engagement residency policy
                    (fails closed if nothing qualifies)
```

- **Task.** A named operation with an input template (from the pack), an output schema (a Pydantic model) and a token budget.
- **Profile.** A named configuration: adapter, endpoint, model identifier, region, residency class, parameters, and capability flags (native JSON-schema output, context length, prompt caching).
- **Router.** Picks the profile for each task from the engagement's settings, after checking the residency policy.
- **Adapter.** Translates a provider-neutral request into one transport and normalises the response, usage and errors.

### Illustrative interface

This sketch shows the shape of the interface. It is not code to copy.

```text
Gateway.run(task: TaskSpec, inputs: dict, engagement: EngagementPolicy) -> TaskResult

TaskResult:
  output        validated object, or None
  status        ok | invalid_output | refused_by_policy | provider_error
  raw_text      as returned
  provenance    adapter, endpoint, region, model_id_returned, params,
                prompt_sha256, schema_sha256, input_sha256, output_sha256,
                tokens_in, tokens_out, cost_estimate, latency_ms, cache_hit
```

## 3. Adapters

| Adapter | Covers | Hosting classes |
|---|---|---|
| `anthropic_messages` | Anthropic API | US (Fact: Anthropic is a US company; confirm its current processing locations) |
| `bedrock_converse` | Amazon Bedrock Converse API: Claude, Mistral, Llama and other models | US or EU, depending on the AWS region chosen (Fact: Bedrock runs in EU regions such as Frankfurt and Ireland; confirm per model) |
| `openai_compatible` | OpenAI; Azure OpenAI; self-hosted servers such as vLLM, llama.cpp and Ollama; other providers that expose the same API shape | US, EU (Azure EU regions and EU data-zone deployments; confirm current options) or self-hosted |
| `mistral` | Mistral AI's own API | EU (Fact: Mistral AI is a French company; confirm where requests are processed) |
| `gemini` (optional) | Google Gemini API, or Vertex AI with regional endpoints | US or EU, by region |

**Recommendation.** Build `openai_compatible` and `anthropic_messages` first. Together they cover a US API, self-hosted models and, through Azure in EU regions, an EU-hosted option. Add `bedrock_converse` or `mistral` when an engagement needs a specific EU arrangement.

**Recommendation on LiteLLM.** The transcript suggested LiteLLM. Keep Evalia's own thin interface, and allow LiteLLM as one possible adapter behind it if its breadth becomes useful. **Interpretation:** owning the interface keeps residency checks, provenance recording and caching in Evalia's code, where they can be tested. Delegating them to a fast-moving third-party library would move control of exactly the properties Evalia must guarantee.

## 4. Residency policy

Each engagement's `engagement.yaml` declares a policy. Illustrative form:

```yaml
residency:
  allowed_classes: [eu_api, self_hosted]   # any of: us_api, eu_api, self_hosted
  allowed_providers: [mistral, azure_openai_eu, local_vllm]   # optional allow-list
  provider_parent_jurisdiction: any         # or: eu_only
  zero_retention_required: true
```

Each profile declares its own residency class, region, the provider's parent jurisdiction, and whether zero-retention terms are in place. The router:

1. discards profiles that do not satisfy the policy;
2. picks the profile that the engagement names for the task, or the pack's default if that profile qualifies;
3. **refuses the call** (`refused_by_policy`) if none qualifies. It never falls back to another provider silently.

**Interpretation.** "EU-hosted" is not the same as "beyond US jurisdiction". A US-headquartered provider operating an EU region may still be subject to US legal process. Some clients will accept EU hosting by such a provider; others will require an EU-headquartered provider or self-hosting. The policy field `provider_parent_jurisdiction` exists so that this choice is explicit, and engagement terms should state which applies.

**Fact.** An AI coding assistant is also a model provider. [`CLAUDE.md`](../CLAUDE.md) therefore forbids coding sessions from reading the engagement data folder unless Victor authorises it for that engagement.

## 5. Structured output

1. The task's output schema is a Pydantic model. Its JSON Schema is sent to the provider.
2. The schema is enforced through the strongest mechanism available:
   - native schema-constrained output or tool use on hosted APIs;
   - grammar- or schema-guided decoding on self-hosted servers (vLLM and llama.cpp both offer forms of this; confirm the version in use);
   - otherwise, JSON mode plus validation.
3. The output is validated. On failure there is **one** repair attempt, with the validation error appended.
4. A second failure produces a finding with status `invalid_output`. The evaluator sees it. Nothing is dropped silently.
5. Model-independent guardrails then run on every response, whatever the provider: quote verification, threshold preservation and status sanity rules (for example, any status other than `not_addressed` or `not_applicable` requires at least one verified quote).

## 6. Prompts

- Prompts are pack files (`prompts/*.md.j2`), rendered with Jinja2 using strict undefined variables. **Fact:** DeepSeek's prompts fail under `str.format()` (probes P019 to P024).
- Each rendered prompt is hashed (SHA-256). The hash, the template path and the pack version enter the provenance record.
- **Recommendation.** No prompt may name a particular model or vendor. Where a task needs different wording for a weaker model, the variant is a separate template selected by the profile, so the difference stays visible.

## 7. Reproducibility and caching

- Temperature 0, and a fixed seed where the provider supports one. **Fact, widely documented by providers:** neither guarantees identical output across calls.
- Reproducibility therefore comes from **caching**. Each request is keyed by the hash of (adapter, endpoint, model identifier, parameters, rendered prompt, schema). The response is stored under that key in the engagement's `llm-cache` folder, inside the data folder because it contains tender text.
- Regenerating a report reuses the cache unless `--refresh` is passed. A refreshed run gets a new run record; the old one is kept.
- The model identifier recorded is the one the provider **returns**, not only the one requested, so that silent version changes are visible.

## 8. Evaluation harness

Each profile is measured on the same golden set before use on client data, and again whenever its model changes.

| Metric | Why | Proposed v1 threshold |
|---|---|---|
| Quote verification rate | Measures invented or misquoted evidence | ≥ 98% |
| Threshold preservation in requirement extraction | Prevents comparisons against the wrong figure | 100% (hard gate) |
| False-negative rate on mandatory requirements (synthetic gap injection) | The costly error: a missed failure | ≤ 2% |
| False-positive rate on `not_met` and `not_addressed` | Wastes evaluator time and erodes trust | ≤ 10% |
| Agreement with the evaluator's final status and score | Overall usefulness; EVA's own measure of value | Recorded; no threshold in v1 |
| Invalid-output rate after repair | Fitness of the profile for structured work | ≤ 1% |
| Cost and latency per submission | Commercial viability | Recorded |

The proposed thresholds are adapted from the transcript's targets (source lines 1395 to 1400). They are starting points to revise once data exists, not established benchmarks.

The golden set begins with synthetic packages, generated by script and visibly fictitious. It later adds historical packages for which a client has given written consent, kept in the data folder.

## 9. Self-hosted open-weight option

- **Serving.** An OpenAI-compatible server such as vLLM on a GPU machine the client or Evalia controls, or llama.cpp or Ollama for small-scale testing on a workstation.
- **Model selection criteria:** a licence that permits commercial use; enough context for long clauses plus retrieved evidence (as a working assumption, at least 32,000 tokens); reliable schema-guided output; and, where bids are not in English, quality in the bid language. **Recommendation:** shortlist candidates when the work starts, because open-weight releases move quickly. Choose by golden-set results, not by reputation.
- **Speculation.** On extraction and resolution tasks, smaller open-weight models will probably trail the strongest hosted models by a margin large enough to matter for false negatives. The harness exists to measure that margin. If it proves too large, self-hosting may suit screening tasks, or clients whose policy permits nothing else, with heavier evaluator review.
- Self-hosted profiles are recorded exactly like hosted ones, including model file hashes, so that runs remain reproducible.

## 10. Cost control

- Each task has a token budget, enforced before the call.
- The two-pass pattern from the transcript (a cheap model screens, a stronger model structures) is adopted only if the harness shows that it keeps recall while saving cost.
- Every run record reports estimated cost per submission. **Interpretation:** this is a discovery-test metric in its own right, because it bears on pricing.

## 11. Security

- API keys come from environment variables or the operating system's keychain, never from the repository or engagement files.
- Logs record hashes and metadata, not prompt or response text. Full text lives only in the engagement cache.
- No third-party telemetry is sent from the gateway.

## 12. Version-one subset

- Adapters: `openai_compatible` and `anthropic_messages`.
- Residency enforcement, provenance records and caching: complete.
- Tasks: `requirement.extract`, `compliance.resolve` and `qualification.extract`, each with a schema and a template in the construction pack.
- One self-hosted smoke test on the synthetic golden set, to prove the path works end to end and to measure the gap.
