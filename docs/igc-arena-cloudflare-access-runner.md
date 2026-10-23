# Cloudflare Access for the IGC Arena runner

The Workbench uses Cloudflare Access for human-facing routes. The Worker Access application has a path override that leaves only `/api/runner/*` reachable without an Access login, so GitHub Actions can call the runner API directly.

Those endpoints still require the timestamped HMAC signature. The Worker validates the signature, method, path, request-body SHA-256, and timestamp before processing the snapshot or callback. The runner also verifies the immutable snapshot SHA-256. These checks are independent of Cloudflare Access.

## GitHub Actions configuration

The workflow needs:

- Repository variable `IGC_SERVICE_ORIGIN`, set to the Workbench Worker origin.
- Repository secret `IGC_RUNNER_HMAC_SECRET`, matching the Worker's HMAC secret.

The runner does not need `CF_ACCESS_CLIENT_ID` or `CF_ACCESS_CLIENT_SECRET`. The workflow must not send Cloudflare Access service-token headers to the public runner path.

The workflow uploads `igc-arena-probe-artifact.json` even when the callback step fails. The authenticated Workbench polls the completed run, retrieves only the artifact named for its `job_id`, and imports it after checking the workflow run, snapshot hash, result hash, and a separate HMAC signature. The Worker's `GITHUB_TOKEN` therefore needs read access to Actions artifacts (`Actions: read` for a fine-grained token). The download redirect is fetched without the GitHub Authorization header. The existing signed callback remains available as the fast path.

## Cloudflare configuration

Keep the researcher `Allow` policy and the Access application protecting the Workbench. The only exception is the existing path override for `/api/runner/*`. Do not add a hostname-wide bypass or change the researcher policy.

## Scope

This lowers friction for GitHub Actions by removing the separate Cloudflare service-token requirement. The runner API is reachable at the edge, while HMAC remains required inside the Worker. All other Workbench routes remain behind Cloudflare Access.

References: [Protect a Worker with Access](https://developers.cloudflare.com/workers/configuration/cloudflare-access/), [Cloudflare Access policies](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/).
