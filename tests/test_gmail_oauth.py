from pathlib import Path
from unittest.mock import MagicMock, patch

from google.auth.exceptions import RefreshError

from kindle_send_mcp.gmail_oauth import GmailOAuth
from kindle_send_mcp.token_store import TokenStore


def test_is_authorized_delegates_to_token_store(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    assert oauth.is_authorized() is False
    tokens.save_refresh_token("refresh-abc")
    assert oauth.is_authorized() is True


def test_authorization_url_returns_the_url_from_flow(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    fake_flow = MagicMock()
    fake_flow.authorization_url.return_value = ("https://accounts.google.com/consent", "state-xyz")

    with patch("kindle_send_mcp.gmail_oauth.Flow.from_client_config", return_value=fake_flow):
        url = oauth.authorization_url()

    assert url == "https://accounts.google.com/consent"
    assert fake_flow.redirect_uri == "https://kindle-mcp.example.com/oauth/callback"


def test_exchange_code_saves_the_refresh_token(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    fake_flow = MagicMock()
    fake_flow.credentials.refresh_token = "refresh-from-google"

    with patch("kindle_send_mcp.gmail_oauth.Flow.from_client_config", return_value=fake_flow):
        oauth.exchange_code("auth-code-123")

    fake_flow.fetch_token.assert_called_once_with(code="auth-code-123")
    assert tokens.load_refresh_token() == "refresh-from-google"


def test_get_access_token_raises_when_not_authorized(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    try:
        oauth.get_access_token()
        assert False, "expected an exception"
    except RuntimeError:
        pass


def test_get_access_token_refreshes_and_returns_the_token(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    tokens.save_refresh_token("refresh-abc")
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    def fake_refresh(self, request):
        self.token = "fresh-access-token"

    with patch("kindle_send_mcp.gmail_oauth.Credentials.refresh", fake_refresh):
        access_token = oauth.get_access_token()

    assert access_token == "fresh-access-token"
    assert tokens.has_token() is True


def test_get_access_token_clears_the_token_when_google_rejects_the_refresh(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    tokens.save_refresh_token("refresh-abc")
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    def fake_refresh(self, request):
        raise RefreshError("invalid_grant")

    with patch("kindle_send_mcp.gmail_oauth.Credentials.refresh", fake_refresh):
        try:
            oauth.get_access_token()
            assert False, "expected an exception"
        except RefreshError:
            pass

    assert tokens.has_token() is False


def test_get_access_token_keeps_the_token_on_an_unrelated_failure(tmp_path: Path):
    tokens = TokenStore(tmp_path)
    tokens.save_refresh_token("refresh-abc")
    oauth = GmailOAuth(
        client_id="id",
        client_secret="secret",
        redirect_uri="https://kindle-mcp.example.com/oauth/callback",
        token_store=tokens,
    )

    def fake_refresh(self, request):
        raise TimeoutError("network blip")

    with patch("kindle_send_mcp.gmail_oauth.Credentials.refresh", fake_refresh):
        try:
            oauth.get_access_token()
            assert False, "expected an exception"
        except TimeoutError:
            pass

    assert tokens.has_token() is True
