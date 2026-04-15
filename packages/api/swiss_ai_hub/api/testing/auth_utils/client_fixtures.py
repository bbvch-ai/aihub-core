import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"


@pytest_asyncio.fixture
async def development_auth_api_client(controller_mount_func):
    """
    Create an AsyncClient with TestAuthHandler for testing.

    Usage:
        @pytest.mark.asyncio
        async def test_something(development_auth_api_client):
            def mount_controller(auth):
                return MyAccountController(auth=auth).get_my_account()

            client = await development_auth_api_client(mount_controller)
            response = await client.get("/api/v1/my-account")
    """
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(controller_mount_func(auth))

    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest_asyncio.fixture
async def token_auth_api_client(controller_mount_func):
    """Create an AsyncClient with TokenAuthHandler for testing."""
    runner = ApiTestRunner()
    auth = TokenAuthHandler()
    runner.mount(controller_mount_func(auth))

    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest_asyncio.fixture
async def keycloak_auth_api_client(controller_mount_func):
    """Create an AsyncClient with KeycloakAuthHandler for testing."""
    runner = ApiTestRunner()
    auth = KeycloakAuthHandler()
    runner.mount(controller_mount_func(auth))

    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


def create_my_account_controller_mount():
    """
    Helper function to create a controller mount function for MyAccountController.
    Use this as the controller_mount_func parameter for the client fixtures.
    """

    def mount_func(auth):
        from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController

        return MyAccountController(auth=auth).get_my_account()

    return mount_func


def create_token_controller_mount():
    """
    Helper function to create a controller mount function for TokenController.
    Use this as the controller_mount_func parameter for the client fixtures.
    """

    def mount_func(auth):
        from swiss_ai_hub.api.routes.token.token_controller import TokenController

        return TokenController(auth=auth)

    return mount_func


def create_thread_controller_mount():
    """
    Helper function to create a controller mount function for ThreadController.
    Use this as the controller_mount_func parameter for the client fixtures.
    """

    def mount_func(auth):
        from swiss_ai_hub.api.routes.thread.thread_controller import ThreadController

        return ThreadController(auth=auth)

    return mount_func
