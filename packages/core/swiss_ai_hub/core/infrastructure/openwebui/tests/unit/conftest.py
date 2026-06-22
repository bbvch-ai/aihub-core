from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

_MOCK_SCIM = MagicMock(name="mock_scim_client")


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
        return prov
