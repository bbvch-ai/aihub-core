import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker, AccessLevel

scenarios("./features/access_checker.feature")


@pytest.fixture
def context():
    """A dictionary to hold state between BDD steps."""
    return {}


@pytest.fixture
def access_rules():
    """Holds user access rules between BDD steps."""
    return []


@pytest.fixture
def tenant_access_rules():
    """Holds tenant access rules between BDD steps."""
    return []


@given(parsers.parse("no access rules"))
def given_no_access_rules(access_rule: str, access_rules: list[str]):
    """Clears all user access rules."""
    access_rules.clear()


@given(parsers.parse('the access rule "{access_rule}"'))
def given_access_rules(access_rule: str, access_rules: list[str]):
    """Adds an access rule to the user's list of access roles."""
    access_rules.append(access_rule)


@given(parsers.parse('the tenant access rule "{tenant_access_rule}"'))
def given_tenant_access_rules(tenant_access_rule: str, tenant_access_rules: list[str]):
    """Adds an access rule to the tenant's list of access rules."""
    tenant_access_rules.append(tenant_access_rule)


@when(parsers.parse('the access checker checks for the permission "{permission_template}"'))
def check_permission(context, access_rules: list[str], tenant_access_rules: list[str], permission_template: str):
    """Initializes AccessChecker and stores the result or any exception."""
    try:
        # Use tenant access rules if provided, otherwise default to full access for backward compatibility
        tenant_rules = tenant_access_rules if tenant_access_rules else ["aihub.admin.>"]
        checker = AccessChecker(access_rules, tenant_access_rules=tenant_rules)
        result = checker.access_level(permission_template)
        context["result"] = result
        context["exception"] = None
    except Exception as e:
        context["result"] = None
        context["exception"] = e


@when(parsers.parse('the access checker checks for the permission "{user_permission_template}"'))
def check_user_level_permission(
    context, access_rules: list[str], tenant_access_rules: list[str], user_permission_template: str
):
    """Alias for the main 'when' step for clarity in admin scenarios."""
    check_permission(context, access_rules, tenant_access_rules, user_permission_template)


@then(parsers.parse("the result should be {expected_level}"))
def assert_result(context, expected_level: str):
    """Asserts that the permission check returned the expected AccessLevel."""
    assert context.get("exception") is None, f"Expected no exception, but got {context.get('exception')}"
    try:
        expected = AccessLevel[expected_level]
    except KeyError:
        pytest.fail(f"Invalid expected level '{expected_level}' in feature file.")

    assert context.get("result") is expected, f"Expected {expected}, but got {context.get('result')}"


@then("a ValueError should be raised")
def assert_value_error(context):
    """Asserts that a ValueError was raised during the permission check."""
    exception = context.get("exception")
    assert exception is not None, "Expected a ValueError, but no exception was raised."
    assert isinstance(exception, ValueError), f"Expected ValueError, but got {type(exception).__name__}."
