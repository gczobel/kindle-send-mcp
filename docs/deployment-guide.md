# Deploying kindle-send-mcp

This guide covers the one-time, human-run steps to deploy kindle-send-mcp and make the first send work. The code, tests, and docs live in the repo and CI covers them. You need a Resend account, a domain you control on Cloudflare, the Calibre library reachable from the NAS, and a way to run containers on it.

## What you need before you start

- A Resend account. The free tier (3,000 emails/month, 100/day) needs no credit card.
- A domain you control. The sender address lives on a subdomain of it, for example `mail.<your-zone>`.
- The Calibre library path on the NAS, mounted read-only into the container.
- A way to run containers on the NAS. Docker Compose, Portainer, or whatever you already use for the other services.

## Set up Resend

1. Sign up at resend.com and add your sending domain. The four DNS records you need are in `docs/adr/0003-resend-instead-of-gmail.md`: two CNAMEs, the DKIM TXT record, and `_dmarc`. Add them in Cloudflare.
2. Keep the CNAMEs DNS-only (grey cloud). Proxying them breaks Resend's domain verification.
3. Wait until the domain shows Verified in the Resend dashboard. The records resolve correctly, but propagation can take minutes to hours.
4. Create an API key (API Keys -> Create API Key) with send permission. This is `RESEND_API_KEY`. A key restricted to sending works fine; it cannot read domain status, which is expected.

## Choose the sender address (RESEND_FROM)

`RESEND_FROM` is an address you pick. Nothing creates it for you. Any address on your verified sending domain works, for example `kindle@mail.<your-zone>` or `books@mail.<your-zone>`. No mailbox has to exist and nobody reads it; Resend sends from it because the domain is verified.

Pick one string and use it in exactly two places:

- `RESEND_FROM` in the server environment,
- the Approved Personal Document E-mail List in Amazon.

The two must match character for character. If you change the address later, update both places again.

## Approve the sender in Amazon

In Amazon, go to Manage Your Content and Devices, then Preferences, then Personal Document Settings, and add the address you chose as `RESEND_FROM` to the Approved Personal Document E-mail List. Skip this and every send returns "sent" while Amazon silently drops the mail. There is no bounce and no delivery confirmation anywhere in the chain.

## Configure the server environment

Deploy the container with your usual tool and set these environment variables on the `kindle-send-mcp` service:

- Add `RESEND_API_KEY` and `RESEND_FROM` (the address from the previous section).
- Remove `SENDER_EMAIL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `PUBLIC_OAUTH_CALLBACK_URL`. The server no longer uses them.
- Keep `CALIBRE_LIBRARY_PATH`, `CALIBRE_DB_FILENAME`, `STATE_DIR`, `HTTP_PORT`.

Two things to be careful about.

Many deployment tools replace the whole environment list when you update a stack, not just the fields you change. If yours does, re-pass every other variable verbatim: `TUNNEL_TOKEN` (from the Cloudflare dashboard if you lost it), `CONFIG_BASE_FOLDER`, and anything else the compose file references. Miss one and that service breaks on redeploy.

Env values are often hidden from scripts and automation. Edit where you can see the current values, or have them ready from your own records before you save.

Redeploy with an image pull. The container runs `ghcr.io/gczobel/kindle-send-mcp:latest`, and a plain redeploy may reuse the cached old image. Pull explicitly, then check that the app container was recreated and that the tunnel and companion containers still run.

## Register devices

Find each Kindle's `@kindle.com` address in Amazon, under Personal Document Settings, Send-to-Kindle E-Mail Settings. Register it with the `add_device` tool (nickname plus address). No file editing.

## Connect an MCP client

Connect the client to the MCP endpoint. The tools are `list_devices`, `add_device`, `send_book`.

After any redeploy, reconnect the client. A session from before the redeploy holds a session id the new container does not know; the next call fails with `400 Bad Request: Missing session ID`, which clients show as a generic "Error occurred during tool execution". The server logs only the 400. Restart the client or toggle the server connection and retry. This is also in the README under Operations.

## Test the first send

Call `send_book` with a real book id and a registered device. A "sent" response means Resend accepted the message. It does not mean the Kindle got it. Check the device, then the Resend dashboard if you want proof the message went out.
