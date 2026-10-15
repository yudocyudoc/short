# IGC-0 — M01-R2 Llama, preparation and gate (2026-10-15)

**Status:** WORKER DEPLOYED (version `4ac1bd77-ea85-4f51-aae9-fab8b564606a`) / NO R2 INFERENCE EXECUTED.

## R1 diagnosis (source: PR #2 / run 38692953137-1)

- The deployed Worker source path is `experiments/igc0/worker/src/index.mjs`.
- Source at the R1 development commit explicitly requested `max_tokens: 4500`, `temperature: 0.1`, `stream: false`; the GitHub client request did not itself contain these Worker-side parameters.
- The R1 archived response reports 18,377 prompt tokens and 2,128 completion tokens. It contains one completed `<think>...</think>` segment and an incomplete JSON body; the final bytes end inside a pipe property.
- The archived provider result has `response` and `usage`, **without a finish_reason**. Whether the provider stopped due to an internal limit, backend termination, token accounting or another reason is **not identifiable** from the evidence. Do not report a known root cause.
- M01-R1 remains `FORMAT_REJECT`, with one inference and no review. Existing raw artifacts and SHA-256 hashes must not be rewritten.

## R2 experimental choice

- Model: `@cf/meta/llama-3.3-70b-instruct-fp8-fast` (Cloudflare Workers AI).
- Exactly **one** authorized IG-stage call. No REVIEW, C, retry, automatic repair, projection, or second model.
- Keep the same public M01 input and exact `ig_graph_v3.md` prompt. Keep `graph_gate` and all existing provenance and conservation checks unchanged.
- Use Cloudflare `response_format: {type:"json_schema", json_schema: GRAPH_SCHEMA}` for the existing **seven IG fields only**. This constrains structure but does **not** validate causal correctness or force chain-of-thought.
- Preserve unknown initial values as `null`, with `DESCONOCIDO` and [] references where appropriate. A valid JSON object can still be rejected by the deterministic graph gate.
- Keep `max_tokens: 4500`, `temperature: 0.1`, `stream: false`; the Worker now returns non-secret effective generation settings as `inference_config`. The input footprint and the 24k-token Llama context should be reviewed before any billed run.
- If Cloudflare cannot satisfy the schema, archive the provider/transport rejection; **do not retry or relax the schema in the same R2 run**.

## Preflight and authorization

1. Confirm Worker JS syntax and its offline tests, then Python analyst unit tests; prepare the public input.
2. Review branch diff and verify no oracle/model-generator material is sent to the LLM.
3. **Completed 2026-10-15:** authorized Worker deployment, confirmed by Wrangler at https://github.com/yudocyudoc/short/actions/runs/38706537956. The temporary one-shot trigger was removed; manual-only deployment is restored.
4. Once deployment and the protected endpoint are checked, explicitly authorize the **single inference** using `igc0-worker-audit.yml`, branch `experiment/igc0-m01-r2-llama`, input `confirm_inference=RUN_M01_R2_IG_ONCE`.
5. Archive and review the complete GitHub Actions artifact; workflow does not automatically push a PR because earlier GitHub workflow permissions made that archival route fail.
6. Judge separately: (a) transport/form, (b) graph gate, (c) actual SD structural quality and evidential honesty. An IG graph accepted by code is **not** verified ground truth.

## Cost guard and known risk

Cloudflare's published price for Llama 3.3 FP8 Fast is US$0.293 / 1M input tokens and US$2.253 / 1M output tokens. At the R1 prompt-token count and the 4,500-token output ceiling, the illustrative token charge is ~US$0.0155, **not a guaranteed run quote**: Llama tokenization, schema overhead, actual completion, and any platform fees may differ.

Llama context is 24,000 tokens; DeepSeek R1 Distill context is larger. The same M01 packet could therefore fail at inference-time if the effective tokenized prompt plus schema plus output reservation exceed the context window. This must be treated as a transport/capacity limit, not a causal-model failure.

Official docs:
- https://developers.cloudflare.com/workers-ai/models/llama-3.3-70b-instruct-fp8-fast/
- https://developers.cloudflare.com/workers-ai/features/json-mode/
