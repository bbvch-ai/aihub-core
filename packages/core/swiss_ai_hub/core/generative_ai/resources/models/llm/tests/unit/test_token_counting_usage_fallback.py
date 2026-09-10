from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.callbacks.schema import CBEventType, EventPayload

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig


def _counting_tokenizer():
    calls = []

    def tokenizer(text: str) -> list[int]:
        calls.append(text)
        return [0] * len(text.split())

    return tokenizer, calls


def _messages() -> list[ChatMessage]:
    return [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=MessageRole.USER, content="What is the capital of Switzerland?"),
    ]


def test_usage_on_final_chunk_skips_the_local_tokenizer_entirely():
    """
    Regression test for #1632: when the gateway reports real usage (``stream_options.include_usage``),
    ``TokenCountingHandler`` must read it directly and never fall back to re-tokenizing the chat
    history — that fallback is what previously drove N+1 blocking HTTP calls per streamed response.
    """
    tokenizer, calls = _counting_tokenizer()
    handler = TokenCountingHandler(tokenizer=tokenizer)

    final_chunk = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="Bern."),
        raw={"usage": {"prompt_tokens": 42, "completion_tokens": 7, "total_tokens": 49}},
    )

    handler.on_event_end(
        CBEventType.LLM,
        payload={EventPayload.MESSAGES: _messages(), EventPayload.RESPONSE: final_chunk},
        event_id="test-event",
    )

    assert handler.prompt_llm_token_count == 42
    assert handler.completion_llm_token_count == 7
    assert calls == []


def test_missing_usage_falls_back_to_the_local_tokenizer():
    """The fallback still exists for providers/paths where the gateway drops ``stream_options``."""
    tokenizer, calls = _counting_tokenizer()
    handler = TokenCountingHandler(tokenizer=tokenizer)

    final_chunk = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="Bern."),
        raw={},
    )

    handler.on_event_end(
        CBEventType.LLM,
        payload={EventPayload.MESSAGES: _messages(), EventPayload.RESPONSE: final_chunk},
        event_id="test-event",
    )

    assert handler.prompt_llm_token_count > 0
    assert calls, "local tokenizer fallback should have been used when usage is absent"


def test_llm_config_wires_the_real_local_tokenizer_into_the_handler():
    """The tokenizer plugged into TokenCountingHandler must be the in-process one, not an HTTP call."""
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
    handler = TokenCountingHandler(tokenizer=config.token_counter)

    assert handler.tokenizer("hello world") == config.token_counter("hello world")
