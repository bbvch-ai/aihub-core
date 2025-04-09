import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx

# Set up logging
logger = logging.getLogger("openwebui.client")


class OpenWebuiAPIError(Exception):
    """Exception raised for OpenWebUI API errors"""

    def __init__(self, status_code: int, detail: str, response_body: str = None):
        self.status_code = status_code
        self.detail = detail
        self.response_body = response_body
        message = f"API Error {status_code}: {detail}"
        super().__init__(message)


class BaseClient:
    """
    Base HTTP client for making API requests to OpenWebUI.

    Handles authentication and request formatting. All API endpoints
    should use this client for communication.

    Example:
        ```python
        client = BaseClient(token="my-bearer-token")
        response = await client.get("/api/v1/users/")
        ```
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        token: Optional[str] = None,
        timeout: int = 30,
        debug: bool = False,
    ):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.debug = debug

        # Configure logging based on debug setting
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def _get_headers(self) -> Dict[str, str]:
        """Prepare request headers with authentication if token is provided"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get_url(self, endpoint: str) -> str:
        """Build full URL from endpoint path"""
        return urljoin(self.base_url, endpoint)

    async def _handle_response(self, response: httpx.Response) -> httpx.Response:
        """
        Handle HTTP response and log details in debug mode
        Raises exceptions for error status codes
        """
        if self.debug:
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            # Log response body but truncate if too large
            body = response.text
            if len(body) > 1000:
                logger.debug(f"Response body (truncated): {body[:1000]}...")
            else:
                logger.debug(f"Response body: {body}")

        # Handle error responses
        if response.status_code >= 400:
            detail = "Unknown error"

            # Try to extract error details from response
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    if "detail" in error_data:
                        if isinstance(error_data["detail"], str):
                            detail = error_data["detail"]
                        else:
                            detail = json.dumps(error_data["detail"])
                    else:
                        detail = json.dumps(error_data)
            except Exception as e:
                detail = response.text or str(e)

            logger.error(f"API error {response.status_code}: {detail}")
            raise OpenWebuiAPIError(response.status_code, detail, response.text)

        return response

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    ) -> httpx.Response:
        """Send HTTP request and handle connection errors"""
        url = self._get_url(endpoint)
        headers = self._get_headers()

        if self.debug:
            logger.debug(f"Request: {method} {url}")
            logger.debug(f"Headers: {headers}")
            logger.debug(f"Params: {params}")

            # Log request body but don't log potentially sensitive auth info
            if json_data:
                logger.debug(f"Body: {json_data}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method=method, url=url, headers=headers, params=params, json=json_data)
                return await self._handle_response(response)

        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise OpenWebuiAPIError(status_code=0, detail=f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make a GET request to the API"""
        return await self._request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make a POST request to the API with JSON body"""
        return await self._request("POST", endpoint, params=params, json_data=json_data)

    async def put(
        self, endpoint: str, json_data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Make a PUT request to the API with JSON body"""
        return await self._request("PUT", endpoint, params=params, json_data=json_data)

    async def delete(
        self,
        endpoint: str,
        json_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make a DELETE request to the API"""
        return await self._request("DELETE", endpoint, params=params, json_data=json_data)
