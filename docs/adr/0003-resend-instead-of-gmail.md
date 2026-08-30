# Send via the Resend API instead of Gmail SMTP

ADR-0002 established delivery through the operator's real Gmail account, authenticated with OAuth2 (XOAUTH2) over SMTP. That path has a structural flaw for an **unattended** sender: Google OAuth apps still in **Testing** status issue refresh tokens that expire after **7 days** — a guaranteed recurring break, since nothing re-runs the consent flow between sends. Moving the app to **Production** status requires Google's multi-day verification process, which was not an option. The server-hosted `/oauth/start` + `/oauth/callback` flow also sat behind the operator's auth proxy (`mcp-auth-proxy`), which rejects anything without its bearer token — in practice the callback got 401'd by that gate. (An earlier task brief mentioned a Cloudflare `/oauth/*` bypass rule; it was never verified to exist and is not relied on here. The `mcp-auth-proxy` in front of the server is the auth gate that actually matters.)

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
- The Gmail path is **deleted**, not left dormant: `gmail_oauth.py`, `token_store.py`, `smtp_sender.py`, the `/oauth/start` and `/oauth/callback` routes, and the `needs_authorization` contract in `send_book` are all gone, along with the `google-auth`/`google-auth-oauthlib` dependencies. Any Cloudflare bypass rule for `/oauth/*` — if one exists; it was never verified — is now inert and can be deleted.
- The sender address (e.g. `kindle@mail.<your-zone>`) **must** be added to the Amazon account's Approved Personal Document E-mail List, or Amazon silently discards every send (unchanged silent-failure behavior from ADR-0001).
- The BCC audit trail is dropped. The old SMTP sender BCC'd its own inbox on every send; the Resend From address is not a human inbox, and Resend keeps its own logs and dashboard.
- Still no delivery confirmation from Amazon — "sent" means the Resend API accepted the message, not that the Kindle received it.
- Runtime dependency change: `google-auth`/`google-auth-oauthlib` out, `resend` in.
