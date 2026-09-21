from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

_MOCK_SCIM = MagicMock(name="mock_scim_client")


@pytest.fixture(autouse=True)
def unregistered_base_models():
    """Defaults every sync's base-registry read to the healthy state — no managed rows yet.

    Tests exercising specific base rows shadow this with their own instance-level
    ``list_base_models`` patch, which takes precedence over this class-level one.
    """
    with patch.object(OpenWebuiClient, "list_base_models", return_value=[]):
        yield


@asynccontextmanager
async def _mock_scim_session():
    yield _MOCK_SCIM


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://open-webui:8080"
    settings.SECRET_KEY = MagicMock()
    settings.SECRET_KEY.get_secret_value.return_value = "sk-test"
    settings.SCIM_TOKEN = MagicMock()
    settings.SCIM_TOKEN.get_secret_value.return_value = "scim-test-token"
    settings.SERVICE_ACCOUNT_ID = "00000000-0000-4000-a000-000000000001"
    settings.MODEL_NAME_LOCALE = "en"
    return settings


@pytest.fixture
def mock_redis() -> MagicMock:
    redis = MagicMock()
    lock = MagicMock()
    lock.acquire = AsyncMock(return_value=True)
    lock.release = AsyncMock()
    redis.lock.return_value = lock
    return redis


@pytest.fixture
def provisioner(mock_settings: MagicMock, mock_redis: MagicMock) -> OpenWebuiProvisioner:
    with patch(
        "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.OpenWebuiSettings",
        return_value=mock_settings,
    ):
        prov = OpenWebuiProvisioner(redis=mock_redis)
        prov._openwebui.scim_session = _mock_scim_session
        # Defaults _delete_legacy_preset_models's read to the healthy state — nothing to migrate.
        # Scoped to this instance (not OpenWebuiClient globally) so it doesn't affect
        # test_openwebui_client.py's direct tests of the real list_models implementation. Tests
        # exercising the migration itself override this with their own patch.object call.
        prov._openwebui.list_models = AsyncMock(return_value=[])
        return prov
