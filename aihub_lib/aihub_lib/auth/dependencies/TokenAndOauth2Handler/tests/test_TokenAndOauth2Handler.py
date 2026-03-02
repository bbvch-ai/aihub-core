from typing import Any

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.dependencies.KeycloakAuthHandler.KeycloakSettings import KeycloakSettings
from aihub_lib.auth.identity.TenantIdentity import TenantIdentity
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- Dummy authentication handler implementations ---


class DummySuccessAuth:
    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials | None = None
    ) -> UserIdentity:
        """Return a successful authenticated user."""
        return await self.authenticate_token("dummy_token")

    async def authenticate_token(self, token: str) -> UserIdentity:
        """Return a successful authenticated user."""
        return UserIdentity(
            name="Dummy Success",
            email="dummy@success.com",
            id="1",
            roles=["user"],
            acting_within_tenant=TenantIdentity(id="t1", name="Tenant1", access_rules=["aihub.admin.>"]),
        )


class DummyFailureAuth:
    def __init__(self, detail: str, status_code: int = 401) -> None:
        self.detail = detail
        self.status_code = status_code

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials | None = None
    ) -> UserIdentity:
        """Raise HTTPException with a 401 error."""
        raise HTTPException(status_code=self.status_code, detail=self.detail)

    async def authenticate_token(self, token: str) -> UserIdentity:
        """Raise HTTPException with a 401 error."""
        raise HTTPException(status_code=self.status_code, detail=self.detail)


class DummyFailureNon401:
    def __init__(self, detail: str) -> None:
        self.detail = detail

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials | None = None
    ) -> UserIdentity:
        """Raise HTTPException with a non-401 error."""
        raise HTTPException(status_code=500, detail=self.detail)

    async def authenticate_token(self, token: str) -> UserIdentity:
        """Raise HTTPException with a non-401 error."""
        raise HTTPException(status_code=500, detail=self.detail)


# --- Fixtures to store context ---


@pytest.fixture
def multi_auth_result() -> dict[str, Any]:
    """Container for storing the multi auth handler result."""
    return {}


@pytest.fixture
def multi_auth_error() -> dict[str, Any]:
    """Container for storing the multi auth handler error."""
    return {}


@pytest.fixture
def dummy_request() -> Request:
    """Create and return a dummy Request object."""
    scope: dict[str, Any] = {"type": "http", "headers": [], "method": "GET", "path": "/"}
    return Request(scope)


# --- Scenario Declarations ---


scenarios("features/token_and_oauth2_handler.feature")


# --- Given step: Build the MultiAuthHandler from a data table ---


@given(
    parsers.parse('a Keycloak configuration with url "{url}" and realm "{realm}"'),
    target_fixture="keycloak_config",
)
def keycloak_config(monkeypatch: pytest.MonkeyPatch, url: str, realm: str) -> KeycloakSettings:
    """Set the Keycloak configuration environment variables."""
    monkeypatch.setenv("KEYCLOAK_URL", url)
    monkeypatch.setenv("KEYCLOAK_REALM", realm)
    return KeycloakSettings()


@given(parsers.parse("a multi auth handler composed of:"), target_fixture="multi_auth_instance")
def given_multi_auth_handler(datatable: list[list[str]]) -> "TokenAndOauth2Handler":  # type: ignore[name-defined] # noqa: F821
    from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler

    """Build a MultiAuthHandler from the provided table."""
    headers = datatable[0]
    handlers: list[DummySuccessAuth | DummyFailureAuth | DummyFailureNon401] = []
    for row in datatable[1:]:
        row_data = dict(zip(headers, row, strict=False))
        behavior = row_data["behavior"].strip().lower()
        detail = row_data["detail"].strip() if row_data["detail"] else ""
        if behavior == "success":
            handlers.append(DummySuccessAuth())
        elif behavior == "failure_401":
            handlers.append(DummyFailureAuth(detail=detail, status_code=401))
        elif behavior == "failure_non_401":
            handlers.append(DummyFailureNon401(detail=detail))
    return TokenAndOauth2Handler(bearer_handlers=handlers, oauth2_handlers=[])


# --- When steps ---


@when("I invoke the multi auth handler")
@async_test
async def invoke_multi_auth(
    multi_auth_instance: "TokenAndOauth2Handler",  # type: ignore[name-defined] # noqa: F821
    multi_auth_result: dict[str, Any],
    dummy_request: Request,
) -> None:
    """Invoke the multi auth handler and store the returned user."""
    try:
        bearer_security = await HTTPBearer(auto_error=False)(dummy_request)
        keycloak_settings = KeycloakSettings()
        oauth_security = await keycloak_settings.OPTIONAL_SCHEMA(dummy_request)
        user = await multi_auth_instance(dummy_request, bearer_security, oauth_security)
        multi_auth_result["user"] = user
    except HTTPException as e:
        pytest.fail(f"MultiAuthHandler raised an unexpected exception: {e.detail}")


# --- Then steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_multi_auth_user_name(multi_auth_result: dict[str, Any], expected_name: str) -> None:
    """Check that the returned user has the expected name."""
    user = multi_auth_result.get("user")
    assert user is not None, "No user was returned"
    assert user.name == expected_name, f'Expected user name "{expected_name}", got "{user.name}"'
