#!/usr/bin/env bash
# Smoke-check the public auth chain in front of an MCP server that is exposed
# through a Cloudflare tunnel and mcp-auth-proxy.
#
# Per hostname it makes three requests:
#
#   GET  /.well-known/oauth-protected-resource/mcp   expect 200 from the proxy
#   GET  /.well-known/oauth-authorization-server     expect 200 from the proxy
#   POST /mcp           (unauthenticated)            expect 401 from the proxy
#
# The first two fail with 404 when a tunnel path rule hijacks the OAuth
# discovery paths and sends them to the MCP server instead. cloudflared compiles
# a public hostname's `path` field as an unanchored regex, so a rule as innocent
# as `/oauth/*` matches `/.well-known/oauth-protected-resource/mcp` too. The
# third fails when the auth proxy is not in the chain at all.
#
# Both failures are written up in docs/deployment-guide.md, under "When a client
# cannot connect", and the first one in docs/adr/0003-resend-instead-of-gmail.md.
#
# Assumes the MCP endpoint is served at /mcp.
set -euo pipefail

TIMEOUT="${TIMEOUT:-20}"

usage() {
  cat <<'EOF'
Usage: check-mcp-auth.sh <host> [<host> ...]

Checks the public auth chain for each hostname, and reports which hop is broken
when a check fails. Hostnames may be given with or without a scheme.

  scripts/check-mcp-auth.sh kindle-mcp.example.org calibre-mcp.example.org
  TIMEOUT=5 scripts/check-mcp-auth.sh kindle-mcp.example.org

Assumes the MCP endpoint is served at /mcp. Exit status is 0 when every check
passes, 1 when any check fails, and 2 on a usage error.
EOF
}

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    -*) echo "unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

PASSED=0
FAILED=0

note() {
  printf '        %s\n' "$*"
}

pass_check() {
  printf '  ok    %s -> %s\n' "$1" "$2"
  PASSED=$((PASSED + 1))
}

fail_check() {
  printf '  FAIL  %s\n' "$1"
  note "$2"
  FAILED=$((FAILED + 1))
}

# Leaves the response in $tmp/body, the status in CODE, and the curl error in ERR.
request() {
  local method="$1" url="$2"
  CODE=""
  ERR=""
  if ! CODE=$(curl -sS --max-time "$TIMEOUT" -o "$tmp/body" \
      -w '%{http_code}' -X "$method" "$url" 2>"$tmp/err"); then
    CODE=""
    ERR="$(tr -d '\n' <"$tmp/err" || true)"
    : >"$tmp/body"
  fi
  BODY="$(head -c 200 "$tmp/body" 2>/dev/null | tr -d '\n' || true)"
}

check_discovery() {
  local base="$1" path="$2" label
  label="GET $path"
  request GET "$base$path"

  if [[ -z "$CODE" ]]; then
    fail_check "$label" "request failed: ${ERR:-no response}"
    note "The hostname does not resolve, or the tunnel is down."
    return 0
  fi
  if [[ "$CODE" == "200" ]] && grep -q 'authorization' "$tmp/body"; then
    pass_check "$label" "$CODE"
    return 0
  fi
  if [[ "$CODE" == "404" ]]; then
    fail_check "$label" "404, so this path never reached the auth proxy"
    if [[ "$BODY" == "Not Found" ]]; then
      note "The body of \"Not Found\" comes from an origin server, which is what a"
      note "hijacked discovery path looks like here."
    elif [[ -z "$BODY" ]]; then
      note "The body is empty, which is the tunnel's own fallback, so this"
      note "hostname may not be mapped to any service at all."
    else
      note "body: $BODY"
    fi
    note "In Zero Trust > Networks > Tunnels > Public Hostnames, check for a path"
    note "rule whose regex matches /.well-known/oauth-* and delete it."
    return 0
  fi
  if [[ "$CODE" == "401" || "$CODE" == "403" ]]; then
    fail_check "$label" "$CODE"
    note "Something in front of the auth proxy is intercepting it, most likely a"
    note "Cloudflare Access policy. Discovery has to answer without credentials."
    return 0
  fi
  fail_check "$label" "$CODE, expected 200 with JSON metadata"
  note "body: ${BODY:-<empty>}"
}

check_mcp() {
  local base="$1" label="POST /mcp"
  request POST "$base/mcp"

  if [[ -z "$CODE" ]]; then
    fail_check "$label" "request failed: ${ERR:-no response}"
    return 0
  fi
  if [[ "$CODE" == "401" ]]; then
    pass_check "$label" "$CODE (unauthenticated, as expected)"
    return 0
  fi
  fail_check "$label" "$CODE, expected 401 for an unauthenticated request"
  if [[ "$CODE" == "400" || "$CODE" == "406" ]]; then
    note "This looks like the MCP server answering directly, so the auth proxy is"
    note "not in the chain for this hostname."
  fi
  note "body: ${BODY:-<empty>}"
}

for host in "$@"; do
  case "$host" in
    http://*|https://*) base="${host%/}" ;;
    *) base="https://${host%/}" ;;
  esac
  printf '\n%s\n' "$base"
  check_discovery "$base" "/.well-known/oauth-protected-resource/mcp"
  check_discovery "$base" "/.well-known/oauth-authorization-server"
  check_mcp "$base"
done

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
if [[ "$FAILED" -gt 0 ]]; then
  exit 1
fi
