import json
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Self

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.llms import LLM
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.llm.Message import Message
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent

if TYPE_CHECKING:
    from aihub_lib.agents.AgentConfig import AgentConfig


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
