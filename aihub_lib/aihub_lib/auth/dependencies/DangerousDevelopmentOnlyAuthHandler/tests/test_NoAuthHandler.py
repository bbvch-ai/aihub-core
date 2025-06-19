import pytest
from fastapi import Request
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- Scenario Declaration ---


scenarios("features/no_auth_handler.feature")


# --- Fixtures ---


@pytest.fixture
def dummy_request() -> Request:
    """Create and return a dummy Request object."""
    scope = {"type": "http", "headers": [(b"host", b"testserver")], "method": "GET", "path": "/"}
    return Request(scope)


@pytest.fixture
def result_user() -> dict:
    """Container for storing the resulting user."""
    return {}


# --- Given Steps ---


@given(parsers.parse('a NoAuth configuration with name "{name}", email "{email}", oid "{oid}", and roles "{roles}"'))
def setup_no_auth_config(monkeypatch, name, email, oid, roles):
    """Set up the NoAuth configuration using environment variables."""
    roles_list = [role.strip() for role in roles.split(",")]
    monkeypatch.setenv("NAME", name)
    monkeypatch.setenv("EMAIL", email)
    monkeypatch.setenv("OID", oid)
    monkeypatch.setenv("ROLES", f"{roles_list}".replace("'", '"'))


# --- When Steps ---


@when("I invoke the DangerousDevelopmentOnlyAuthHandler with a dummy request")
@async_test
async def invoke_no_auth_handler(dummy_request: Request, result_user: dict) -> None:
    """Invoke the DangerousDevelopmentOnlyAuthHandler and store the returned user."""
    handler = DangerousDevelopmentOnlyAuthHandler()
    user = await handler(dummy_request)
    result_user["user"] = user


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_name(result_user: dict, expected_name: str) -> None:
    """Check that the returned user has the expected name."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert user.name == expected_name, f'Expected user name "{expected_name}", got "{user.name}"'


@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_preferred_username(result_user: dict, expected_email: str) -> None:
    """Check that the returned user has the expected preferred username."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert (
        user.preferred_username == expected_email
    ), f'Expected preferred username "{expected_email}", got "{user.preferred_username}"'


@then(parsers.parse('the returned user should have oid "{expected_oid}"'))
def check_oid(result_user: dict, expected_oid: str) -> None:
    """Check that the returned user has the expected oid."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert user.oid == expected_oid, f'Expected oid "{expected_oid}", got "{user.oid}"'


@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_roles(result_user: dict, role1: str, role2: str) -> None:
    """Check that the returned user has the expected roles."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert set(user.roles) == {role1, role2}, f"Expected roles {role1}, {role2}, got {user.roles}"
