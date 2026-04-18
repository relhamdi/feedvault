import httpx

from app.core.sources.base import BaseSource


class APISource(BaseSource):
    """Base class for API sources."""

    base_url: str = ""
    default_headers: dict = {}
    default_params: dict = {}

    def build_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        url = self.build_url(endpoint)
        merged_params = {**self.default_params, **(params or {})}
        with httpx.Client() as client:
            response = client.get(
                url,
                headers=self.default_headers,
                params=merged_params,
            )
            response.raise_for_status()
            return response.json()
