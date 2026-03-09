from requests.adapters import BaseAdapter
from requests.models import Response
from starlette.testclient import TestClient


class ASGIAdapter(BaseAdapter):
    """
    ASGIAdapter is a custom requests adapter designed to intercept outbound HTTP calls
    and route them directly to a provided ASGI application, bypassing actual network communication.

    ### Purpose
    In testing environments - especially when using FastAPI - it is common for parts of the application
    to issue HTTP requests to endpoints that are also part of the same ASGI app. Without interception,
    these requests would attempt to resolve the hostname and make real network calls, which can lead to
    name resolution errors or unintended external dependencies. ASGIAdapter prevents these issues by
    directing the HTTP traffic internally, ensuring that:
    - The full request/response lifecycle (including middleware and routing) is exercised.
    - The tests remain isolated without relying on external network connectivity.
    - Performance is improved by avoiding unnecessary network overhead.

    ### Implementation Details
    - **Inheritance:** Extends `requests.adapters.BaseAdapter` to integrate with the `requests` library.
    - **TestClient Integration:** Instantiates a Starlette `TestClient` with the supplied ASGI app.
      This client is used to simulate HTTP calls internally.
    - **Response Conversion:** The adapter's `send` method dispatches the request using TestClient
      and then constructs a corresponding `requests.Response` object from the TestClient response.
    - **Usage:** By mounting ASGIAdapter on a `requests.Session`, any HTTP call matching a specific
      scheme or host (e.g., "http://test") is intercepted and routed to the in-memory ASGI app.

    This adapter is particularly useful when patching HTTP sessions in testing setups to ensure that
    all HTTP interactions occur within the test process, thereby enhancing test reliability and speed.
    """

    def __init__(self, app):
        super().__init__()
        self.client = TestClient(app)

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        # Use TestClient to call the app instead of going over the network.
        response = self.client.request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            data=request.body,
        )

        # Build a requests.Response from the TestClient response.
        resp = Response()
        resp.status_code = response.status_code
        resp.headers.update(response.headers)
        resp._content = response.content
        resp.url = request.url
        resp.request = request
        return resp

    def close(self):
        self.client.__exit__(None, None, None)
