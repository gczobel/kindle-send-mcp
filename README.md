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

Sender authentication is OAuth2, not a static App Password — see
[docs/adr/0002-oauth2-for-gmail-instead-of-app-password.md](docs/adr/0002-oauth2-for-gmail-instead-of-app-password.md)
for why (App Passwords can be gated entirely on brand-new Google
accounts, with no documented waiting period).

### 1. Create a dedicated sender email account

Use an account separate from your personal email — this server holds a
live credential and is reachable by anyone who finds its URL.

### 2. Approve that sender in your Amazon account

Manage Your Content and Devices -> Preferences -> Personal Document
Settings -> Approved Personal Document E-mail List -> add the sender's
address. Skip this and every send vanishes silently.

### 3. Create a Google OAuth client

1. [Google Cloud Console](https://console.cloud.google.com) -> create a
   project (or reuse one).
2. APIs & Services -> Credentials -> **Google Auth Platform** -> Get
   started. Audience: **External**. Skip the optional Branding fields
   (home page, privacy policy, terms of service) -- those are only
   required to switch to production/public status, which this doesn't
   need.
3. Audience tab -> **Test users** -> add the sender's Gmail address.
   This, not Branding, is the actual fix if you see `Access blocked:
   has not completed the Google verification process`.
4. Clients tab -> Create OAuth client -> Application type: **Web
   application** (not Desktop app -- Google restricts Desktop clients
   to loopback redirects only, incompatible with a server-hosted
   callback). Authorized redirect URI:
   `<your PUBLIC_BASE_URL>/oauth/callback`.
5. Copy the Client ID and Client Secret.

### 4. Configure the server

- `SENDER_EMAIL` / `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` -- from
  steps 1 and 3.
- `PUBLIC_BASE_URL` -- the server's real public URL (e.g.
  `https://kindle-mcp.example.com`), used to build the OAuth redirect
  URI. Must exactly match what you registered in step 3.4.
- `STATE_DIR` (default `/state`) -- where `devices.json` and
  `oauth_refresh_token.json` are stored. Mount a host directory here,
  read-write.
- `CALIBRE_LIBRARY_PATH` (default `/books`) -- your Calibre library,
  mounted read-only.

### 5. Authorize the sender account

Nothing to do here upfront -- the first time you ask to send a book,
`send_book` returns a `needs_authorization` status with a link
(`<PUBLIC_BASE_URL>/oauth/start`). The calling agent should present
that link, ask you to confirm once you've signed in as the sender
account, and retry the same request on its own -- the same pattern it
already uses for `needs_device_selection`, not something you need to
re-ask for yourself. This is a one-time step: the resulting refresh
token is stored server-side and used silently for every future send.

If you'd rather get it out of the way before ever asking for a book,
you can open that link directly once the server's deployed.

### 6. Register your devices

Find each device's `@kindle.com` address in Manage Your Content and
Devices -> Preferences -> Personal Document Settings -> Send-to-Kindle
E-Mail Settings, then use the `add_device` tool (nickname + address) --
no file editing needed.

### Example `docker run`

```bash
docker run -d \
  -e SENDER_EMAIL=your-bot@gmail.com \
  -e GOOGLE_CLIENT_ID=xxxxxxxxxx.apps.googleusercontent.com \
  -e GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxxxxx \
  -e PUBLIC_BASE_URL=https://kindle-mcp.example.com \
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
  returns the device list instead of guessing which one you meant. If
  the sender account hasn't been authorized yet (or a previous
  authorization went stale), returns a `needs_authorization` status
  with a link instead of failing outright — visit the link, then call
  this again.
