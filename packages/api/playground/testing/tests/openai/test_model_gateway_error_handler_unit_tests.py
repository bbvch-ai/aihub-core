from openai import APIConnectionError, APIStatusError, APITimeoutError
from swiss_ai_hub.core.exceptions import ModelGatewayErrorHandler

from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner


class TestApiRunnerInheritsTheHandler:
    """The handler's own behaviour is covered in ``packages/core``. What only this scope can prove
    is that ``ApiRunner`` overriding ``_get_api_app`` still ends up with the registration — losing
    it here would silently restore the opaque 500 on every model-backed endpoint."""

    def test_api_runner_registers_every_gateway_error(self):
        handlers = ApiTestRunner()._api_app.exception_handlers

        assert handlers[APIStatusError] == ModelGatewayErrorHandler.handle_status_error
        assert handlers[APITimeoutError] == ModelGatewayErrorHandler.handle_timeout_error
        assert handlers[APIConnectionError] == ModelGatewayErrorHandler.handle_connection_error
