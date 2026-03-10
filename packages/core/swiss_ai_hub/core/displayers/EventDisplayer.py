import json
import logging
from typing import Annotated, Any

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.llms import LLM
from opentelemetry import trace

from swiss_ai_hub.core.displayers.stream.StreamProcessor import StreamProcessor
from swiss_ai_hub.core.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from swiss_ai_hub.core.nats.events.cost.LLMCostEvent import LLMCostEvent
from swiss_ai_hub.core.nats.events.display.ChunkEvent import ChunkEvent
from swiss_ai_hub.core.nats.events.display.DisplayEvent import DisplayEvent
from swiss_ai_hub.core.nats.events.display.ThoughtEvent import ThoughtEvent
from swiss_ai_hub.core.nats.events.semantic.llm.LLMEvent import LLMEvent
from swiss_ai_hub.core.nats.events.semantic.llm.LLMStopEvent import LLMStopEvent
from swiss_ai_hub.core.nats.events.semantic.llm.Message import Message
from swiss_ai_hub.core.nats.publishers.JSPublisher import JSPublisher
from swiss_ai_hub.core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager

logger = logging.getLogger(__name__)


def _flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dot-delimited keys for OTel span attributes."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    result.update(_flatten_dict(item, f"{full_key}.{i}"))
                else:
                    result[f"{full_key}.{i}"] = item
        else:
            result[full_key] = value
    return result


class EventDisplayer:
    """
    A utility class responsible for publishing display-related events (e.g., chunks of output,
    reasoning thoughts, cost metrics) to the event stream. It integrates with tracing and ensures
    that each piece of output is captured as a `DisplayEvent` (or subclass) and sent to the corresponding
    subject.

    ### Why EventDisplayer?
    In conversational or generative AI workflows, you may produce intermediate outputs, reasoning steps,
    or cost metrics that should be visible in logs or UI streams. EventDisplayer:
    - Publishes these outputs as display events.
    - Flushes tokens or partial responses incrementally (like streaming chat responses).
    - Allows other services or UIs to subscribe to these display events and show them to users or operators.

    ### Tracing Integration
    Each display event is recorded in the current OTel span, adding trace attributes for observability.
    Developers can correlate displayed content with the execution flow in distributed traces.

    ### Example
    When an LLM is asked a question, `display_llm_stream` streams the model's reply line-by-line as `ChunkEvent`s.
    Another scenario: after completion, `display_llm_costs` publishes an `LLMCostEvent` summarizing token usage.

    """

    def __init__(
        self,
        publisher: Annotated[JSPublisher, "JSPublisher for sending events to JetStream"],
        topic_manager: Annotated[AgentThreadTopicManager, "Manages event subjects for a thread"],
    ):
        self.publisher = publisher
        self.topic_manager = topic_manager

    async def display_event(
        self,
        event: Annotated[DisplayEvent, "The display event to publish."],
        content: Annotated[str | None, "Optional human-readable content for tracing."] = None,
    ):
        """
        Publish a display event, optionally logging its content to the current trace span.
        Useful for any displayable output that needs to be consumed downstream (UI, logs, etc.).
        """
        subject = self.topic_manager.get_subject_for_display_event_in_thread(event.event_name, event.event_id)
        attributes = _flatten_dict(event.model_dump())

        current_span = trace.get_current_span()
        current_span.add_event(
            name=f"{event.event_name}: {content or json.dumps(attributes)}",
            attributes=attributes,
        )

        await self.publisher.publish_event(event, subject)

    async def display_chunk(
        self,
        content: Annotated[str, "A partial piece of output"],
        model_name: Annotated[str, "Name of the model producing this chunk"],
    ):
        """
        Display a chunk of output (e.g., partial LLM response) as a ChunkEvent.
        This method helps in streaming responses as they are generated.
        """
        event = ChunkEvent(content=content, model_name=model_name)
        await self.display_event(event, content=content)

    async def display_thought(self, thought: Annotated[str, "The reasoning or thought content to display"]):
        """
        Publish an internal reasoning thought as a ThoughtEvent.
        Provides transparency into agent's internal logic or decision-making steps.
        """
        event = ThoughtEvent(content="", model_name="", reasoning_content=f"{thought}\n")
        await self.display_event(event, content=thought)

    async def display_llm_costs(
        self,
        model_name: Annotated[str, "Model name for cost attribution"],
        cost_tracker: Annotated[LLMCostTracker, "Tracks token usage and associated costs"],
    ):
        """
        Publish LLM cost metrics as an LLMCostEvent.
        Useful at the end of a run to account for expenses and usage.
        """
        llm_cost_event = LLMCostEvent.from_llm_costs(
            llm_name=model_name,
            costs=cost_tracker.get_total_costs(),
        )
        await self.display_event(llm_cost_event)

    async def display_llm_stream(
        self,
        llm_config: Annotated[LLMConfig, "Configuration for the LLM (model name, parameters)."],
        llm: Annotated[LLM, "The LLM instance providing stream_chat functionality."],
        messages: Annotated[
            list[ChatMessage],
            "The chat messages (prompt + context) to send to the LLM.",
        ],
        as_stop_step: Annotated[bool, "Stop Agent after response finished streaming"] = False,
    ) -> LLMEvent | LLMStopEvent:
        """
        Stream the LLM's response incrementally as chunked events, then return a final LLMEvent encapsulating
        the entire output.

        ### How it Works
        - Calls `llm.stream_chat(messages)` to get a generator of partial responses (chunks).
        - Maintains separate buffers for regular content and thinking content.
        - Flushes buffers when encountering sentence boundaries (.), newlines,
          or when buffer exceeds `max_buffer_length`.
        - Content within <think>...</think> tags is streamed live as ThoughtEvents.
        - After streaming all chunks, retrieves token usage from `TokenCountingHandler`.
        - Returns an LLMEvent summarizing the entire conversation (inputs + full output).

        ### Example
        If the LLM returns content with thinking, `display_llm_stream` will stream both
        ChunkEvents for regular content and ThoughtEvents for thinking content in real-time,
        then produce a final LLMEvent with the aggregate content.
        """
        processor = StreamProcessor(self, llm_config.model_name)

        for chunk in llm.stream_chat(messages):
            await processor.process_chunk(chunk.delta)

        aggregate_content = await processor.finalize()
        prompt_tokens, completion_tokens = self._extract_token_counts(llm)

        llm_event = self._create_llm_event(
            messages=messages,
            aggregate_content=aggregate_content,
            llm_config=llm_config,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        if as_stop_step:
            return LLMStopEvent(**llm_event.model_dump())
        return llm_event

    @staticmethod
    def _extract_token_counts(llm: LLM) -> tuple[int, int]:
        """Extract token counts from LLM handlers."""
        handlers = llm.callback_manager.handlers
        token_handler = next((h for h in handlers if isinstance(h, TokenCountingHandler)), None)

        if token_handler:
            return (token_handler.prompt_llm_token_count, token_handler.completion_llm_token_count)
        return (0, 0)

    @staticmethod
    def _create_llm_event(
        messages: list[ChatMessage],
        aggregate_content: str,
        llm_config: LLMConfig,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> LLMEvent:
        """Create an LLMEvent with the provided information."""
        return LLMEvent(
            input_messages=[Message.from_llama_index(msg) for msg in messages],
            output_messages=[
                Message.from_string(role="assistant", content=aggregate_content, name=llm_config.model_name)
            ],
            invocation_parameters=llm_config.model_dump(),
            chat_model_name=llm_config.model_name,
            provider=llm_config.__class__.__name__,
            token_count_prompt=prompt_tokens,
            token_count_completion=completion_tokens,
            token_count_total=prompt_tokens + completion_tokens,
        )
