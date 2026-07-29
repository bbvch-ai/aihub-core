from unittest.mock import Mock, patch

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

_FAKE_MODEL_INFO = {
    "model_info": {
        "max_input_tokens": 8192,
        "mode": "chat",
        "supports_function_calling": True,
        "max_output_tokens": 2048,
        "supports_response_schema": True,
        "input_cost_per_token": 0.000001,
        "output_cost_per_token": 0.000002,
    }
}


def _build_llm():
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

    fake_settings = Mock(BASE_URL="http://litellm-test/v1", API_KEY=Mock(get_secret_value=Mock(return_value="key")))
    with (
        patch.object(LLMConfig, "get_model_info", return_value=_FAKE_MODEL_INFO),
        patch(
            "swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config.LiteLLMProxySettings",
            return_value=fake_settings,
        ),
    ):
        llm, cost_tracker = config.to_llama_index()

    return llm, cost_tracker


def test_to_llama_index_requests_usage_on_streamed_calls():
    llm, _ = _build_llm()

    assert llm.additional_kwargs == {"stream_options": {"include_usage": True}}


def test_stream_options_only_sent_when_actually_streaming():
    llm, _ = _build_llm()

    non_streaming_kwargs = llm._get_model_kwargs()
    streaming_kwargs = llm._get_model_kwargs(stream=True)

    assert "stream_options" not in non_streaming_kwargs
    assert streaming_kwargs["stream_options"] == {"include_usage": True}
