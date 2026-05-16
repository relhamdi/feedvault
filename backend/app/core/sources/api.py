from typing import Any

import httpx
from sqlmodel import Session

from app.core.crypto import decrypt_credentials
from app.core.sources.base import BaseSource
from app.models.source import Source

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)


class APISource(BaseSource):
    """Base class for API sources."""

    default_headers: dict = {}
    default_params: dict = {}
    timeout: httpx.Timeout = DEFAULT_TIMEOUT
    _client: httpx.Client | None = None

    def __init__(
        self,
        feed_id: int,
        session: Session,
        source: Source,
        params: dict | None = None,
    ):
        super().__init__(feed_id=feed_id, session=session, source=source, params=params)
        credentials = (
            decrypt_credentials(source.credentials) if source.credentials else {}
        )
        auth_headers = self._build_auth_headers(credentials)
        if auth_headers:
            self.default_headers = {**self.__class__.default_headers, **auth_headers}

    def _build_auth_headers(self, credentials: dict) -> dict:
        """Override in subclasses to inject auth headers from credentials."""
        return {}

    def build_url(self, endpoint: str) -> str:
        return f"{self.source.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> tuple[Any, httpx.Headers]:
        """Perform a GET request. Returns (data, headers)."""
        url = self.build_url(endpoint)
        merged_params = {**self.default_params, **(params or {})}
        response = self.get_client().get(
            url,
            headers=self.default_headers,
            params=merged_params,
        )
        response.raise_for_status()
        return response.json(), response.headers
