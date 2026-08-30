# kindle-send-mcp

An MCP server that lets an AI agent send books from a Calibre library
directly to a Kindle device, via Amazon's own [Send to Kindle by
email](https://www.amazon.com/gp/sendtokindle) feature — no OAuth session,
no reverse-engineered API. Delivery goes through the [Resend](https://resend.com)
email API, see
[docs/adr/0003-resend-instead-of-gmail.md](docs/adr/0003-resend-instead-of-gmail.md)
for why.

## What this is, and isn't

- **Read access** to a Calibre library's `metadata.db` and book files, to
  resolve a book by id to a real file to send.
- **Send access** via the Resend API, to any device you've registered by
  nickname and `@kindle.com` address.
- No metadata editing, no library writes, no Amazon account access at all.

## Reliability posture

Amazon's Send-to-Kindle email service gives **no delivery confirmation**
and **silently discards** mail from senders not on the account's Approved
Personal Document Email List — no bounce, no error. A "sent" status from
this server means the message was handed to the Resend API successfully,
not that the Kindle received it. Resend's own logs are the audit trail.
See [CONTEXT.md](CONTEXT.md) for the exact vocabulary this server uses
around delivery.

## Setting up your own instance

Sender authentication is a Resend API key, not SMTP credentials or OAuth —
nothing expires and nothing needs re-authorizing. See
[docs/adr/0003-resend-instead-of-gmail.md](docs/adr/0003-resend-instead-of-gmail.md)
for why the Gmail OAuth path was replaced.

### 1. Create a Resend account and verify a sending domain

1. Sign up at [resend.com](https://resend.com) and generate an API key
   (API Keys -> Create API Key). It goes into the `RESEND_API_KEY`
   environment variable.
2. Add and verify a sending domain. The records for your sending
   domain are documented in
   [docs/adr/0003-resend-instead-of-gmail.md](docs/adr/0003-resend-instead-of-gmail.md).
   The From address the server sends from is a subdomain address
   (e.g. `kindle@<your-sending-domain>`), so the domain must show
   **Verified** in the Resend dashboard.

### 2. Approve that sender in your Amazon account

Manage Your Content and Devices -> Preferences -> Personal Document
Settings -> Approved Personal Document E-mail List -> add the From
address (e.g. `kindle@<your-sending-domain>`). **Skip this and
every send vanishes silently** — Amazon gives no bounce.

### 3. Configure the server

- `RESEND_API_KEY` — required. Missing at send time raises a clear error.
- `RESEND_FROM` (e.g. `kindle@<your-sending-domain>`) — the sender
  address; required, and must be on Amazon's approved list from step 2.
- `STATE_DIR` (default `/state`) — where `devices.json` and
  `default_device.json` are stored. Mount a host directory here,
  read-write.
- `CALIBRE_LIBRARY_PATH` (default `/books`) — your Calibre library,
  mounted read-only.

### 4. Register your devices

Find each device's `@kindle.com` address in Manage Your Content and
Devices -> Preferences -> Personal Document Settings -> Send-to-Kindle
E-Mail Settings, then use the `add_device` tool (nickname + address) --
no file editing needed.

### Example `docker run`

```bash
docker run -d \
  -e RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxx \
  -e RESEND_FROM=kindle@<your-sending-domain> \
  -v /path/to/your/state-dir:/state \
  -v /path/to/your/calibre/library:/books:ro \
  -p 9002:9002 \
  ghcr.io/gczobel/kindle-send-mcp:latest
```

## Tools

- `list_devices()` — lists devices registered with this server.
- `add_device(nickname, email)` — registers a device by nickname and its
  `@kindle.com` address.
- `send_book(book_id, target_device_nickname=None)` — sends the book
  with that id (looked up in `metadata.db`) to a device. If no device
  has been chosen yet (no default set, no explicit target given),
  returns the device list instead of guessing which one you meant.
  Sends directly — there is no authorization step.
