import httpx
import pytest
from openai import InternalServerError

from swiss_ai_hub.core.exceptions.model_gateway_error_handler import ModelGatewayErrorHandler

pytestmark = pytest.mark.unit

UPSTREAM_URL = "http://litellm:4000/audio/transcriptions"

# Recorded verbatim from the provider on 2026-09-03 by transcribing an Indonesian recording.
ALIGNMENT_FAILURE = (
    "litellm.InternalServerError: InternalServerError: OpenAIException - Error code: 500 - "
    "{'detail': \"Transcription failed: Request 03486716-5ed9-4a4d-b7b9-ffcffe6713b4 failed: 500: "
    "Transcription failed: 503: Failed to load alignment model for 'id': "
    'No default align-model for language: id"}. Received Model Group=inference-whisper-large-v3\n'
    "Available Model Group Fallbacks=None"
)


def _internal_server_error(message: str) -> InternalServerError:
    body = {"error": {"message": message, "type": None, "param": None, "code": "500"}}
    request = httpx.Request("POST", UPSTREAM_URL)
    return InternalServerError("Error code: 500", response=httpx.Response(500, request=request, json=body), body=body)


class TestProviderInternalsAreRewrittenForTheCaller:
    """The transcription provider names its own pipeline stage — "align-model" means nothing to a
    chat user, and the language it names is the one it detected, not one the caller chose."""

    def test_alignment_failure_names_the_language_instead_of_the_stage(self):
        cause = ModelGatewayErrorHandler.cause_of(_internal_server_error(ALIGNMENT_FAILURE))

        assert "align-model" not in cause
        assert "'id'" in cause
        assert cause.startswith("Transcription is not available for the language")

    def test_unrecognised_failures_keep_the_gateway_wording(self):
        """Guessing at an unmatched failure would hide it; the gateway's own wording is still the
        best description available."""
        message = "litellm.InternalServerError: OpenAIException - upstream exploded in a new way"

        assert ModelGatewayErrorHandler.cause_of(_internal_server_error(message)) == message
