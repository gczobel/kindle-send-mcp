from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class BearerTokenMiddleware:
    """Rejects any request without a matching `Authorization: Bearer <token>` header."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self._expected = f"Bearer {token}".encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        provided = headers.get(b"authorization", b"")
        if provided != self._expected:
            response = JSONResponse({"error": "Forbidden"}, status_code=403)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
