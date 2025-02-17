import pytest
from fastapi import Request
from pytest_bdd import given, parsers, scenario, then, when

from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --------------------------
# Scenario Declaration
# --------------------------


@scenario("features/no_auth_handler.feature", "NoAuthHandler returns a static user")
def test_no_auth_handler():
    pass


# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def dummy_request():
    scope = {"type": "http", "headers": [(b"host", b"testserver")], "method": "GET", "path": "/"}
    return Request(scope)


@pytest.fixture
def result_user():
    return {}


# --------------------------
# Given Steps
# --------------------------


@given(parsers.parse('a NoAuth configuration with name "{name}", email "{email}", oid "{oid}", and roles "{roles}"'))
def setup_no_auth_config(monkeypatch, name, email, oid, roles):
    monkeypatch.setenv("NAME", name)
    monkeypatch.setenv("EMAIL", email)
    monkeypatch.setenv("OID", oid)
    roles_list = [r.strip() for r in roles.split(",")]
    monkeypatch.setenv("ROLES", f"{roles_list}".replace("'", '"'))


# --------------------------
# When Steps
# --------------------------


@when("I invoke the NoAuthHandler with a dummy request")
@async_test
async def invoke_no_auth_handler(dummy_request, result_user):
    handler = NoAuthHandler()
    user = await handler(dummy_request)
    result_user["user"] = user


# --------------------------
# Then Steps
# --------------------------


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_name(result_user, expected_name):
    user = result_user.get("user")
    assert user is not None, "No user returned by NoAuthHandler"
    assert user.name == expected_name


@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_preferred_username(result_user, expected_email):
    user = result_user.get("user")
    assert user.preferred_username == expected_email


@then(parsers.parse('the returned user should have oid "{expected_oid}"'))
def check_oid(result_user, expected_oid):
    user = result_user.get("user")
    assert user.oid == expected_oid


@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_roles(result_user, role1, role2):
    user = result_user.get("user")
    assert set(user.roles) == {role1, role2}
