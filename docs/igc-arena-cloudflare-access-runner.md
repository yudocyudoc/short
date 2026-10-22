# Cloudflare Access for the IGC Arena runner

The GitHub runner sends two independent forms of authentication to the Workbench:

1. Cloudflare Access service-token headers authenticate GitHub Actions at the edge.
2. The existing timestamped HMAC authenticates each runner request to the Worker. The snapshot SHA-256 remains checked before the runner evaluates or reports a result.

The Access credentials do not replace the HMAC or the immutable snapshot hash.
The runner rejects HTTP redirects for both snapshot reads and callbacks, so it does not forward the Access service-token headers to a redirected origin.

## GitHub Actions secrets

Create these repository Actions secrets for `yudocyudoc/short`:

| Secret | Value |
| --- | --- |
| `CF_ACCESS_CLIENT_ID` | Client ID for the dedicated GitHub runner service token |
| `CF_ACCESS_CLIENT_SECRET` | Client Secret for that same service token |

The workflow maps the secrets to environment variables with the same names. Keep `IGC_RUNNER_HMAC_SECRET` as a separate existing secret, and keep `IGC_SERVICE_ORIGIN` as the repository variable. Do not put any of these values in the repository or workflow file.

## Cloudflare Zero Trust setup

Do this in the Cloudflare dashboard; this repository does not create or change Access policies.

1. Keep the existing `cei-igc-workbench-v02 - Cloudflare Workers` application protecting the full Worker hostname and retain its current researcher `Allow` policy.
2. In **Zero Trust → Access controls → Service credentials → Service Tokens**, create one token named for the GitHub runner. Choose an expiry that fits the rotation policy and save its Client ID and Client Secret directly as the two GitHub Actions secrets above. Cloudflare displays the Client Secret only at creation.
3. Open the existing `cei-igc-workbench-v02 - Cloudflare Workers` Access application and add a policy with action **Service Auth**, Include selector **Service Token**, and only the dedicated runner token. Do not select **Any Access Service Token**, add `Everyone`, or create a public bypass. Cloudflare specifically advises adding the policy to the existing Worker application rather than creating a second Access app for the same Worker.
4. Leave the current researcher `Allow` policy unchanged. Cloudflare evaluates `Service Auth` before `Allow`; the added policy therefore admits the dedicated machine credential while the existing identity policy continues to admit the researcher.
5. Confirm the policy decision in Access authentication logs before dispatching a probe. A request to `/api/runner/*` with the service token but without valid HMAC should pass the Access edge and still receive the Workbench's HMAC `401`. A request without the service-token headers should be denied at Access before reaching the Worker.
6. Rotate or revoke the dedicated token through **Service Tokens** if it is exposed or no longer needed, and update both GitHub secrets together.

### Scope boundary

The current Worker-level Access application protects the Worker as a whole. Its Service Auth policy is not path-scoped: a valid service token can pass Access for other Worker URLs too. The runner sends these credentials only to the two `/api/runner/jobs/...` endpoints. The Workbench still checks HMAC on those routes and validates a human Access JWT on user API routes, but the token can reach non-sensitive public routes/assets such as `/api/health` at the Access layer. If the service token must be cryptographically restricted to `/api/runner/*`, split the runner API onto its own Worker/hostname before enabling this policy; do not add a competing Access application for the same Worker.

Cloudflare documents service-token authentication using `CF-Access-Client-Id` and `CF-Access-Client-Secret`, and the `Service Auth` action with an Include rule for a service token. Access evaluates `Service Auth` before `Allow`; preserving the current user policy keeps interactive researcher access available.

References: [Protect a Worker with Access](https://developers.cloudflare.com/workers/configuration/cloudflare-access/), [Service tokens](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/), [Authenticate a service using a service token](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/common-policies/), [Worker Access policy guidance](https://developers.cloudflare.com/workers/local-development/).
