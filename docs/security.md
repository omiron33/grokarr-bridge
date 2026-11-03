# Permissions and exposure

## Trust boundary

App keys stay in private local bridge state or mounted app config. They are used for direct requests to owner-configured private endpoints, never as a bot credential. The MCP pairing token is the only bridge credential: it is generated with 256 random bits, not logged or exposed by tools, and entered through a connector's secure credential UI. Protect backups/state as secrets. The pairing UI/credential store belongs to the MCP client; this package cannot create it for a third-party hosted bot.

Every request needs `Authorization: Bearer <pairing-secret>`. Tokens never go in URLs. The endpoint is `/mcp` (Streamable HTTP, stateless JSON responses); `/healthz` also requires bearer authentication. Exact allowed Host/Origin values prevent DNS rebinding and browser cross-origin calls. Cookies are not accepted as bridge authentication. No wildcard CORS, no arbitrary outbound URL tool, no redirect following, no environment HTTP proxy, no shell/Docker socket tools. Destinations must resolve to private/loopback/Tailscale addresses, excluding link-local metadata services, multicast and unspecified addresses. Local DNS/network and the explicitly configured apps are trusted; do not configure an attacker-controlled DNS name (this is not an Internet URL fetch sandbox).

Remote tools cannot update consent/config/secrets. MCP and CLI use the same schema validation and dispatcher. Read-only tools never invoke app mutations even when a vendor uses POST JSON-RPC for reads. qBittorrent/Deluge authentication creates app sessions but does not alter media/config. Unidentified services receive no app credentials during discovery. Config adoption happens locally.

Ordinary single-ID pause/resume, one-title registration, one movie/one TV season request and one-entity refresh need **autopilot**. Adding uses an existing root-folder ID, never a caller-supplied path, and never requests a missing-content search. Plex section refresh, delete, bulk/all, path/root config, network, VPN, container and unknown mutation routes always return `confirm_required` without execution. This release has no remote confirmation token or `force` flag: the owner reviews/executes those operations locally in the app UI. Avoids letting a bot approve its own request. Unknown read routes return `not_allowed`.

If an app times out after a write, state is uncertain: inspect the app before retrying. The bridge never retries writes automatically. Transmission's first 409 session-token handshake is the protocol's rejected request, not a blind mutation retry. Application read tools can return library/session data and untrusted titles; the bot must treat all content as data, never instructions. Only grant access to a bot you trust with those results.

## Tailscale (preferred for a client on your tailnet)

1. Install/sign in to Tailscale on the bridge host and client. Restrict tailnet grants/ACLs to the intended client/service.
2. Register the exact assigned DNS host locally: `grokarr-bridge init --allow-host nas.YOUR-TAILNET.ts.net`; Docker: prefix with `docker exec grokarr-bridge`. Restart only the bridge container/process to reload HTTP host validation.
3. On the host, choose a dedicated HTTPS port so an existing Serve route isn't overwritten:
   `tailscale serve --bg --https=18765 http://127.0.0.1:8765`
4. Connector URL: `https://nas.YOUR-TAILNET.ts.net:18765/mcp`. Enter the bridge secret in its secure bearer field. Add exact Origin only if your browser-based connector sends one.
5. Check that an unauthenticated request is 401, authenticated initialize works, `bridge_status.autopilot` is false, and only intended apps are present.

**Do not use Funnel.** A publicly hosted GrokArr client cannot reach a private tailnet unless its execution host is actually on that tailnet; a URL alone cannot fix that. In that case use an Access-protected tunnel or the local CLI. [Tailscale Serve reference](https://tailscale.com/docs/reference/tailscale-cli/serve).

## Cloudflare Tunnel + Access

1. Create a named Cloudflare Tunnel on the bridge host. Route a chosen hostname only to `http://127.0.0.1:8765`, with a catch-all 404. If cloudflared runs in another container, join an isolated shared network and route to `http://grokarr-bridge:8765`; do not publish a host wildcard port.
2. **Before enabling the public hostname**, create a self-hosted Access application for that entire hostname/path. Require an explicit user or Service Auth policy; no bypass policy. Set appropriate short credential expiry.
3. For a machine client, provision a Cloudflare service token in its secure credential manager. It sends `CF-Access-Client-Id` and `CF-Access-Client-Secret` in addition to bridge `Authorization: Bearer ...`. Alternatively use Access's supported OAuth flow if the client implements it. Do not replace the bridge bearer header with a Cloudflare token.
4. Locally `init --allow-host bridge.example.com`, restart only the bridge, and set connector URL `https://bridge.example.com/mcp`. No secrets go in chat. Test Access rejection without Access credentials and bridge 401 with Access credentials but without pairing. Only then test full authenticated MCP.
5. If the MCP client cannot securely provide **both** Access authentication and the bridge bearer token (or a supported OAuth equivalent), do not expose an unprotected fallback. Use Tailscale/local CLI until that client can authenticate correctly.

See [Cloudflare service-token documentation](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/). This bridge implements a static local bearer token, not its own OAuth authorization server. No Tailscale/tunnel/access changes were made during the Shane test.

## Limits

No guarantee of credential secrecy against root, compromised apps, malicious local code, untrusted DNS/network owners or a compromised bridge process. Upstream responses are bounded and scrubbed, credential/config fields removed, and opaque exception strings withheld. This is defense in depth, not a replacement for endpoint ACLs and backups. No request/response/access logs are emitted by the bridge. Secrets sent to app APIs using query-only protocols (SABnzbd/Tautulli) can still be visible to that app's own HTTP/proxy logging; keep that connection private and configure upstream logs appropriately.
