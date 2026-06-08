"""HTTP client class for making GET requests."""

import asyncio
from urllib.parse import urljoin

import httpx2

from dvmeta.models.config import Config


class HttpxClient:
    """HTTP client class for making GET requests."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.httpx_success_status = 200
        self.semaphore_num = config.semaphore_limit

        self.header = (
            {'Accept': 'application/json'}
            if not config.api_key
            else {'Accept': 'application/json', 'X-Dataverse-key': config.api_key}
        )

    async def _async_semaphore_client(
        self, request: httpx2.Request, semaphore: asyncio.Semaphore, client: httpx2.AsyncClient
    ) -> httpx2.Response:
        """Asynchronous HTTP client with semaphore.

        Args:
            request (httpx2.Request): Pre-built request object
            semaphore (asyncio.Semaphore): Semaphore bound to the current event loop
            client (httpx2.AsyncClient): Async client bound to the current event loop

        Returns:
            httpx2.Response: Response object
        """
        async with semaphore:
            try:
                return await client.send(request)
            except (httpx2.HTTPStatusError, httpx2.RequestError):
                return httpx2.Response(
                    status_code=500,
                    text='Error occurred during request',
                    request=request,
                )

    def authenticate_api_key(self) -> bool:
        """Authenticate the API key for the Dataverse repository.

        Returns:
            bool: True if the API key is valid, False otherwise
        """
        base_url: str = self.config.base_url
        api_key: str = self.config.api_key or ''
        auth_headers: dict = {'X-Dataverse-key': api_key}
        api_endpoint: str = '/api/users/:me'
        auth_url = urljoin(base_url, api_endpoint)

        try:
            with httpx2.Client(timeout=None, headers=self.header) as client:
                response = client.get(auth_url, headers=auth_headers)
                return response.status_code == self.httpx_success_status
        except (httpx2.HTTPStatusError, httpx2.RequestError):
            return False

    def authenticate_dv_connection(self) -> bool:
        """Authenticate the connection to the Dataverse repository.

        Returns:
            bool: True if the connection is successful, False otherwise
        """
        base_url: str = self.config.base_url
        public_url: str = urljoin(base_url, '/api/info/version')

        try:
            with httpx2.Client(timeout=None, headers=self.header) as client:
                response = client.get(public_url)
                return response.status_code == self.httpx_success_status
        except (httpx2.HTTPStatusError, httpx2.RequestError):
            return False

    def sync_get(self, url: str, params: list | dict | None = None) -> httpx2.Response | None:
        """Synchronous GET request.

        Args:
            url (str): URL to GET
            params (dict | None): Additional parameters for the GET request

        Returns:
            httpx2.Response | None: Response object or None if error
        """
        try:
            # Create a new client for each request to avoid the "closed client" issue
            with httpx2.Client(timeout=None, headers=self.header) as client:
                response = client.get(url, params=params)
                return response if response.status_code == self.httpx_success_status else None
        except (httpx2.HTTPStatusError, httpx2.RequestError):
            return httpx2.Response(
                status_code=500,  # Server error as a fallback
                text='Error occurred during request',
                request=httpx2.Request('GET', url),
            )

    async def async_get(
        self,
        url_list: list,
    ) -> list:
        """Asynchronous GET request.

        Args:
            url_list (list): List of URLs (str) or pre-built httpx2.Request objects to GET

        Returns:
            list: List of httpx2.Response objects
        """
        semaphore = asyncio.Semaphore(self.semaphore_num)
        async with httpx2.AsyncClient(timeout=None, headers=self.header) as client:
            built = [
                client.build_request(r.method, str(r.url))
                if isinstance(r, httpx2.Request)
                else client.build_request('GET', r)
                for r in url_list
            ]
            tasks = [self._async_semaphore_client(request, semaphore, client) for request in built]
            return await asyncio.gather(*tasks)
