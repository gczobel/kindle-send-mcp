# kindle-send-mcp

An MCP server that lets an AI agent send books from a Calibre library
directly to a Kindle device, using [`stkclient`](https://github.com/maxdjohnson/stkclient)
(an unofficial client for Amazon's Send to Kindle API) instead of the
unreliable email/SMTP path.

## What this is, and isn't

- **Read access** to a Calibre library's `metadata.db` and book files, to
  resolve a book by id to a real file to send.
- **Send access** to your Amazon account's registered Kindle devices, via
  `stkclient`.
- No metadata editing, no library writes, no device management beyond
  listing and sending.

## Reliability posture

`stkclient` is unofficial and reverse-engineered — it isn't published or
supported by Amazon, and has gone roughly a year between PyPI releases at
times. If Amazon changes their API, sending may break until the library
(or a patch to it) is updated. The official `@kindle.com` email path
remains a manual fallback if this stops working. This tradeoff is
accepted deliberately in exchange for avoiding email/SMTP's own
reliability problems and the 10MB attachment limit.

## Setting up your own instance

### 1. Generate your own OAuth session (`client.json`)

This step authenticates `stkclient` against **your** Amazon account. Do
this once, on any machine with a browser — the resulting file is what the
server reads later, and never needs regenerating unless the session is
revoked.

```bash
pip install stkclient
python3 -c "
import stkclient

oauth = stkclient.OAuth2()
url = oauth.get_signin_url()
print('Open this URL, sign in, then paste the URL you land on:')
print(url)
redirect_url = input('Redirect URL: ')
client = oauth.create_client(redirect_url)
with open('client.json', 'w') as f:
    client.dump(f)
print('Saved client.json')
"
```

This produces `client.json` — **a live credential for your Amazon
account**. Treat it like a password:
- Never commit it to git (this repo's `.gitignore` already excludes it,
  but that only helps if it's ever placed inside the repo directory in
  the first place — don't).
- Never include it in a Docker build context.
- Store it only in the mounted state directory described below.

### 2. Where the server expects it

The server reads `$STATE_DIR/client.json` (`STATE_DIR` defaults to
`/state` inside the container). Mount a host directory containing your
`client.json` to that path, read-write — the server re-saves the session
after every use, since `stkclient` rotates the refresh token on each
call, and a stale unrotated token will fail to re-authenticate.

### 3. Point it at your library

Mount your Calibre library (containing `metadata.db` and the book files)
read-only to `/books` (`CALIBRE_LIBRARY_PATH`, default `/books`).

### Example `docker run`

```bash
docker run -d \
  -v /path/to/your/state-dir:/state \
  -v /path/to/your/calibre/library:/books:ro \
  -p 9002:9002 \
  ghcr.io/gczobel/kindle-send-mcp:latest
```

## Tools

- `list_devices()` — lists Kindle devices registered to the Amazon
  account behind the configured `client.json`.
- `send_book(book_id, target_device_serial_number=None)` — sends the
  book with that id (looked up in `metadata.db`) to a device. If no
  device has been chosen yet (no default set, no explicit target given),
  returns the device list instead of guessing which one you meant.
