import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- Dummy authentication handler implementations ---


class DummySuccessAuth(AuthHandler):
    async def __call__(self, *args, **kwargs) -> AuthenticatedUser:
        """Return a successful authenticated user."""
        return AuthenticatedUser(
            name="Dummy Success",
            preferred_username="dummy@success.com",
            oid="1",
            roles=["user"],
        )


class DummyFailureAuth(AuthHandler):
    def __init__(self, detail: str, status_code: int = 401):
        self.detail = detail
        self.status_code = status_code

    async def __call__(self, *args, **kwargs) -> AuthenticatedUser:
        """Raise HTTPException with a 401 error."""
        raise HTTPException(status_code=self.status_code, detail=self.detail)


class DummyFailureNon401(AuthHandler):
    def __init__(self, detail: str):
        self.detail = detail

    async def __call__(self, *args, **kwargs) -> AuthenticatedUser:
        """Raise HTTPException with a non-401 error."""
        raise HTTPException(status_code=500, detail=self.detail)


# --- Fixtures to store context ---


@pytest.fixture
def multi_auth_result() -> dict:
    """Container for storing the multi auth handler result."""
    return {}


@pytest.fixture
def multi_auth_error() -> dict:
    """Container for storing the multi auth handler error."""
    return {}


@pytest.fixture
def dummy_request() -> Request:
    """Create and return a dummy Request object."""
    scope = {"type": "http", "headers": [], "method": "GET", "path": "/"}
    return Request(scope)


# --- Scenario Declarations ---


scenarios("features/multi_auth_handler.feature")


# --- Given step: Build the MultiAuthHandler from a data table ---


@given(
    parsers.parse(
        'an OAuth2 configuration with tenant_id "{tenant_id}", client_id "{client_id}", and authority_url "{authority_url}"'
    ),
    target_fixture="oauth2_config",
)
def oauth2_config(monkeypatch, tenant_id: str, client_id: str, authority_url: str) -> OAuth2Config:
    """Set the OAuth2 configuration environment variables."""
    monkeypatch.setenv("TENANT_ID", tenant_id)
    monkeypatch.setenv("CLIENT_ID", client_id)
    monkeypatch.setenv("AUTHORITY_URL", authority_url)
    return OAuth2Config()


@given(parsers.parse("a multi auth handler composed of:"), target_fixture="multi_auth_instance")
def given_multi_auth_handler(datatable: list[list[str]]) -> "TokenAndOauth2Handler":
    from aihub_lib.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler

    """Build a MultiAuthHandler from the provided table."""
    headers = datatable[0]
    handlers: list[AuthHandler] = []
    for row in datatable[1:]:
        row_data = dict(zip(headers, row))
        behavior = row_data["behavior"].strip().lower()
        detail = row_data["detail"].strip() if row_data["detail"] else ""
        if behavior == "success":
            handlers.append(DummySuccessAuth())
        elif behavior == "failure_401":
            handlers.append(DummyFailureAuth(detail=detail, status_code=401))
        elif behavior == "failure_non_401":
            handlers.append(DummyFailureNon401(detail=detail))
    return TokenAndOauth2Handler(*handlers)


# --- When steps ---


@when("I invoke the multi auth handler")
@async_test
async def invoke_multi_auth(
    multi_auth_instance: "TokenAndOauth2Handler", multi_auth_result: dict, dummy_request: Request
):
    """Invoke the multi auth handler and store the returned user."""
    try:
        bearer_security = await HTTPBearer(auto_error=False)(dummy_request)
        oauth_security = await OAuth2Config().OPTIONAL_SCHEMA(dummy_request)
        user = await multi_auth_instance(dummy_request, bearer_security, oauth_security)
        multi_auth_result["user"] = user
    except HTTPException as e:
        pytest.fail(f"MultiAuthHandler raised an unexpected exception: {e.detail}")


# --- Then steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_multi_auth_user_name(multi_auth_result: dict, expected_name: str):
    """Check that the returned user has the expected name."""
    user = multi_auth_result.get("user")
    assert user is not None, "No user was returned"
    assert user.name == expected_name, f'Expected user name "{expected_name}", got "{user.name}"'
