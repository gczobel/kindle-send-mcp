# CLAUDE.md

Never read, print, cat, or log the contents of `client.json` (or any file matching `*client.json`, `default_device.json`) in this repo or its state directory. It is a live OAuth credential for the operator's real Amazon account — treat it exactly like a password.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `gczobel/kindle-send-mcp` (uses the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
