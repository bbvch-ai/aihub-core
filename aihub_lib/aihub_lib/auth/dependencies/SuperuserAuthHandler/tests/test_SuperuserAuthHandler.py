from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserAuthHandler import SuperuserAuthHandler
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- Scenario Declaration ---

scenarios("features/superuser_auth_handler.feature")


# --- Fixtures ---


@pytest.fixture
def superuser_handler() -> SuperuserAuthHandler:
    """Create and return a SuperuserAuthHandler instance."""
    return SuperuserAuthHandler()


@pytest.fixture
def result_container() -> dict[str, object]:
    """Container for storing test results."""
    return {}


@pytest.fixture
def mock_request() -> Request:
    """Create a mock Request object."""
    scope = {
        "type": "http",
        "headers": [(b"authorization", b"Bearer e78a133a52a97f14bd413a567d53663c70c5fe65d01c9783b0bf72811f774a9e")],
        "method": "GET",
        "path": "/",
    }
    return Request(scope)


@pytest.fixture
def mock_bearer_token() -> HTTPAuthorizationCredentials:
    """Create a mock bearer token."""
    token = MagicMock(spec=HTTPAuthorizationCredentials)
    token.credentials = "e78a133a52a97f14bd413a567d53663c70c5fe65d01c9783b0bf72811f774a9e"
    return token


# --- Given Steps ---


@given(
    parsers.parse(
        'a superuser configuration with name "{name}", email "{email}", oid "{oid}", role "{role}", and token "{token}"'
    )
)
def setup_superuser_config(monkeypatch: pytest.MonkeyPatch, name: str, email: str, oid: str, role: str, token: str) -> None:
    """Set up the superuser configuration using environment variables."""
    monkeypatch.setenv("SUPERUSER_NAME", name)
    monkeypatch.setenv("SUPERUSER_EMAIL", email)
    monkeypatch.setenv("SUPERUSER_OID", oid)
    monkeypatch.setenv("SUPERUSER_ROLE", role)
    monkeypatch.setenv("SUPERUSER_TOKEN", token)


@given(parsers.parse('a bearer token with value "{token_value}"'))
def setup_bearer_token(
    mock_bearer_token: HTTPAuthorizationCredentials, token_value: str
) -> HTTPAuthorizationCredentials:
    """Set up a bearer token with a specific value."""
    mock_bearer_token.credentials = token_value
    return mock_bearer_token


# --- When Steps ---


@when(parsers.parse('I authenticate with token "{token}"'))
@async_test
async def authenticate_with_token(superuser_handler: SuperuserAuthHandler, token: str, result_container: dict[str, object]) -> None:
    """Authenticate using a token and store the result."""
    try:
        user = await superuser_handler.authenticate_token(token)
        result_container["user"] = user
        result_container["exception"] = None
    except HTTPException as e:
        result_container["user"] = None
        result_container["exception"] = e


@when("I authenticate with an empty token")
@async_test
async def authenticate_with_empty_token(superuser_handler: SuperuserAuthHandler, result_container: dict[str, object]) -> None:
    """Authenticate using an empty token and store the result."""
    try:
        user = await superuser_handler.authenticate_token("")
        result_container["user"] = user
        result_container["exception"] = None
    except HTTPException as e:
        result_container["user"] = None
        result_container["exception"] = e


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_user_name(result_container: dict[str, object], expected_name: str) -> None:
    """Check that the returned user has the expected name."""
    user = result_container.get("user")
    assert user is not None, "No user returned by SuperuserAuthHandler"
    assert user.name == expected_name, f'Expected user name "{expected_name}", got "{user.name}"'  # type: ignore[union-attr]


@then(parsers.parse('the returned user should have email "{expected_email}"'))
def check_user_email(result_container: dict[str, object], expected_email: str) -> None:
    """Check that the returned user has the expected email."""
    user = result_container.get("user")
    assert user is not None, "No user returned by SuperuserAuthHandler"
    assert user.email == expected_email, f'Expected user email "{expected_email}", got "{user.email}"'  # type: ignore[union-attr]


@then(parsers.parse('the returned user should have oid "{expected_oid}"'))
def check_user_oid(result_container: dict[str, object], expected_oid: str) -> None:
    """Check that the returned user has the expected oid."""
    user = result_container.get("user")
    assert user is not None, "No user returned by SuperuserAuthHandler"
    assert user.id == expected_oid, f'Expected user oid "{expected_oid}", got "{user.id}"'  # type: ignore[union-attr]


@then(parsers.parse('the returned user should have role "{expected_role}"'))
def check_user_role(result_container: dict[str, object], expected_role: str) -> None:
    """Check that the returned user has the expected role."""
    user = result_container.get("user")
    assert user is not None, "No user returned by SuperuserAuthHandler"
    assert expected_role in user.roles, f'Expected role "{expected_role}" not found in {user.roles}'  # type: ignore[union-attr]


@then(parsers.parse("an HTTPException with status code {status_code:d} should be raised"))
def check_http_exception(result_container: dict[str, object], status_code: int) -> None:
    """Check that an HTTPException with the expected status code was raised."""
    exception = result_container.get("exception")
    assert exception is not None, "No exception was raised"
    assert isinstance(exception, HTTPException), f"Expected HTTPException, got {type(exception)}"
    assert exception.status_code == status_code, f"Expected status code {status_code}, got {exception.status_code}"


@then(parsers.parse('the exception detail should be "{expected_detail}"'))
def check_exception_detail(result_container: dict[str, object], expected_detail: str) -> None:
    """Check that the exception has the expected detail message."""
    exception = result_container.get("exception")
    assert exception is not None, "No exception was raised"
    assert isinstance(exception, HTTPException), f"Expected HTTPException, got {type(exception)}"
    assert exception.detail == expected_detail, f'Expected detail "{expected_detail}", got "{exception.detail}"'


# --- Unit Tests ---


class TestSuperuserAuthHandler:
    """Unit tests for SuperuserAuthHandler."""

    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test authentication with a valid superuser token."""
        # Setup environment
        monkeypatch.setenv("SUPERUSER_NAME", "Super Admin")
        monkeypatch.setenv("SUPERUSER_EMAIL", "admin@example.com")
        monkeypatch.setenv("SUPERUSER_OID", "admin-123")
        monkeypatch.setenv("SUPERUSER_ROLE", "AIHubSuperuser")
        monkeypatch.setenv(
            "SUPERUSER_TOKEN", "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
        )

        handler = SuperuserAuthHandler()
        user = await handler.authenticate_token(
            "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
        )

        assert user.name == "Super Admin"
        assert user.email == "admin@example.com"
        assert user.id == "admin-123"
        assert "AIHubSuperuser" in user.roles

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test authentication with an invalid token."""
        monkeypatch.setenv(
            "SUPERUSER_TOKEN", "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
        )
        monkeypatch.setenv("SUPERUSER_NAME", "Super Admin")
        monkeypatch.setenv("SUPERUSER_EMAIL", "admin@example.com")
        monkeypatch.setenv("SUPERUSER_OID", "admin-123")
        monkeypatch.setenv("SUPERUSER_ROLE", "AIHubSuperuser")

        handler = SuperuserAuthHandler()

        with pytest.raises(HTTPException) as exc_info:
            await handler.authenticate_token("wrong-token")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token."

    @pytest.mark.asyncio
    async def test_authenticate_empty_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test authentication with an empty token."""
        monkeypatch.setenv(
            "SUPERUSER_TOKEN", "secret-token-4f517978885a2bd7b8065be4d16cc422c6d7c37292db9fbc7da23eabc8d35585"
        )
        monkeypatch.setenv("SUPERUSER_NAME", "Super Admin")
        monkeypatch.setenv("SUPERUSER_EMAIL", "admin@example.com")
        monkeypatch.setenv("SUPERUSER_OID", "admin-123")
        monkeypatch.setenv("SUPERUSER_ROLE", "AIHubSuperuser")

        handler = SuperuserAuthHandler()

        with pytest.raises(HTTPException) as exc_info:
            await handler.authenticate_token("")

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token missing."

    @pytest.mark.asyncio
    async def test_call_with_valid_bearer(self, monkeypatch: pytest.MonkeyPatch, mock_request: Request) -> None:
        """Test __call__ method with valid bearer token."""
        # Setup environment
        monkeypatch.setenv("SUPERUSER_NAME", "Super Admin")
        monkeypatch.setenv("SUPERUSER_EMAIL", "admin@example.com")
        monkeypatch.setenv("SUPERUSER_OID", "admin-123")
        monkeypatch.setenv("SUPERUSER_ROLE", "AIHubSuperuser")
        monkeypatch.setenv("SUPERUSER_TOKEN", "e78a133a52a97f14bd413a567d53663c70c5fe65d01c9783b0bf72811f774a9e")

        handler = SuperuserAuthHandler()

        # Mock the HTTPBearer security
        mock_bearer = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_bearer.credentials = "e78a133a52a97f14bd413a567d53663c70c5fe65d01c9783b0bf72811f774a9e"

        user = await handler(mock_request, mock_bearer)

        assert user.name == "Super Admin"
        assert user.email == "admin@example.com"
        assert user.id == "admin-123"
        assert "AIHubSuperuser" in user.roles

    @pytest.mark.asyncio
    async def test_handler_has_required_methods(self) -> None:
        """Test that SuperuserAuthHandler has the required methods."""
        handler = SuperuserAuthHandler()

        # Check that required methods are implemented
        assert hasattr(handler, "__call__")
        assert hasattr(handler, "authenticate_token")
