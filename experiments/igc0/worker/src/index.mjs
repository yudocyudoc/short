/**
 * IGC-0 minimal inference Worker.
 * - No GitHub credential, storage, oracle, or validator on Cloudflare.
 * - No inference without a Worker-scoped secret.
 * - Exactly one Workers AI invocation per accepted POST.
 * - GitHub Actions owns source manifests, deterministic validation and audit PRs.
 */
export const MODEL = "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b";
export const MAX_REQUEST_BYTES = 240_000;
export const CONTRACT = "igc0.worker.v1";
const STAGES = new Set(["IG", "REVIEW", "C"]);
const ALLOWED_ROLES = new Set(["system", "user", "assistant"]);

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
        temperature: 0.1,
        max_tokens: 4500,
        stream: false,
      });
      return response({
        schema_version: CONTRACT,
        case_id: body.case_id,
        stage: body.stage,
        request_id: body.request_id,
        model: MODEL,
        provider_result: result,
      });
    } catch {
      // Never leak provider error details or request contents over a public endpoint.
      return response({ error: "AI_INFERENCE_FAILED", request_id: body.request_id }, 502);
    }
  },
};
