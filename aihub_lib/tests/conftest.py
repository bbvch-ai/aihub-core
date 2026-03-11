from unittest.mock import MagicMock, patch

import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://open-webui:8080"
    settings.SECRET_KEY = MagicMock()
    settings.SECRET_KEY.get_secret_value.return_value = "sk-test"
    settings.SCIM_TOKEN = MagicMock()
    settings.SCIM_TOKEN.get_secret_value.return_value = "scim-test"
    settings.SERVICE_ACCOUNT_ID = "00000000-0000-4000-a000-000000000001"
    return settings


@pytest.fixture
def provisioner(mock_settings: MagicMock) -> OpenWebuiProvisioner:
    with patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.OpenWebuiSettings", return_value=mock_settings):
        return OpenWebuiProvisioner()
