import pytest
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from mongoengine import connect, disconnect
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess

from pytest_bdd import scenario, given, when, then, parsers
from fastapi import Request, HTTPException

from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.persistence.access.entities.AccessToken import AccessToken, ApiUser
from aihub_lib.testing.asyncio_utils.bdd import async_test


# -----------------------------------------------------------------------------
# MongoDB Connection Fixture
# -----------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def mongo_connection():
    """
    Connect to the MongoDB using the connection string from CosmosAccess.
    This fixture is automatically used for all tests in this module.
    """
    connection = connect(
        db="aihub",
        host=CosmosAccess().get_connection_string(),
    )
    yield connection
    disconnect()


# -----------------------------------------------------------------------------
# Scenario Declaration
# -----------------------------------------------------------------------------
@scenario("features/token_auth_handler.feature", "Valid token returns authenticated user")
def test_token_auth_handler():
    pass


# -----------------------------------------------------------------------------
# Fixtures for Test Context and Cleanup
# -----------------------------------------------------------------------------
@pytest.fixture
def token_context():
    """
    Stores values needed across steps, including the inserted token string and document id.
    """
    return {}

@pytest.fixture
def token_context_result():
    """
    Fixture to store the result (the authenticated user) from TokenAuthHandler.
    """
    return {}

@pytest.fixture
def cleanup_token():
    """
    Collects inserted token documents for cleanup after the test.
    """
    inserted_tokens = []
    yield inserted_tokens
    for token_doc in inserted_tokens:
        token_doc.delete()


def create_dummy_request(headers: dict) -> Request:
    """
    Create a dummy FastAPI Request with the provided headers.
    ASGI spec requires header names to be lower-case.
    """
    headers_list = [(k.lower().encode("utf8"), v.encode("utf8")) for k, v in headers.items()]
    scope = {"type": "http", "headers": headers_list, "method": "GET", "path": "/"}
    return Request(scope)


# -----------------------------------------------------------------------------
# Given Steps
# -----------------------------------------------------------------------------
@given(parsers.parse('a token exists in the database with user details: name "{name}", email "{email}", and roles "{roles}"'))
def insert_token_document(token_context, cleanup_token, name, email, roles):
    """
    Inserts a token document into the test MongoDB with the specified user details.
    The token format is "<object_id>.<random_string>".
    Roles are provided as a comma-separated string.
    """
    object_id = ObjectId()
    token_str = f"{str(object_id)}.random123"

    roles_list = [r.strip() for r in roles.split(",")]

    api_user = ApiUser(
        name=name,
        preferred_username=email,
        roles=roles_list,
    )

    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    token_doc = AccessToken(id=object_id, token=token_str, expiry_date=expiry, roles=roles_list, user=api_user)
    token_doc.save()  # Insert the document into the database

    token_context["token_str"] = token_str
    token_context["object_id"] = str(object_id)

    cleanup_token.append(token_doc)


# -----------------------------------------------------------------------------
# When Steps
# -----------------------------------------------------------------------------
@when("I invoke the TokenAuthHandler with an Authorization header using the token")
@async_test
async def invoke_token_auth_handler(token_context, token_context_result):
    """
    Create a dummy request with the Authorization header using the inserted token,
    invoke the TokenAuthHandler, and store the returned authenticated user.
    """
    token_str = token_context["token_str"]
    headers = {"Authorization": f"Bearer {token_str}"}
    request = create_dummy_request(headers)
    handler = TokenAuthHandler()
    try:
        user = await handler(request)
    except HTTPException as e:
        pytest.fail(f"TokenAuthHandler raised an exception: {e.detail}")
    token_context_result["user"] = user


# -----------------------------------------------------------------------------
# Then Steps
# -----------------------------------------------------------------------------
@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_name(token_context_result, expected_name):
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by TokenAuthHandler"
    assert user.name == expected_name

@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_preferred_username(token_context_result, expected_email):
    user = token_context_result.get("user")
    assert user.preferred_username == expected_email

@then("the returned user should have oid matching the token's id")
def check_oid(token_context_result, token_context):
    user = token_context_result.get("user")
    expected_oid = token_context.get("object_id")
    assert user.oid == expected_oid

@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_roles(token_context_result, role1, role2):
    user = token_context_result.get("user")
    assert set(user.roles) == {role1, role2}
