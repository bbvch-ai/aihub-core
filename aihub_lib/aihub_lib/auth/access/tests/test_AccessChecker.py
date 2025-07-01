import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Assuming the refactored AccessChecker is in this path
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity

# Point scenarios to the feature file
scenarios("./features/access_checker.feature")


@pytest.fixture
def context():
    """A dictionary to hold state between BDD steps."""
    return {}


@given('a user with the name "Test User" and email "test@example.com"', target_fixture="user_identity")
def user_identity():
    """Creates a base UserIdentity object with an empty list of roles."""
    return UserIdentity(id="test-user-id", name="Test User", email="test@example.com", roles=[])


@given(parsers.parse('the user has the role "{role}"'))
def add_user_role(user_identity: UserIdentity, role: str):
    """Adds a role to the user's list of roles."""
    user_identity.roles.append(role)


@when(parsers.parse('the access checker checks for the permission "{permission_template}"'))
def check_permission(context, user_identity: UserIdentity, permission_template: str):
    """
    Initializes the AccessChecker and calls has_permission, storing the result
    or any exception in the context.
    """
    try:
        checker = AccessChecker(user_identity)
        result = checker.has_permission(permission_template)
        context["result"] = result
        context["exception"] = None
    except Exception as e:
        context["result"] = None
        context["exception"] = e


@when(parsers.parse('the access checker checks for the user-level permission "{user_permission_template}"'))
def check_user_level_permission(context, user_identity: UserIdentity, user_permission_template: str):
    """Alias for the main 'when' step for clarity in admin scenarios."""
    check_permission(context, user_identity, user_permission_template)


@then(parsers.parse("the result should be {has_permission}"))
def assert_result(context, has_permission: str):
    """Asserts that the permission check returned the expected boolean value."""
    expected = has_permission.lower() == "true"
    assert context.get("exception") is None, f"Expected no exception, but got {context.get('exception')}"
    assert context.get("result") is expected, f"Expected {expected}, but got {context.get('result')}"


@then("a ValueError should be raised")
def assert_value_error(context):
    """Asserts that a ValueError was raised during the permission check."""
    exception = context.get("exception")
    assert exception is not None, "Expected a ValueError, but no exception was raised."
    assert isinstance(exception, ValueError), f"Expected ValueError, but got {type(exception).__name__}."

