# kindle-send-mcp

Sends EPUBs from a Calibre library to Kindle devices via email, and tracks which devices exist.

## Language

**Device**:
A Kindle (or Kindle app) the operator wants to receive books on. Identified by a nickname the operator chooses (e.g. `paperwhite`), paired with its `@kindle.com` delivery address. Registered via the `add_device` tool or by editing the device config directly.
_Avoid_: "serial number" as the identifying key — that was Amazon's OAuth-era device identifier and is no longer used; nothing in this system calls Amazon's API anymore.

**Sender**:
The email address this server sends from, added to Amazon's Approved Personal Document Email List. It is a dedicated address on the Resend sending domain (e.g. `kindle@<your-sending-domain>`), configured via `RESEND_FROM`. Under the old Gmail path it was the operator's real Gmail account, because the OAuth identity and sender had to match exactly (see docs/adr/0002); Resend removed that constraint (see docs/adr/0003).
_Avoid_: assuming this is a low-stakes throwaway address; it is the address Amazon's approved list trusts, so anything sent from it is deliverable to the operator's Kindles.

**Delivery**:
Handing an EPUB to the Resend API, addressed to a device's `@kindle.com` address. This confirms only that the Resend API accepted the message — it does **not** confirm the Kindle received it. Amazon's Send-to-Kindle email service gives no delivery confirmation and silently discards mail from unapproved senders (no bounce, no error). Resend's own logs are the audit trail.
_Avoid_: "sent" implying confirmed delivery — that was true under the old Amazon OAuth integration (which returned a real SKU), it is not true here.

**Default device**:
The device a send targets when none is specified explicitly. Sticky across calls until explicitly changed or cleared on a failed send.
