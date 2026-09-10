import httpx
import pytest
from openai import APIConnectionError, APITimeoutError, BadRequestError, RateLimitError

from swiss_ai_hub.core.exceptions.model_gateway_error_handler import ModelGatewayErrorHandler

pytestmark = pytest.mark.unit

UPSTREAM_URL = "http://litellm:4000/chat/completions"
UPSTREAM_MESSAGE = (
    "litellm.BadRequestError: OpenAIException - /audio/transcriptions: "
    "Invalid model name passed in model=whisper-large-v3."
)
UPSTREAM_BODY = {"error": {"message": UPSTREAM_MESSAGE, "type": None, "param": None, "code": "400"}}


def _status_error[T: Exception](error_class: type[T], status_code: int) -> T:
    request = httpx.Request("POST", UPSTREAM_URL)
    response = httpx.Response(status_code, request=request, json=UPSTREAM_BODY)
    return error_class(f"Error code: {status_code}", response=response, body=UPSTREAM_BODY)


class TestCauseIsReadableOutsideTheHttpBoundary:
    """Agent steps fail through the same SDK but report through NATS and logs, where `str(e)` is
    the `Error code: N - {…}` wrapper. That is searchable but not readable, and it reached the chat
    UI the same way."""

    @pytest.mark.parametrize(("error_class", "status"), [(BadRequestError, 400), (RateLimitError, 429)])
    def test_gateway_errors_are_unwrapped(self, error_class: type[Exception], status: int):
        assert ModelGatewayErrorHandler.cause_of(_status_error(error_class, status)) == UPSTREAM_MESSAGE

    def test_wrapper_prefix_is_gone(self):
        cause = ModelGatewayErrorHandler.cause_of(_status_error(BadRequestError, 400))

        assert not cause.startswith("Error code:")

    @pytest.mark.parametrize(
        "exception",
        [
            ValueError("a step bug that has nothing to do with the gateway"),
            APITimeoutError(request=httpx.Request("POST", UPSTREAM_URL)),
            APIConnectionError(request=httpx.Request("POST", UPSTREAM_URL)),
        ],
    )
    def test_everything_else_is_returned_unchanged(self, exception: Exception):
        """Only the status errors carry an upstream envelope; anything else must not be reworded,
        or a step's own bug would be reported as something the gateway said."""
        assert ModelGatewayErrorHandler.cause_of(exception) == str(exception)
