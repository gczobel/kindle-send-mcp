# kindle-send-mcp

Sends EPUBs from a Calibre library to Kindle devices via email, and tracks which devices exist.

## Language

**Device**:
A Kindle (or Kindle app) the operator wants to receive books on. Identified by a nickname the operator chooses (e.g. `paperwhite`), paired with its `@kindle.com` delivery address. Registered via the `add_device` tool or by editing the device config directly.
_Avoid_: "serial number" as the identifying key — that was Amazon's OAuth-era device identifier and is no longer used; nothing in this system calls Amazon's API anymore.

**Sender**:
The email address this server sends from, added to Amazon's Approved Personal Document Email List. Originally planned as a dedicated address separate from the operator's personal email; in practice it's the operator's real Gmail account, because it's also the one they authorize as in Google's OAuth consent screen — the two have to match exactly, or every send fails (see docs/adr/0002).
_Avoid_: assuming this is a low-stakes throwaway address; it currently is the operator's real inbox.

**Delivery**:
Handing an EPUB to SMTP, addressed to a device's `@kindle.com` address. This confirms only that the message was accepted by the SMTP server — it does **not** confirm the Kindle received it. Amazon's Send-to-Kindle email service gives no delivery confirmation and silently discards mail from unapproved senders (no bounce, no error).
_Avoid_: "sent" implying confirmed delivery — that was true under the old Amazon OAuth integration (which returned a real SKU), it is not true here.

**Default device**:
The device a send targets when none is specified explicitly. Sticky across calls until explicitly changed or cleared on a failed send.

**Authorized**:
Whether the server currently holds a working OAuth2 credential (a refresh token) letting it send as the Sender. Not authorized — because setup never happened, or a previously-working credential went stale — means `send_book` returns a one-time setup link instead of attempting to send. Becomes true the moment that link is completed once; nothing about normal use ever asks again unless the credential itself later stops working.
_Avoid_: confusing with Amazon's Approved Personal Document Email List (a completely different account, a static allowlist Amazon checks, not a credential this server holds at all).
