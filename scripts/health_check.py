"""Calls the deployed kindle-send-mcp connector's list_devices() over real
HTTP and exits non-zero on any failure. Run on a schedule (see
.github/workflows/health-check.yml) to catch OAuth session invalidation
(see issue #11) independently of manual testing."""

import asyncio
import sys

from fastmcp import Client

SERVER_URL = "https://kindle-mcp.gczobel.dpdns.org/mcp"


async def main() -> int:
    try:
        async with Client(SERVER_URL) as client:
            result = await client.call_tool("list_devices", {})
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1

    devices = result.data
    if not devices:
        print("FAIL: list_devices() returned no devices")
        return 1

    print(f"OK: {len(devices)} device(s) returned")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
