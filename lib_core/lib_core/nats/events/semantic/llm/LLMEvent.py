from typing import Optional, List, Dict
from pydantic import Field

from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

from lib_core.nats.events.semantic import SemanticEvent
from lib_core.nats.events.semantic.llm.Message import Message


class LLMEvent(SemanticEvent):
    input_messages: Optional[List[Message]] = Field(
        None,
        description="List of messages sent to the LLM as input."
    )
    output_messages: Optional[List[Message]] = Field(
        None,
        description="List of messages received from the LLM as output."
    )
    invocation_parameters: Optional[Dict] = Field(
        None,
        description="Parameters used during the invocation of the LLM."
    )
    chat_model_name: Optional[str] = Field(
        None,
        description="The name of the language model being utilized."
    )
    provider: Optional[str] = Field(
        None,
        description="The hosting provider of the LLM, e.g., OpenAI, Azure."
    )
    system: Optional[str] = Field(
        None,
        description="The AI product as identified by the client or server."
    )
    prompt_template: Optional[str] = Field(
        None,
        description="The prompt template as a Python f-string."
    )
    prompt_template_variables: Optional[Dict] = Field(
        None,
        description="A dictionary of input variables to the prompt template."
    )
    prompt_template_version: Optional[str] = Field(
        None,
        description="The version of the prompt template being used."
    )
    token_count_prompt: Optional[int] = Field(
        None,
        description="The number of tokens in the prompt."
    )
    token_count_completion: Optional[int] = Field(
        None,
        description="The number of tokens in the completion."
    )
    token_count_total: Optional[int] = Field(
        None,
        description="The total number of tokens, including both prompt and completion."
    )
    tools: Optional[List[Dict]] = Field(
        None,
        description="List of tools that are advertised to the LLM to be able to call."
    )

    def to_semantic_convention(self) -> dict:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
            SpanAttributes.LLM_INVOCATION_PARAMETERS: self.invocation_parameters,
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
                    **message.to_semantic_convention(SpanAttributes.LLM_INPUT_MESSAGES, i)
                }

        if self.output_messages:
            for i, message in enumerate(self.output_messages):
                attributes = {
                    **attributes,
                    **message.to_semantic_convention(SpanAttributes.LLM_OUTPUT_MESSAGES, i)
                }

        return attributes
