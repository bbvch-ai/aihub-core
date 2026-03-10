import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings


@pytest.fixture(scope="module")
def mongo_db():
    """Set up MongoDB connection for testing."""
    config = AIHubSettings()
    connect(
        db=config.MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture
def clean_test_fields():
    """
    Helper to clean up test-specific fields from API responses.
    Use this to remove fields that are tested separately or are non-deterministic.
    """

    def clean_fields(user_data, fields_to_remove=None):
        """Remove specified fields from user data dict."""
        if fields_to_remove is None:
            fields_to_remove = ["dashboard", "access", "last_accessed"]

        cleaned_data = user_data.copy()
        for field in fields_to_remove:
            cleaned_data.pop(field, None)
        return cleaned_data

    return clean_fields
