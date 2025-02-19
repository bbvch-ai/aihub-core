import pytest
from fastapi import HTTPException, Request
from pytest_bdd import given, parsers, scenario, scenarios, then, when

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.MultiAuthHandler.MultiAuthHandler import MultiAuthHandler
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- Dummy authentication handler implementations ---


class DummySuccessAuth(AuthHandler):
    async def __call__(self, request: Request) -> AuthenticatedUser:
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

    async def __call__(self, request: Request) -> AuthenticatedUser:
        """Raise HTTPException with a 401 error."""
        raise HTTPException(status_code=self.status_code, detail=self.detail)


class DummyFailureNon401(AuthHandler):
    def __init__(self, detail: str):
        self.detail = detail

    async def __call__(self, request: Request) -> AuthenticatedUser:
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


@given(parsers.parse("a multi auth handler composed of:"), target_fixture="multi_auth_instance")
def given_multi_auth_handler(datatable: list[list[str]]) -> MultiAuthHandler:
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
    return MultiAuthHandler(*handlers)


# --- When steps ---


@when("I invoke the multi auth handler")
@async_test
async def invoke_multi_auth(multi_auth_instance: MultiAuthHandler, multi_auth_result: dict, dummy_request: Request):
    """Invoke the multi auth handler and store the returned user."""
    try:
        user = await multi_auth_instance(dummy_request)
        multi_auth_result["user"] = user
    except HTTPException as e:
        pytest.fail(f"MultiAuthHandler raised an unexpected exception: {e.detail}")


@when("I invoke the multi auth handler expecting error")
@async_test
async def invoke_multi_auth_expect_error(
    multi_auth_instance: MultiAuthHandler, multi_auth_error: dict, dummy_request: Request
):
    """Invoke the multi auth handler and store the error detail."""
    with pytest.raises(HTTPException) as excinfo:
        await multi_auth_instance(dummy_request)
    multi_auth_error["error"] = excinfo.value.detail


# --- Then steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_multi_auth_user_name(multi_auth_result: dict, expected_name: str):
    """Check that the returned user has the expected name."""
    user = multi_auth_result.get("user")
    assert user is not None, "No user was returned"
    assert user.name == expected_name, f'Expected user name "{expected_name}", got "{user.name}"'


@then(parsers.parse('I should receive an HTTP error with detail "{expected_detail}"'))
def check_multi_auth_error(multi_auth_error: dict, expected_detail: str):
    """Check that the error detail matches the expected detail."""
    error = multi_auth_error.get("error")
    assert error == expected_detail, f'Expected error detail "{expected_detail}", got "{error}"'
