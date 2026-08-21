# kindle-send-mcp

An MCP server that lets an AI agent send books from a Calibre library
directly to a Kindle device, via Amazon's own [Send to Kindle by
email](https://www.amazon.com/gp/sendtokindle) feature — no OAuth session,
no reverse-engineered API. See
[docs/adr/0001-smtp-delivery-instead-of-amazon-oauth.md](docs/adr/0001-smtp-delivery-instead-of-amazon-oauth.md)
for why.

## What this is, and isn't

- **Read access** to a Calibre library's `metadata.db` and book files, to
  resolve a book by id to a real file to send.
- **Send access** via SMTP, to any device you've registered by nickname
  and `@kindle.com` address.
- No metadata editing, no library writes, no Amazon account access at all.

## Reliability posture

Amazon's Send-to-Kindle email service gives **no delivery confirmation**
and **silently discards** mail from senders not on the account's Approved
Personal Document Email List — no bounce, no error. A "sent" status from
this server means the message was handed off to SMTP successfully, not
that the Kindle received it. Every send is BCC'd to the sender's own
inbox as an audit trail. See [CONTEXT.md](CONTEXT.md) for the exact
vocabulary this server uses around delivery.

## Setting up your own instance

### 1. Create a dedicated sender email account

Use an account separate from your personal email — this server holds a
live SMTP credential and is reachable by anyone who finds its URL.
Generate an [app password](https://myaccount.google.com/apppasswords)
for it (requires 2-Step Verification).

### 2. Approve that sender in your Amazon account

Manage Your Content and Devices -> Preferences -> Personal Document
Settings -> Approved Personal Document E-mail List -> add the sender's
address. Skip this and every send vanishes silently.

### 3. Configure the server

The server reads:

- `SENDER_EMAIL` / `SMTP_APP_PASSWORD` — the account from steps 1-2.
- `STATE_DIR` (default `/state`) — where `devices.json` is stored.
  Mount a host directory here, read-write.
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
  -e SENDER_EMAIL=your-bot@gmail.com \
  -e SMTP_APP_PASSWORD=xxxxxxxxxxxxxxxx \
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
