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
        self, url: str, semaphore: asyncio.Semaphore, client: httpx2.AsyncClient
    ) -> httpx2.Response | list[str]:
        """Asynchronous HTTP client with semaphore.

        Args:
            url (str): URL to GET
            semaphore (asyncio.Semaphore): Semaphore bound to the current event loop
            client (httpx2.AsyncClient): Async client bound to the current event loop

        Returns:
            httpx2.Response: Response object
        """
        async with semaphore:
            try:
                response = await client.get(url)
                if response.status_code != self.httpx_success_status:
                    # print(f'HTTP request Error for {url}: {response.status_code}')
                    return response
                return response
            except (httpx2.HTTPStatusError, httpx2.RequestError):
                # print(f'HTTP request Error for {url}: {exc}')
                return httpx2.Response(
                    status_code=500,  # Server error as a fallback
                    text='Error occurred during request',
                    request=httpx2.Request('GET', url),
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
            parameters (dict | None): Additional parameters for the GET request

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
            url_list (list): List of URLs to GET
            semaphore_num (int): Number of concurrent requests allowed

        Returns:
            list: List of httpx2.Response objects
        """
        semaphore = asyncio.Semaphore(self.semaphore_num)  # TODO: make this configurable
        async with httpx2.AsyncClient(timeout=None, headers=self.header) as client:
            tasks = [self._async_semaphore_client(url, semaphore, client) for url in url_list]
            return await asyncio.gather(*tasks)
