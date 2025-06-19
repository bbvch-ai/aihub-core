import json
from typing import Any, ClassVar, Dict, List, Optional

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.llms import LLM
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.llm.Message import Message
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class LLMEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_llm_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_llm_event.description"
    )

    input_messages: Optional[List[Message]] = Field(None, description="List of messages sent to the LLM as input.")
    output_messages: Optional[List[Message]] = Field(
        None, description="List of messages received from the LLM as output."
    )
    invocation_parameters: Optional[Dict[str, Any]] = Field(
        None, description="Parameters used during the invocation of the LLM."
    )
    chat_model_name: Optional[str] = Field(None, description="The name of the language model being utilized.")
    provider: Optional[str] = Field(None, description="The hosting provider of the LLM, e.g., OpenAI, Azure.")
    system: Optional[str] = Field(None, description="The AI product as identified by the client or server.")
    prompt_template: Optional[str] = Field(None, description="The prompt template as a Python f-string.")
    prompt_template_variables: Optional[Dict[str, str]] = Field(
        None, description="A dictionary of input variables to the prompt template."
    )
    prompt_template_version: Optional[str] = Field(None, description="The version of the prompt template being used.")
    token_count_prompt: Optional[int] = Field(None, description="The number of tokens in the prompt.")
    token_count_completion: Optional[int] = Field(None, description="The number of tokens in the completion.")
    token_count_total: Optional[int] = Field(
        None,
        description="The total number of tokens, including both prompt and completion.",
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of tools that are advertised to the LLM to be able to call.",
    )

    def to_semantic_convention(self) -> Dict[str, str]:
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
        cls, input_messages: List[ChatMessage], output_message: ChatMessage, llm: LLM, agent_config: AgentConfig
    ) -> "LLMEvent":
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
            chat_model_name=agent_config.llm.name,
            provider=agent_config.llm.__class__.__name__,
            token_count_prompt=token_count_prompt,
            token_count_completion=token_count_completion,
            token_count_total=token_count_prompt + token_count_completion,
        )
