"""Unified test client fixture utilities for consistent test setup."""

import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"


@pytest_asyncio.fixture
async def development_auth_api_client(controller_mount_func):
    """
    Create an AsyncClient with DangerousDevelopmentOnlyAuthHandler for testing.

    Usage:
        @pytest.mark.asyncio
        async def test_something(development_auth_api_client):
            def mount_controller(auth):
                return MyAccountController(auth=auth).get_my_account()

            client = await development_auth_api_client(mount_controller)
            response = await client.get("/api/v1/my-account")
    """
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler()
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
async def oauth2_auth_api_client(controller_mount_func):
    """Create an AsyncClient with OAuth2AuthHandler for testing."""
    runner = ApiTestRunner()
    auth = OAuth2AuthHandler()
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
        from aihub_api.routes.my_account.MyAccountController import MyAccountController

        return MyAccountController(auth=auth).get_my_account()

    return mount_func


def create_token_controller_mount():
    """
    Helper function to create a controller mount function for TokenController.
    Use this as the controller_mount_func parameter for the client fixtures.
    """

    def mount_func(auth):
        from aihub_api.routes.token.TokenController import TokenController

        return TokenController(auth=auth)

    return mount_func


def create_thread_controller_mount():
    """
    Helper function to create a controller mount function for ThreadController.
    Use this as the controller_mount_func parameter for the client fixtures.
    """

    def mount_func(auth):
        from aihub_api.routes.thread.ThreadController import ThreadController

        return ThreadController(auth=auth)

    return mount_func
