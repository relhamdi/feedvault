from typing import Any

import httpx

from app.core.sources.base import BaseSource

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)


class APISource(BaseSource):
    """Base class for API sources."""

    default_headers: dict = {}
    default_params: dict = {}
    timeout: httpx.Timeout = DEFAULT_TIMEOUT

    def build_url(self, endpoint: str) -> str:
        return f"{self.source.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> tuple[Any, httpx.Headers]:
        """Perform a GET request. Returns (data, headers)."""
        url = self.build_url(endpoint)
        merged_params = {**self.default_params, **(params or {})}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                url,
                headers=self.default_headers,
                params=merged_params,
            )
            response.raise_for_status()
            return response.json(), response.headers
