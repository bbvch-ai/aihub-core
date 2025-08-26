import json
import logging
from typing import Annotated

from flatdict import FlatterDict
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.llms import LLM
from opentelemetry import trace

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.nats.events import ChunkEvent, DisplayEvent, LLMEvent, LLMStopEvent, ThoughtEvent
from aihub_lib.nats.events.cost.LLMCostEvent import LLMCostEvent
from aihub_lib.nats.events.semantic import Message
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager

logger = logging.getLogger(__name__)


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
        attributes = FlatterDict(event.model_dump(), delimiter=".").as_dict()

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
        - Flushes buffers when encountering sentence boundaries (.), newlines, or when buffer exceeds `max_buffer_length`.
        - Content within <think>...</think> tags is streamed live as ThoughtEvents.
        - After streaming all chunks, retrieves token usage from `TokenCountingHandler`.
        - Returns an LLMEvent summarizing the entire conversation (inputs + full output).

        ### Example
        If the LLM returns content with thinking, `display_llm_stream` will stream both
        ChunkEvents for regular content and ThoughtEvents for thinking content in real-time,
        then produce a final LLMEvent with the aggregate content.
        """

        aggregate = ""
        regular_buffer = ""
        thinking_buffer = ""
        pending_content = ""  # Content that needs to be processed
        in_thinking = False
        max_buffer_length = 500

        async def flush_regular_buffer():
            nonlocal regular_buffer
            if regular_buffer:
                await self.display_chunk(regular_buffer, model_name=llm_config.model_name)
                regular_buffer = ""

        async def flush_thinking_buffer():
            nonlocal thinking_buffer
            if thinking_buffer:
                await self.display_thought(thinking_buffer)
                thinking_buffer = ""

        def add_to_buffer_and_check_flush(char, buffer_type="regular"):
            """Add character to appropriate buffer and check flush conditions"""
            nonlocal regular_buffer, thinking_buffer

            if buffer_type == "thinking":
                thinking_buffer += char
                should_flush = char == "." or char == "\n" or len(thinking_buffer) >= max_buffer_length
                return should_flush
            else:
                regular_buffer += char
                should_flush = char == "." or char == "\n" or len(regular_buffer) >= max_buffer_length
                return should_flush

        # Iterate over streamed chunks from the LLM
        for chunk in llm.stream_chat(messages):
            content = chunk.delta
            aggregate += content
            pending_content += content

            # Process pending content
            while pending_content:
                # Check if we're at the start of a potential tag
                if pending_content.startswith("<think>"):
                    # Found opening think tag
                    await flush_regular_buffer()
                    in_thinking = True
                    pending_content = pending_content[7:]  # Remove '<think>'

                elif pending_content.startswith("</think>"):
                    # Found closing think tag
                    await flush_thinking_buffer()
                    in_thinking = False
                    pending_content = pending_content[8:]  # Remove '</think>'

                elif pending_content.startswith("<") and len(pending_content) < 8:
                    # Might be start of a tag but need more content to determine
                    # Check if it could be the beginning of <think> or </think>
                    if "<think>".startswith(pending_content) or "</think>".startswith(pending_content):
                        # Could be a tag, wait for more content
                        break
                    else:
                        # Not a thinking tag, process the '<' character
                        char = pending_content[0]
                        pending_content = pending_content[1:]

                        if in_thinking:
                            if add_to_buffer_and_check_flush(char, "thinking"):
                                await flush_thinking_buffer()
                        else:
                            if add_to_buffer_and_check_flush(char, "regular"):
                                await flush_regular_buffer()
                else:
                    # Process regular character
                    char = pending_content[0]
                    pending_content = pending_content[1:]

                    if in_thinking:
                        if add_to_buffer_and_check_flush(char, "thinking"):
                            await flush_thinking_buffer()
                    else:
                        if add_to_buffer_and_check_flush(char, "regular"):
                            await flush_regular_buffer()

        # Process any remaining pending content
        if pending_content:
            # Incomplete tag or remaining content
            if pending_content.startswith("<") and (
                "<think>".startswith(pending_content) or "</think>".startswith(pending_content)
            ):
                logger.warning(f"Incomplete tag found at end of stream: {pending_content}")

            # Process remaining content as regular text
            for char in pending_content:
                if in_thinking:
                    thinking_buffer += char
                else:
                    regular_buffer += char

        # Flush any remaining buffers
        await flush_thinking_buffer()
        await flush_regular_buffer()

        # Extract token counts from handler if present
        handlers = llm.callback_manager.handlers
        token_count_handler = next((h for h in handlers if isinstance(h, TokenCountingHandler)), None)
        if token_count_handler:
            token_count_prompt = token_count_handler.prompt_llm_token_count
            token_count_completion = token_count_handler.completion_llm_token_count
        else:
            token_count_prompt = 0
            token_count_completion = 0

        llm_event = LLMEvent(
            input_messages=[Message.from_llama_index(msg) for msg in messages],
            output_messages=[Message.from_string(role="assistant", content=aggregate, name=llm_config.model_name)],
            invocation_parameters=llm_config.model_dump(),
            chat_model_name=llm_config.model_name,
            provider=llm_config.__class__.__name__,
            token_count_prompt=token_count_prompt,
            token_count_completion=token_count_completion,
            token_count_total=token_count_prompt + token_count_completion,
        )

        if not as_stop_step:
            return llm_event

        return LLMStopEvent(**llm_event.model_dump())
