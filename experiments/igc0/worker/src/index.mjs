/**
 * IGC-0 minimal inference Worker.
 * - No GitHub credential, storage, oracle, or validator on Cloudflare.
 * - No inference without a Worker-scoped secret.
 * - Exactly one Workers AI invocation per accepted POST.
 * - GitHub Actions owns source manifests, deterministic validation and audit PRs.
 */
export const MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast";
export const MAX_REQUEST_BYTES = 240_000;
export const CONTRACT = "igc0.worker.v1";
const STAGES = new Set(["IG"]); // M01-R2: no revision/contrast call at this endpoint
const ALLOWED_ROLES = new Set(["system", "user", "assistant"]);

// Output contract is a formatting aid, NOT the epistemic or dimensional validator.
export const GENERATION = Object.freeze({ temperature: 0.1, max_tokens: 4500, stream: false });
const ref = {
  type: "object", additionalProperties: false,
  properties: { source_id: { type: "string" }, sha256: { type: "string" } },
  required: ["source_id", "sha256"],
};
const refs = { type: "array", items: ref };
const stock = {
  type: "object", additionalProperties: false,
  properties: {
    id: { type: "string" }, unit: { type: "string" },
    initial: { type: ["number", "null"] },
    initial_label: { type: "string", enum: ["OBSERVADO", "CALIBRADO", "INFERIDO", "HIPÓTESIS", "DESCONOCIDO"] },
    initial_refs: refs,
  },
  required: ["id", "unit", "initial", "initial_label", "initial_refs"],
};
const pipe = {
  type: "object", additionalProperties: false,
  properties: {
    id: { type: "string" }, from: { type: "string" }, to: { type: "string" },
    unit_per_time: { type: "string" },
    capacity_source: { anyOf: [ref, { type: "null" }] },
    mechanism: { type: "string" }, evidence_refs: refs,
    epistemic: { type: "string", enum: ["OBSERVADO", "CALIBRADO", "INFERIDO", "HIPÓTESIS", "DESCONOCIDO"] },
  },
  required: ["id", "from", "to", "unit_per_time", "capacity_source", "mechanism", "evidence_refs", "epistemic"],
};
export const GRAPH_SCHEMA = {
  type: "object", additionalProperties: false,
  properties: {
    case_id: { type: "string", enum: ["M01"] },
    stocks: { type: "array", items: stock, minItems: 1 },
    pipes: { type: "array", items: pipe, minItems: 1 },
    informational_links: {
      type: "array", items: {
        type: "object", additionalProperties: false,
        properties: { from: { type: "string" }, to: { type: "string" },
          type: { type: "string", enum: ["information"] }, why: { type: "string" } },
        required: ["from", "to", "type", "why"],
      },
    },
    boundary: {
      type: "object", additionalProperties: false,
      properties: { inside: { type: "array", items: { type: "string" } },
        outside: { type: "array", items: { type: "string" } },
        possible_omissions: { type: "array", items: { type: "string" } } },
      required: ["inside", "outside", "possible_omissions"],
    },
    mechanism_checks: {
      type: "array", minItems: 4, maxItems: 4,
      items: {
        type: "object", additionalProperties: false,
        properties: {
          role: { type: "string", enum: ["shared_kitchen", "order_backlog", "delivery_dispatch", "payout_delay"] },
          status: { type: "string", enum: ["unknown", "hypothesis", "represented"] },
          linked_ids: { type: "array", items: { type: "string" } },
          evidence_refs: refs, explanation: { type: "string" },
        },
        required: ["role", "status", "linked_ids", "evidence_refs", "explanation"],
      },
    },
    unknowns: { type: "array", items: { type: "string" }, minItems: 1 },
  },
  required: ["case_id", "stocks", "pipes", "informational_links", "boundary", "mechanism_checks", "unknowns"],
};


function response(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

function authentication(request, env) {
  const configured = env?.IGC_API_KEY;
  if (typeof configured !== "string" || configured.length < 24) {
    return "UNCONFIGURED";
  }
  const value = request.headers.get("authorization") ?? "";
  if (!value.startsWith("Bearer ")) return "DENIED";
  const candidate = value.slice("Bearer ".length);
  if (candidate.length !== configured.length) return "DENIED";
  // A comparable-work loop; no secret contents are logged or returned.
  let difference = 0;
  for (let i = 0; i < configured.length; i += 1) {
    difference |= configured.charCodeAt(i) ^ candidate.charCodeAt(i);
  }
  return difference === 0 ? "OK" : "DENIED";
}

function validate(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) return false;
  if (body.schema_version !== CONTRACT || body.case_id !== "M01") return false;
  if (!STAGES.has(body.stage)) return false;
  if (typeof body.request_id !== "string" || !/^[a-zA-Z0-9_-]{8,96}$/.test(body.request_id)) return false;
  if (!Array.isArray(body.messages) || body.messages.length < 2 || body.messages.length > 6) return false;
  const roles = body.messages.map((m) => m?.role);
  if (roles[0] !== "system" || roles.at(-1) !== "user") return false;
  if (roles.some((role) => !ALLOWED_ROLES.has(role))) return false;
  return body.messages.every((message) =>
    message && typeof message.content === "string" &&
    message.content.length > 0 && message.content.length <= 210_000
  );
}

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (request.method === "GET" && path === "/health") {
      return response({ service: "igc0-review-lab", contract: CONTRACT, status: "ok", requires_authorization: true });
    }
    if (path !== "/v1/infer") return response({ error: "NOT_FOUND" }, 404);
    if (request.method !== "POST") return response({ error: "METHOD_NOT_ALLOWED" }, 405);

    const access = authentication(request, env);
    if (access === "UNCONFIGURED") return response({ error: "INFERENCE_DISABLED" }, 503);
    if (access !== "OK") return response({ error: "UNAUTHORIZED" }, 401);

    const contentLength = Number(request.headers.get("content-length") || "0");
    if (contentLength > MAX_REQUEST_BYTES) return response({ error: "REQUEST_TOO_LARGE" }, 413);
    if (!(request.headers.get("content-type") ?? "").toLowerCase().startsWith("application/json")) {
      return response({ error: "JSON_REQUIRED" }, 415);
    }

    let body;
    try {
      const raw = await request.text();
      if (new TextEncoder().encode(raw).length > MAX_REQUEST_BYTES) return response({ error: "REQUEST_TOO_LARGE" }, 413);
      body = JSON.parse(raw);
    } catch {
      return response({ error: "INVALID_JSON" }, 400);
    }
    if (!validate(body)) return response({ error: "INVALID_IGC_CONTRACT" }, 422);
    if (!env?.AI || typeof env.AI.run !== "function") return response({ error: "AI_BINDING_UNAVAILABLE" }, 503);

    try {
      const result = await env.AI.run(MODEL, {
        messages: body.messages,
        ...GENERATION,
        response_format: { type: "json_schema", json_schema: GRAPH_SCHEMA },
      });
      return response({
        schema_version: CONTRACT,
        case_id: body.case_id,
        stage: body.stage,
        request_id: body.request_id,
        model: MODEL,
        inference_config: { ...GENERATION, response_format_type: "json_schema", schema_version: "IGC0_GRAPH_V3" },
        provider_result: result,
      });
    } catch {
      // Never leak provider error details or request contents over a public endpoint.
      return response({ error: "AI_INFERENCE_FAILED", request_id: body.request_id }, 502);
    }
  },
};
