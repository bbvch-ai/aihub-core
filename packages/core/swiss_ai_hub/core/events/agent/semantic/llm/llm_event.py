import json
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Self

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.llms import LLM
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.llm.message import Message, TextContent
from swiss_ai_hub.core.events.agent.semantic.semantic_event import SemanticEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.agents.agent_config import AgentConfig

# An answer handed back rides on every event that ends the turn, and the broker refuses an event above its payload limit
# (1 MB in development) without an error the caller sees, so the run would wait forever. Room for the turns, not for the
# context the model read: a form of `____` blanks is cheap in tokens and long in characters.
HAND_BACK_BYTES = 200_000
_CUT_MARKER = "\n[…]"
_CONVERSATION_ROLES = (MessageRole.USER, MessageRole.ASSISTANT)


class LLMEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_llm_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_llm_event.description"
    )

    input_messages: Annotated[list[Message] | None, Field(description="List of messages sent to the LLM as input.")] = (
        None
    )
    output_messages: Annotated[
        list[Message] | None, Field(description="List of messages received from the LLM as output.")
    ] = None
    invocation_parameters: Annotated[
        dict[str, Any] | None, Field(description="Parameters used during the invocation of the LLM.")
    ] = None
    chat_model_name: Annotated[str | None, Field(description="The name of the language model being utilized.")] = None
    provider: Annotated[str | None, Field(description="The hosting provider of the LLM, e.g., OpenAI, Azure.")] = None
    system: Annotated[str | None, Field(description="The AI product as identified by the client or server.")] = None
    prompt_template: Annotated[str | None, Field(description="The prompt template as a Python f-string.")] = None
    prompt_template_variables: Annotated[
        dict[str, str] | None, Field(description="A dictionary of input variables to the prompt template.")
    ] = None
    prompt_template_version: Annotated[
        str | None, Field(description="The version of the prompt template being used.")
    ] = None
    token_count_prompt: Annotated[int | None, Field(description="The number of tokens in the prompt.")] = None
    token_count_completion: Annotated[int | None, Field(description="The number of tokens in the completion.")] = None
    token_count_total: Annotated[
        int | None,
        Field(
            description="The total number of tokens, including both prompt and completion.",
        ),
    ] = None
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="List of tools that are advertised to the LLM to be able to call.",
        ),
    ] = None

    @property
    def chat_messages(self) -> list[ChatMessage]:
        input_messages = self.input_messages or []
        output_messages = self.output_messages or []
        messages = [*input_messages, *output_messages]
        return [msg.to_llama_index() for msg in messages]

    def for_hand_back(self, max_bytes: int = HAND_BACK_BYTES) -> Self:
        """The answer with only the conversation it continues: user and assistant turns, newest first, within
        `max_bytes` serialized. The context the model read stays on `ContextComposedEvent`; carried on here it pushed
        the events that end the turn past the broker's limit. The newest turn is kept, cut when it alone is too long.
        """
        turns = [
            message
            for message in self.input_messages or []
            if message.role in _CONVERSATION_ROLES and message.content.strip()
        ]
        if not turns:
            return self.model_copy(update={"input_messages": turns})
        room = max_bytes - sum(LLMEvent._serialized_size(message) for message in self.output_messages or [])
        *earlier, newest = turns
        kept = [LLMEvent._cut_to_fit(newest, room)]
        room -= LLMEvent._serialized_size(kept[0])
        for message in reversed(earlier):
            size = LLMEvent._serialized_size(message)
            if size > room:
                break
            kept.insert(0, message)
            room -= size
        return self.model_copy(update={"input_messages": kept})

    @staticmethod
    def _serialized_size(message: Message) -> int:
        return len(message.model_dump_json().encode())

    @staticmethod
    def _cut_to_fit(message: Message, room: int) -> Message:
        """Shorten the text proportionally until the message fits; images and audio are references and stay."""
        text = message.content
        others = [block for block in message.contents or [] if not isinstance(block, TextContent)]
        cut, length = message, len(text)
        while (size := LLMEvent._serialized_size(cut)) > room and length > 0:
            length = min(length - 1, length * max(room, 0) // size)
            cut = message.model_copy(update={"contents": [TextContent(text=text[:length] + _CUT_MARKER), *others]})
        return cut

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
            SpanAttributes.LLM_INVOCATION_PARAMETERS: json.dumps(self.invocation_parameters),
            SpanAttributes.LLM_MODEL_NAME: self.chat_model_name,
            SpanAttributes.LLM_PROVIDER: self.provider,
            SpanAttributes.LLM_SYSTEM: self.system,
            SpanAttributes.LLM_PROMPT_TEMPLATE: self.prompt_template,
            SpanAttributes.LLM_PROMPT_TEMPLATE_VARIABLES: self.prompt_template_variables,
            SpanAttributes.LLM_PROMPT_TEMPLATE_VERSION: self.prompt_template_version,
            SpanAttributes.LLM_TOKEN_COUNT_PROMPT: self.token_count_prompt,
            SpanAttributes.LLM_TOKEN_COUNT_COMPLETION: self.token_count_completion,
            SpanAttributes.LLM_TOKEN_COUNT_TOTAL: self.token_count_total,
            SpanAttributes.LLM_TOOLS: self.tools,
        }

        if self.input_messages:
            for i, message in enumerate(self.input_messages):
                attributes = {
                    **attributes,
                    **message.to_semantic_convention(SpanAttributes.LLM_INPUT_MESSAGES, i),
                }

        if self.output_messages:
            for i, message in enumerate(self.output_messages):
                attributes = {
                    **attributes,
                    **message.to_semantic_convention(SpanAttributes.LLM_OUTPUT_MESSAGES, i),
                }

        return {k: v for k, v in attributes.items() if v is not None}

    @classmethod
    def from_chat_response(
        cls, input_messages: list[ChatMessage], output_message: ChatMessage, llm: LLM, agent_config: "AgentConfig"
    ) -> Self:
        handlers = llm.callback_manager.handlers
        token_count_handler = next((h for h in handlers if isinstance(h, TokenCountingHandler)), None)
        if token_count_handler:
            token_count_prompt = token_count_handler.prompt_llm_token_count
            token_count_completion = token_count_handler.completion_llm_token_count
        else:
            token_count_prompt = 0
            token_count_completion = 0

        return LLMEvent(
            input_messages=[Message.from_llama_index(msg) for msg in input_messages],
            output_messages=[Message.from_llama_index(output_message)],
            invocation_parameters=agent_config.llm.model_dump(),
            chat_model_name=agent_config.llm.model_name,
            provider=agent_config.llm.__class__.__name__,
            token_count_prompt=token_count_prompt,
            token_count_completion=token_count_completion,
            token_count_total=token_count_prompt + token_count_completion,
        )
