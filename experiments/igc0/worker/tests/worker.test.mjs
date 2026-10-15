import assert from "node:assert/strict";
import test from "node:test";
import worker, { MODEL, CONTRACT } from "../src/index.mjs";

const TOKEN = "igc0-testing-secret-only-1234567890";
const url = "https://example.workers.dev/v1/infer";
function input(overrides = {}) {
  return {
    schema_version: CONTRACT,
    case_id: "M01",
    stage: "IG",
    request_id: "test-request-001",
    messages: [
      { role: "system", content: "Propón un grafo SD y JSON, sin datos ocultos" },
      { role: "user", content: "Observaciones sintéticas de M01" },
    ],
    ...overrides,
  };
}
function request(body = input(), headers = {}) {
  return new Request(url, {
    method: "POST",
    headers: {
      authorization: `Bearer ${TOKEN}`,
      "content-type": "application/json",
      ...headers,
    },
    body: JSON.stringify(body),
  });
}
function fakeEnv() {
  const calls = [];
  return {
    calls,
    AI: {
      async run(model, payload) {
        calls.push({ model, payload });
        return { response: '{"case_id":"M01"}', usage: { total_tokens: 25 } };
      },
    },
    IGC_API_KEY: TOKEN,
  };
}
test("health returns static status without model calls", async () => {
  const env = fakeEnv();
  const res = await worker.fetch(new Request("https://example.workers.dev/health"), env);
  assert.equal(res.status, 200);
  assert.equal((await res.json()).status, "ok");
  assert.equal(env.calls.length, 0);
});
test("deployment without secret fails closed", async () => {
  const env = fakeEnv(); delete env.IGC_API_KEY;
  const res = await worker.fetch(request(), env);
  assert.equal(res.status, 503);
  assert.equal(env.calls.length, 0);
});
test("wrong authorization blocks requests", async () => {
  const env = fakeEnv();
  const res = await worker.fetch(request(input(), { authorization: "Bearer not-the-secret" }), env);
  assert.equal(res.status, 401);
  assert.equal(env.calls.length, 0);
});
test("malformed contract blocks requests", async () => {
  const env = fakeEnv();
  const res = await worker.fetch(request(input({ case_id: "M04" })), env);
  assert.equal(res.status, 422);
  assert.equal(env.calls.length, 0);
});
test("no automatic retry; one API call per authorized request", async () => {
  const env = fakeEnv();
  const res = await worker.fetch(request(), env);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.schema_version, CONTRACT);
  assert.equal(body.stage, "IG");
  assert.equal(body.provider_result.response, '{"case_id":"M01"}');
  assert.equal(env.calls.length, 1);
  assert.equal(env.calls[0].model, MODEL);
  assert.equal(env.calls[0].payload.stream, false);
});
test("stage REVIEW requires same authenticated contract", async () => {
  const env = fakeEnv();
  const res = await worker.fetch(request(input({ stage: "REVIEW" })), env);
  assert.equal(res.status, 200);
  assert.equal(env.calls.length, 1);
});
test("request body limit blocks inference", async () => {
  const env = fakeEnv();
  const res = await worker.fetch(request(input({ messages: [
    { role: "system", content: "test" },
    { role: "user", content: "x".repeat(240_001) },
  ] })), env);
  assert.equal(res.status, 413);
  assert.equal(env.calls.length, 0);
});
test("AI errors are sanitized and not retried", async () => {
  let calls = 0;
  const env = { IGC_API_KEY: TOKEN, AI: { async run() { calls++; throw Error("upstream sensitive info"); } } };
  const res = await worker.fetch(request(), env);
  assert.equal(res.status, 502);
  assert.ok(!(JSON.stringify(await res.json())).includes("sensitive"));
  assert.equal(calls, 1);
});
test("never provides a GitHub or Cloudflare credential binding to the caller", async () => {
  const env = fakeEnv(); env.CLOUDFLARE_API_TOKEN = "hidden";
  env.GITHUB_TOKEN = "secret";
  const res = await worker.fetch(request(), env);
  const json = await res.text();
  assert.ok(!json.includes("hidden"));
  assert.ok(!json.includes("secret"));
});
