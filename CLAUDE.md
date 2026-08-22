# CLAUDE.md

Never read, print, cat, or log the contents of `.env` in this repo directory, or `oauth_refresh_token.json` anywhere in this repo or a local state directory. `.env` is a stale local artifact from the original App Password setup (superseded by OAuth2, see docs/adr/0002) and may still hold a real SMTP app password. `oauth_refresh_token.json` is a live OAuth2 credential for the operator's real Gmail account. Treat both exactly like a password.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `gczobel/kindle-send-mcp` (uses the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
