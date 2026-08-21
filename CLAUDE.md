# CLAUDE.md

Never read, print, cat, or log the contents of `.env` in this repo directory. It's a local setup artifact (from the SMTP onboarding wizard) holding a live SMTP app password for the operator's real email account — the deployed server never reads it, it only exists here on disk. Treat it exactly like a password.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `gczobel/kindle-send-mcp` (uses the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
