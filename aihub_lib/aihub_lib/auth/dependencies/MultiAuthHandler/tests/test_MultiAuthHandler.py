import pytest
from fastapi import HTTPException, Request
from pytest_bdd import given, parsers, scenario, then, when

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.MultiAuthHandler.MultiAuthHandler import MultiAuthHandler
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- Dummy authentication handler implementations ---


class DummySuccessAuth(AuthHandler):
    async def __call__(self, request: Request) -> AuthenticatedUser:
        return AuthenticatedUser(name="Dummy Success", preferred_username="dummy@success.com", oid="1", roles=["user"])


class DummyFailureAuth(AuthHandler):
    def __init__(self, detail, status_code=401):
        self.detail = detail
        self.status_code = status_code

    async def __call__(self, request: Request) -> AuthenticatedUser:
        raise HTTPException(status_code=self.status_code, detail=self.detail)


class DummyFailureNon401(AuthHandler):
    def __init__(self, detail):
        self.detail = detail

    async def __call__(self, request: Request) -> AuthenticatedUser:
        raise HTTPException(status_code=500, detail=self.detail)


# --- Fixtures to store context ---


@pytest.fixture
def multi_auth_result():
    return {}


@pytest.fixture
def multi_auth_error():
    return {}


# --- Helper to create a dummy request ---


def create_dummy_request() -> Request:
    scope = {"type": "http", "headers": [], "method": "GET", "path": "/"}
    return Request(scope)


# --- Scenario declarations ---


@scenario("features/multi_auth_handler.feature", "First handler succeeds")
def test_multi_auth_first_success():
    pass


@scenario("features/multi_auth_handler.feature", "First fails with 401, second succeeds")
def test_multi_auth_first_fail_second_success():
    pass


@scenario("features/multi_auth_handler.feature", "All handlers fail with 401 errors")
def test_multi_auth_all_fail():
    pass


@scenario("features/multi_auth_handler.feature", "A handler fails with a non-401 error")
def test_multi_auth_non_401_fail():
    pass


# --- Given step: Build the MultiAuthHandler from a data table ---


@given(parsers.parse("a multi auth handler composed of:"), target_fixture="multi_auth_instance")
def given_multi_auth_handler(datatable):
    """
    Build a MultiAuthHandler from the provided table.
    The table is expected to have columns:
      - handler_name (informational)
      - behavior: "success", "failure_401", or "failure_non_401"
      - detail: error detail (if applicable)
    """
    # The first row is assumed to be the header.
    headers = datatable[0]
    handlers = []
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
async def invoke_multi_auth(multi_auth_instance, multi_auth_result):
    request = create_dummy_request()
    try:
        user = await multi_auth_instance(request)
        multi_auth_result["user"] = user
    except HTTPException as e:
        pytest.fail(f"MultiAuthHandler raised an unexpected exception: {e.detail}")


@when("I invoke the multi auth handler expecting error")
@async_test
async def invoke_multi_auth_expect_error(multi_auth_instance, multi_auth_error):
    request = create_dummy_request()
    try:
        await multi_auth_instance(request)
        pytest.fail("MultiAuthHandler did not raise an exception")
    except HTTPException as e:
        multi_auth_error["error"] = e.detail


# --- Then steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_multi_auth_user_name(multi_auth_result, expected_name):
    user = multi_auth_result.get("user")
    assert user is not None, "No user was returned"
    assert user.name == expected_name


@then(parsers.parse('I should receive an HTTP error with detail "{expected_detail}"'))
def check_multi_auth_error(multi_auth_error, expected_detail):
    error = multi_auth_error.get("error")
    assert error == expected_detail
