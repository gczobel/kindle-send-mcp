from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from kindle_send_mcp.auth import BearerTokenMiddleware


def _make_app(token: str) -> Starlette:
    async def endpoint(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/mcp", endpoint)])
    app.add_middleware(BearerTokenMiddleware, token=token)
    return app


def test_request_with_correct_bearer_token_passes_through():
    client = TestClient(_make_app("secret123"))
    response = client.get("/mcp", headers={"Authorization": "Bearer secret123"})
    assert response.status_code == 200
    assert response.text == "ok"


def test_request_with_wrong_bearer_token_is_rejected():
    client = TestClient(_make_app("secret123"))
    response = client.get("/mcp", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 403


def test_request_with_missing_authorization_header_is_rejected():
    client = TestClient(_make_app("secret123"))
    response = client.get("/mcp")
    assert response.status_code == 403


def test_request_with_non_bearer_authorization_is_rejected():
    client = TestClient(_make_app("secret123"))
    response = client.get("/mcp", headers={"Authorization": "Basic secret123"})
    assert response.status_code == 403
