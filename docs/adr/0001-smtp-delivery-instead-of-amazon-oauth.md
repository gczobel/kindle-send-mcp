# Deliver books via SMTP to `@kindle.com` instead of Amazon's OAuth API

The original integration used `stkclient`, a reverse-engineered client for Amazon's internal Send-to-Kindle API, authenticated via a persisted OAuth session. That session repeatedly and unpredictably failed (`DeviceInfoToken`/`invalid_grant`, see issue #11) with no confirmed root cause — restart and redeploy were both ruled out as triggers, leaving "the session just doesn't survive idle time" as the working theory. Because it's an unofficial, unsupported API, there was no path to actually fix this.

We switched to Amazon's own supported Send-to-Kindle **email** feature: EPUBs are sent as attachments to each device's `@kindle.com` address via SMTP, from a dedicated sender address approved in the operator's Amazon account.

## Consequences

- Gained: nothing left to invalidate — no OAuth session, no live credential held by the running service.
- Lost: no delivery confirmation at all. Amazon gives no bounce and no success signal; a misconfigured sender is a **silent** failure. Mitigated by BCC'ing the sender's own inbox on every send, as an audit trail (not a delivery guarantee).
- Lost: device auto-discovery. Amazon's OAuth API returns device names and serial numbers but never the `@kindle.com` address (confirmed against `stkclient`'s actual response model) — auto-discovery was considered and rejected (see triage discussion, 2026-08-21) since it would only save re-typing a device name, not the address itself, which must always be looked up manually in Amazon's account settings. Devices are registered by hand via the `add_device` tool instead.
