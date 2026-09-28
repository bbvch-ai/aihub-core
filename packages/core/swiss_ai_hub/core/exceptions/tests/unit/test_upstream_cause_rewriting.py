import httpx
import pytest
from openai import BadRequestError, InternalServerError

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


# Recorded verbatim from staging (api container, 2026-09-04T10:48:11Z) on a recording a user spoke
# into: the provider's alignment pass produced no segments and it reports only their count.
NO_SEGMENTS_FAILURE = (
    "litellm.InternalServerError: InternalServerError: OpenAIException - Error code: 500 - "
    "{'detail': 'Transcription failed: Request b86b9b03-eba7-48e5-b5f6-ccd832bc6a0f failed: 500: "
    "Transcription failed: 0'}. Received Model Group=inference-whisper-large-v3\n"
    "Available Model Group Fallbacks=None LiteLLM Retried: 2 times, LiteLLM Max Retries: 2"
)


def _bad_request_error(message: str) -> BadRequestError:
    body = {"error": {"message": message, "type": None, "param": None, "code": "400"}}
    request = httpx.Request("POST", UPSTREAM_URL)
    return BadRequestError("Error code: 400", response=httpx.Response(400, request=request, json=body), body=body)


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

    def test_a_transcription_without_segments_names_the_recording_instead_of_the_count(self):
        cause = ModelGatewayErrorHandler.cause_of(_internal_server_error(NO_SEGMENTS_FAILURE))

        assert "Transcription failed: 0" not in cause
        assert "LiteLLM Retried" not in cause
        assert cause.startswith("The speech-to-text provider produced no transcript")

    def test_unrecognised_failures_keep_the_gateway_wording(self):
        """Guessing at an unmatched failure would hide it; the gateway's own wording is still the
        best description available."""
        message = "litellm.InternalServerError: OpenAIException - upstream exploded in a new way"

        assert ModelGatewayErrorHandler.cause_of(_internal_server_error(message)) == message


class TestAnOverlongPromptNamesTheLimitInsteadOfTheGatewaysBookkeeping:
    """Recorded verbatim from Swiss LLM Cloud on 2026-09-14 by asking a 297-page PDF a question
    (aihub-core-private#241). The provider states the limit inside its own token arithmetic, and on the
    stages that configure fallbacks LiteLLM appends its fallback bookkeeping after it -- neither of which
    tells a chat user what to do."""

    CONTEXT_EXCEEDED = (
        "litellm.BadRequestError: OpenAIException - upstream 400 on google/gemma-4-31B-it: "
        '{"error":{"message":"This model\'s maximum context length is 100016 tokens. However, you '
        "requested 1 output tokens and your prompt contains at least 100016 input tokens, for a total "
        "of at least 100017 tokens. Please reduce the length of the input prompt or the number of "
        'requested output tokens. (parameter=input_tokens, value=100016)","type":"BadRequestError",'
        '"param":"input_tokens","code":400}}. Received Model Group=text-generation/gemma-4-31B-it\n'
        "Available Model Group Fallbacks=None"
    )

    def test_the_limit_is_kept_and_the_arithmetic_dropped(self):
        cause = ModelGatewayErrorHandler.cause_of(_bad_request_error(self.CONTEXT_EXCEEDED))

        assert "100016" in cause
        assert "parameter=input_tokens" not in cause
        assert "Received Model Group" not in cause
        assert cause.startswith("This request is too long for the model")

    def test_the_fallback_bookkeeping_is_dropped_too(self):
        """The deployed stages configure `default_fallbacks`, so the real cause arrives with LiteLLM's
        fallback search appended to it."""
        with_fallback_noise = (
            self.CONTEXT_EXCEEDED + "No fallback model group found for original "
            "model_group=text-generation/gemma-4-31B-it. Fallbacks=[{'embedding/bge-m3': []}, "
            "{'reranker/bge': []}]"
        )

        cause = ModelGatewayErrorHandler.cause_of(_bad_request_error(with_fallback_noise))

        assert "No fallback model group found" not in cause
        assert "embedding/bge-m3" not in cause
        assert "100016" in cause

    def test_an_unrelated_bad_request_keeps_the_gateway_wording(self):
        message = "litellm.BadRequestError: OpenAIException - Invalid model name passed in model=nope"

        assert ModelGatewayErrorHandler.cause_of(_bad_request_error(message)) == message


class TestUnusableAudioIsToldFromAGatewayFault:
    """A caller transcribing in chunks drops what the provider cannot use and keeps the rest, so this
    predicate must not answer for a fault that every chunk would hit alike."""

    def test_a_missing_segment_count_is_unusable_audio(self):
        assert ModelGatewayErrorHandler.is_untranscribable_audio(_internal_server_error(NO_SEGMENTS_FAILURE)) is True

    def test_a_nested_provider_status_is_not_unusable_audio(self):
        """The alignment failure reports a 503 through the very same phrase. A status can be
        transient, and dropping a chunk over one loses audio nobody knows is missing."""
        assert ModelGatewayErrorHandler.is_untranscribable_audio(_internal_server_error(ALIGNMENT_FAILURE)) is False

    def test_an_unrelated_gateway_failure_is_not_unusable_audio(self):
        message = "litellm.InternalServerError: OpenAIException - Invalid model name passed in model=whisper-1"

        assert ModelGatewayErrorHandler.is_untranscribable_audio(_internal_server_error(message)) is False

    def test_a_non_gateway_exception_is_not_unusable_audio(self):
        """Only the gateway's own envelope carries this verdict; matching bare exception text would
        let anything that quotes the provider decide how a chunk is handled."""
        assert ModelGatewayErrorHandler.is_untranscribable_audio(RuntimeError("Transcription failed: 0")) is False
