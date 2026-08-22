# Authenticate to Gmail via OAuth2 instead of an App Password

ADR-0001 established SMTP delivery through a dedicated Gmail sender account. The original plan authenticated to that account with a static App Password. App Passwords turned out to be gated on brand-new Google accounts — the App Passwords page itself returned a 400 error, with no documented waiting period. Confirmed via a working prototype (`prototype/gmail-oauth-smtp` branch) that OAuth2 is not subject to the same restriction: a full consent-to-delivery round trip succeeded on the same account.

Considered and rejected: falling back to the operator's personal Gmail account (works today, but breaks the deliberate separation from ADR-0001 — this server holds a live credential and is reachable by anyone who finds its URL, so the sender should stay a low-stakes dedicated account, not a personal one).

## How authorization actually happens

The deployed server hosts the OAuth flow itself (`/oauth/start`, `/oauth/callback`), rather than requiring a setup script run on the NAS over SSH — this needed the Google OAuth client to be **Web application** type (a real HTTPS redirect URI) rather than **Desktop app** type (restricted to loopback addresses only, a hard Google restriction, not a preference). `send_book` checks for a working credential before sending; if none exists yet, or a previously-working one has gone stale, it returns the `/oauth/start` link instead of failing outright — the same recovery path serves both first-time setup and later re-authorization.

## Consequences

- No setup-token secret needed to protect `/oauth/start`/`/oauth/callback`, despite them being unauthenticated, public endpoints. Two independent protections cover it: Google's own Test User allowlist (the OAuth app stays in Testing mode; only the specific listed sender account can complete consent, regardless of who reaches the URL) and the route going permanently inert once a refresh token already exists.
- The old health check (proactive, monthly, SMTP-login test) was dropped rather than adapted. It existed because Amazon's OAuth failures were silent; here, `send_book` self-diagnoses and self-recovers on the next real use, making a separate monitor redundant.
- Runtime dependencies grow from one (`fastmcp`) to three (`fastmcp`, `google-auth`, `google-auth-oauthlib`) — accepted deliberately in exchange for not hand-rolling the OAuth2 token exchange and refresh logic.
