# Send via the Resend API instead of Gmail SMTP

ADR-0002 established delivery through the operator's real Gmail account, authenticated with OAuth2 (XOAUTH2) over SMTP. That path has a structural flaw for an **unattended** sender: Google OAuth apps still in **Testing** status issue refresh tokens that expire after **7 days** — a guaranteed recurring break, since nothing re-runs the consent flow between sends. Moving the app to **Production** status requires Google's multi-day verification process, which was not an option. The server-hosted `/oauth/start` + `/oauth/callback` flow also sat behind the operator's auth proxy (`mcp-auth-proxy`), which rejects anything without its bearer token — in practice the callback got 401'd by that gate. (An earlier task brief mentioned a Cloudflare `/oauth/*` bypass rule. A path rule on the tunnel's `kindle-mcp` public hostname does exist; whether an Access bypass policy also does was never checked. It is not relied on here, and it was not inert either, see the correction at the end of this ADR. The `mcp-auth-proxy` in front of the server is the auth gate that actually matters.)

## Decision

Replace Gmail SMTP with **Resend**, a plain transactional email API. Resend's free tier (3,000 emails/month, 100/day) needs no credit card, the API is a single authenticated REST call, and Amazon's Approved Personal Document E-mail List accepts any sender address — so a dedicated, never-expiring sending identity works.

Sending domain: a subdomain of the operator's existing Cloudflare zone (e.g. `mail.<your-zone>`). The four records below are present in Cloudflare:

| Type  | Name                     | Value                               |
|-------|--------------------------|-------------------------------------|
| CNAME | `rsend.mail`             | `rsend-apne1.forge.rmta.net`        |
| CNAME | `send.mail`              | `send.forge.rmta.net`               |
| TXT   | `resend._domainkey.mail` | Resend's DKIM public key            |
| TXT   | `_dmarc.mail`            | `v=DMARC1; p=none;`                 |

Configuration is two environment variables, matching the repo's `os.environ.get` convention:

- `RESEND_API_KEY` — required. Missing at send time raises a clear error rather than failing at startup.
- `RESEND_FROM` — the From address (e.g. `kindle@mail.<your-zone>`); required, with a clear send-time error if unset.

## Cloudflare gotchas (from setup)

- The two CNAMEs must stay **DNS-only (grey cloud)**. Proxying through Cloudflare breaks Resend's domain verification.
- The TXT records live on the **`mail` subdomain** (`resend._domainkey.mail`, `_dmarc.mail`), not on the zone apex — easy to add at the wrong level from the zone editor.
- Resend's dashboard shows **Pending** until the records propagate (minutes to hours); verification is a dashboard step, not something the server does.

## Consequences

- No OAuth, no refresh token, no re-authorization — unattended sends keep working indefinitely.
- The Gmail path is **deleted**, not left dormant: `gmail_oauth.py`, `token_store.py`, `smtp_sender.py`, the `/oauth/start` and `/oauth/callback` routes, and the `needs_authorization` contract in `send_book` are all gone, along with the `google-auth`/`google-auth-oauthlib` dependencies. Any Cloudflare path rule for `/oauth/*` is inert as far as this server goes, since the routes are gone, but it must still be deleted from the tunnel: it hijacks MCP OAuth discovery, see the correction below.
- The sender address (e.g. `kindle@mail.<your-zone>`) **must** be added to the Amazon account's Approved Personal Document E-mail List, or Amazon silently discards every send (unchanged silent-failure behavior from ADR-0001).
- The BCC audit trail is dropped. The old SMTP sender BCC'd its own inbox on every send; the Resend From address is not a human inbox, and Resend keeps its own logs and dashboard.
- Still no delivery confirmation from Amazon — "sent" means the Resend API accepted the message, not that the Kindle received it.
- Runtime dependency change: `google-auth`/`google-auth-oauthlib` out, `resend` in.

## Correction: the `/oauth/*` rule broke MCP OAuth (2026-09-20)

Two claims above were wrong, and they were wrong in the expensive direction. Both said the `/oauth/*` rule was never verified to exist and, if it did, was inert. Corrected in place rather than rewritten, so the record shows what was believed when the decision was made.

The rule is an **ingress path rule** on the `kindle-mcp` public hostname:

```
{"hostname": "kindle-mcp.<your-zone>", "path": "/oauth/*", "service": "http://kindle-send-mcp:9002"}
{"hostname": "kindle-mcp.<your-zone>", "service": "http://kindle-mcp-auth:9011"}
```

The path rule is listed before the hostname's catch-all, so it wins wherever it matches.

What made it worse than a dead route is how cloudflared reads that field. `ingress/rule.go` compiles `path` with `regexp.Compile` and tests it with `Regexp.MatchString`, which is **unanchored**. `/oauth/*` is therefore not a glob over an `/oauth/` subtree, it matches any path containing the substring `/oauth`. Every OAuth-named discovery URL contains it, which is enough to break discovery. The OIDC fallback, `/.well-known/openid-configuration`, is the only one this rule does not catch.

| Request | Routed to | Response |
|---|---|---|
| `GET /.well-known/oauth-protected-resource/mcp` | this server | `404 Not Found` |
| `GET /.well-known/oauth-protected-resource` | this server | `404 Not Found` |
| `GET /.well-known/oauth-authorization-server` | this server | `404 Not Found` |
| `POST /.idp/token` (no `/oauth` in the path) | auth proxy | `401 invalid_client` |

So the endpoint that a client needs in order to re-authenticate answered 404 from FastMCP, which has had no `/oauth` routes since this ADR, while the token endpoint answered correctly from the proxy. A client that cannot complete discovery cannot register itself either, so a client that had lost its registration could not recover at all. The 404s appeared in this server's own log, which is what made it look like a server bug.

The rule was removed on 2026-09-20 and discovery on that hostname returned to `200`. The generalizable part is not specific to this server: **do not put a `path` on an MCP public hostname whose regex also matches `/.well-known/oauth-*`**, because the auth proxy is the only thing behind that hostname that can answer those requests.
