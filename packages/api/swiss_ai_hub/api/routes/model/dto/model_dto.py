from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class SearchContextCostPerQueryDTO(BaseModel):
    """LiteLLM reports search context cost per query broken down by context size, not as a single value."""

    search_context_size_low: Annotated[
        float | None, Field(None, description="Cost per query with low search context size")
    ]
    search_context_size_medium: Annotated[
        float | None, Field(None, description="Cost per query with medium search context size")
    ]
    search_context_size_high: Annotated[
        float | None, Field(None, description="Cost per query with high search context size")
    ]


class ModelInfoDTO(BaseModel):
    mode: Annotated[str, Field(description="The mode of the model (e.g., 'chat', 'completion', 'embedding')")]
    max_input_tokens: Annotated[
        int | None, Field(None, description="Maximum number of input tokens the model can handle")
    ]
    max_output_tokens: Annotated[
        int | None, Field(None, description="Maximum number of output tokens the model can generate")
    ]
    input_cost_per_token: Annotated[float | None, Field(None, description="Cost per input token in USD")]
    output_cost_per_token: Annotated[float | None, Field(None, description="Cost per output token in USD")]
    cache_creation_input_token_cost: Annotated[
        float | None, Field(None, description="Cost for creating cache from input tokens")
    ]
    cache_read_input_token_cost: Annotated[
        float | None, Field(None, description="Cost for reading cached input tokens")
    ]
    input_cost_per_token_above_128k_tokens: Annotated[
        float | None, Field(None, description="Cost per input token for contexts above 128k tokens")
    ]
    input_cost_per_token_above_200k_tokens: Annotated[
        float | None, Field(None, description="Cost per input token for contexts above 200k tokens")
    ]
    input_cost_per_audio_token: Annotated[float | None, Field(None, description="Cost per audio input token")]
    input_cost_per_token_batches: Annotated[
        float | None, Field(None, description="Cost per input token when using batch API")
    ]
    output_cost_per_token_batches: Annotated[
        float | None, Field(None, description="Cost per output token when using batch API")
    ]
    output_cost_per_audio_token: Annotated[float | None, Field(None, description="Cost per audio output token")]
    output_cost_per_reasoning_token: Annotated[
        float | None, Field(None, description="Cost per reasoning token for models with reasoning capabilities")
    ]
    output_cost_per_token_above_128k_tokens: Annotated[
        float | None, Field(None, description="Cost per output token for contexts above 128k tokens")
    ]
    output_cost_per_token_above_200k_tokens: Annotated[
        float | None, Field(None, description="Cost per output token for contexts above 200k tokens")
    ]
    output_cost_per_image: Annotated[float | None, Field(None, description="Cost per image output")]
    search_context_cost_per_query: Annotated[
        SearchContextCostPerQueryDTO | None, Field(None, description="Cost per search context query by context size")
    ]
    output_vector_size: Annotated[int | None, Field(None, description="Size of output vectors for embedding models")]
    supports_system_messages: Annotated[
        bool | None, Field(None, description="Whether the model supports system messages")
    ]
    supports_response_schema: Annotated[
        bool | None, Field(None, description="Whether the model supports structured response schemas")
    ]
    supports_vision: Annotated[bool | None, Field(None, description="Whether the model supports vision/image input")]
    supports_function_calling: Annotated[
        bool | None, Field(None, description="Whether the model supports function calling")
    ]
    supports_tool_choice: Annotated[
        bool | None, Field(None, description="Whether the model supports tool choice selection")
    ]
    supports_assistant_prefill: Annotated[
        bool | None, Field(None, description="Whether the model supports assistant message prefilling")
    ]
    supports_prompt_caching: Annotated[
        bool | None, Field(None, description="Whether the model supports prompt caching")
    ]
    supports_audio_input: Annotated[bool | None, Field(None, description="Whether the model supports audio input")]
    supports_audio_output: Annotated[bool | None, Field(None, description="Whether the model supports audio output")]
    supports_pdf_input: Annotated[bool | None, Field(None, description="Whether the model supports PDF input")]
    supports_embedding_image_input: Annotated[
        bool | None, Field(None, description="Whether the model supports image input for embeddings")
    ]
    supports_native_streaming: Annotated[
        bool | None, Field(None, description="Whether the model supports native streaming")
    ]
    supports_web_search: Annotated[
        bool | None, Field(None, description="Whether the model supports web search capabilities")
    ]
    supports_url_context: Annotated[
        bool | None, Field(None, description="Whether the model supports URL context input")
    ]
    supports_reasoning: Annotated[
        bool | None, Field(None, description="Whether the model supports reasoning capabilities")
    ]
    supports_computer_use: Annotated[
        bool | None, Field(None, description="Whether the model supports computer use capabilities")
    ]
    tpm: Annotated[int | None, Field(None, description="Tokens per minute rate limit")]
    rpm: Annotated[int | None, Field(None, description="Requests per minute rate limit")]
    supported_openai_params: Annotated[
        list[str] | None, Field(None, description="List of supported OpenAI API parameters")
    ]


class ModelDTO(BaseModel):
    model_name: Annotated[str, Field(description="The name/identifier of the model")]
    model_info: Annotated[ModelInfoDTO, Field(description="Detailed information about the model")]

    @computed_field
    @property
    def icon(self) -> str:
        mode = self.model_info.mode
        if mode == "chat":
            return "mage:message"
        elif mode == "embedding":
            return "mage:chart"
        elif mode == "image_generation":
            return "mage:image"
        elif mode in ("audio_transcription", "audio_speech"):
            return "mage:microphone"
        else:
            return "mage:robot"

    def convert_costs_to_microunits(self):
        """Creates a coopy of the model info with converted cosets."""
        cost_fields = [
            "input_cost_per_token",
            "output_cost_per_token",
            "cache_creation_input_token_cost",
            "cache_read_input_token_cost",
            "input_cost_per_token_above_128k_tokens",
            "input_cost_per_token_above_200k_tokens",
            "input_cost_per_audio_token",
            "input_cost_per_token_batches",
            "output_cost_per_token_batches",
            "output_cost_per_audio_token",
            "output_cost_per_reasoning_token",
            "output_cost_per_token_above_128k_tokens",
            "output_cost_per_token_above_200k_tokens",
            "output_cost_per_image",
        ]

        updates: dict[str, float] = {}
        for field_name in cost_fields:
            current_value = getattr(self.model_info, field_name)
            if current_value is not None:
                updates[field_name] = current_value * 1_000_000

        return self.model_info.model_copy(update=updates)


class ModelTypeGroupDTO(BaseModel):
    name: Annotated[str, Field(description="The name/type of the model group")]
    models: Annotated[list[ModelDTO], Field(description="List of models in this group")]
