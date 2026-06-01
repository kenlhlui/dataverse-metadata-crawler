"""HTTP client class for making GET requests."""

import asyncio
from types import TracebackType
from urllib.parse import urljoin

import httpx
from loguru import logger

from dvmeta.models import Config


class HttpxClient:
    """HTTP client class for making GET requests."""

    def __init__(self, config: Config) -> None:
        """Initialize HTTP client.

        Args:
            config (Config): Configuration settings
            semaphore (asyncio.Semaphore): Semaphore object for limiting concurrent requests
            sync_client (httpx.Client): Synchronous HTTP client
            async_client (httpx.AsyncClient): Asynchronous HTTP client
            async_sleep_time (int): Sleep time for asynchronous requests
        """  # noqa: W505
        self.config = config
        self.sync_client = httpx.Client(timeout=None, headers=dict(config.headers))
        self.async_sleep_time = 0  # TODO: make this configurable
        self.httpx_success_status = 200

    def __enter__(self) -> 'HttpxClient':
        """Enter context manager.

        Returns:
            HttpxClient: Self reference
        """
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        self.sync_client.close()

    async def __aenter__(self) -> 'HttpxClient':
        """Enter asynchronous context manager."""
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Exit asynchronous context manager and cleanup resources."""
        self.sync_client.close()

    async def _async_semaphore_client(
        self, url: str, semaphore: asyncio.Semaphore, client: httpx.AsyncClient
    ) -> httpx.Response | list[str]:
        """Asynchronous HTTP client with semaphore.

        Args:
            url (str): URL to GET
            semaphore (asyncio.Semaphore): Semaphore bound to the current event loop
            client (httpx.AsyncClient): Async client bound to the current event loop

        Returns:
            httpx.Response: Response object
        """
        async with semaphore:
            try:
                response = await client.get(url)
                if response.status_code != self.httpx_success_status:
                    # print(f'HTTP request Error for {url}: {response.status_code}')
                    return response
                return response
            except (httpx.HTTPStatusError, httpx.RequestError):
                # print(f'HTTP request Error for {url}: {exc}')
                return httpx.Response(
                    status_code=500,  # Server error as a fallback
                    text='Error occurred during request',
                    request=httpx.Request('GET', url),
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
            with self.sync_client as client:
                response = client.get(auth_url, headers=auth_headers)
                logger.debug(f'API key authentication response: {response.text}')
                return response.status_code == self.httpx_success_status
        except (httpx.HTTPStatusError, httpx.RequestError):
            return False

    def authenticate_dv_connection(self) -> bool:
        """Authenticate the connection to the Dataverse repository.

        Returns:
            bool: True if the connection is successful, False otherwise
        """
        base_url: str = self.config.base_url
        public_url: str = urljoin(base_url, '/api/info/version')

        try:
            with self.sync_client as client:
                response = client.get(public_url)
                return response.status_code == self.httpx_success_status
        except (httpx.HTTPStatusError, httpx.RequestError):
            return False

    def sync_get(self, url: str, params: list | dict | None = None) -> httpx.Response | None:
        """Synchronous GET request.

        Args:
            url (str): URL to GET
            parameters (dict | None): Additional parameters for the GET request

        Returns:
            httpx.Response | None: Response object or None if error
        """
        try:
            # Create a new client for each request to avoid the "closed client" issue
            with httpx.Client(timeout=None, headers=dict(self.config.headers)) as client:
                response = client.get(url, params=params)
                return response if response.status_code == self.httpx_success_status else None
        except (httpx.HTTPStatusError, httpx.RequestError):
            return httpx.Response(
                status_code=500,  # Server error as a fallback
                text='Error occurred during request',
                request=httpx.Request('GET', url),
            )

    async def async_get(self, url_list: list) -> list:
        """Asynchronous GET request.

        Args:
            url_list (list): List of URLs to GET

        Returns:
            list: List of httpx.Response objects
        """
        semaphore = asyncio.Semaphore(10)  # TODO: make this configurable
        async with httpx.AsyncClient(timeout=None, headers=dict(self.config.headers)) as client:
            tasks = [self._async_semaphore_client(url, semaphore, client) for url in url_list]
            return await asyncio.gather(*tasks)
