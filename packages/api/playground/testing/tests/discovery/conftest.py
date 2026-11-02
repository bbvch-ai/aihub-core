from unittest.mock import patch

import pytest

from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService


@pytest.fixture(autouse=True)
def no_supported_features():
    """The sync reads each class's supported features from Mongo; these tests run without one."""
    with patch.object(AgentEndpointsDiscoveryService, "_supported_features_by_class", return_value={}) as mock:
        yield mock
