import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.incident.incident_controller import IncidentController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

INCIDENTS_BASE = "/api/v1/incidents"


@pytest.fixture
def api(configured: bool):
    runner = ApiTestRunner()
    runner.mount(IncidentController(auth=TestAuthHandler()).get_incident_availability().get_incident_form())
    app = runner.create_app()
    # No `with`: entering the client would run the lifespan, which needs the whole infrastructure
    # and would set `incident_client` from the environment. This test decides the answer itself,
    # and a stand-in is enough — the endpoint only asks whether a client exists.
    app.state.incident_client = object() if configured else None
    return TestClient(app, raise_server_exceptions=True)


@pytest.mark.parametrize("configured", [False])
def test_should_answer_200_with_enabled_false_when_no_repository_is_configured(api) -> None:
    """A 404 here would be toasted by the shell on every page load of every deployment without the feature."""
    response = api.get(f"{INCIDENTS_BASE}/availability")

    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": False}


@pytest.mark.parametrize("configured", [True])
def test_should_answer_enabled_true_when_a_repository_is_configured(api) -> None:
    response = api.get(f"{INCIDENTS_BASE}/availability")

    assert response.status_code == 200, response.text
    assert response.json() == {"enabled": True}


@pytest.mark.parametrize("configured", [False])
def test_should_keep_answering_404_for_the_form_when_unconfigured(api) -> None:
    response = api.get(f"{INCIDENTS_BASE}/form")

    assert response.status_code == 404, response.text
