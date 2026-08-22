from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from .token_store import TokenStore

SCOPES = ["https://mail.google.com/"]
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailOAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_store: TokenStore,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._token_store = token_store

    def is_authorized(self) -> bool:
        return self._token_store.has_token()

    def _client_config(self) -> dict:
        return {
            "web": {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "auth_uri": AUTH_URI,
                "token_uri": TOKEN_URI,
                "redirect_uris": [self._redirect_uri],
            }
        }

    def _flow(self) -> Flow:
        # authorization_url() and exchange_code() each build their own Flow
        # instance -- they're two separate HTTP requests, potentially far
        # apart in time, with nothing carrying a PKCE code_verifier between
        # them. Auto-generated PKCE would mean the verifier used at exchange
        # time never matches the challenge Google actually has on file
        # (invalid_grant: Missing code verifier). Not needed anyway: this is
        # a confidential client (has a client_secret), which is what PKCE
        # exists to substitute for on clients that can't hold one.
        flow = Flow.from_client_config(
            self._client_config(), scopes=SCOPES, autogenerate_code_verifier=False
        )
        flow.redirect_uri = self._redirect_uri
        return flow

    def authorization_url(self) -> str:
        # prompt="consent" forces Google to re-issue a refresh token even
        # if this account already granted consent before -- without it, a
        # second /oauth/start after the stored token was lost some other
        # way could silently come back with no refresh token at all.
        url, _state = self._flow().authorization_url(prompt="consent")
        return url

    def exchange_code(self, code: str) -> None:
        flow = self._flow()
        flow.fetch_token(code=code)
        self._token_store.save_refresh_token(flow.credentials.refresh_token)

    def get_access_token(self) -> str:
        refresh_token = self._token_store.load_refresh_token()
        if refresh_token is None:
            raise RuntimeError("not authorized -- no refresh token stored")

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=TOKEN_URI,
            client_id=self._client_id,
            client_secret=self._client_secret,
        )
        try:
            credentials.refresh(Request())
        except RefreshError:
            # Google explicitly rejected this refresh token (revoked,
            # expired from disuse, etc.) -- it will never work again, so
            # clear it now rather than retrying it on every future send.
            # Other failures (a network timeout, say) don't mean the
            # token itself is bad, so they're left alone and just
            # propagate.
            self._token_store.clear()
            raise
        return credentials.token
