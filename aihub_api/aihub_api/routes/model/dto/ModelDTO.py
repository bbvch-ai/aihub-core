
from pydantic import BaseModel


class ModelInfoDTO(BaseModel):
    mode: str
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    cache_creation_input_token_cost: float | None = None
    cache_read_input_token_cost: float | None = None
    input_cost_per_token_above_128k_tokens: float | None = None
    input_cost_per_token_above_200k_tokens: float | None = None
    input_cost_per_audio_token: float | None = None
    input_cost_per_token_batches: float | None = None
    output_cost_per_token_batches: float | None = None
    output_cost_per_audio_token: float | None = None
    output_cost_per_reasoning_token: float | None = None
    output_cost_per_token_above_128k_tokens: float | None = None
    output_cost_per_token_above_200k_tokens: float | None = None
    output_cost_per_image: float | None = None
    search_context_cost_per_query: float | None = None
    output_vector_size: int | None = None
    supports_system_messages: bool | None = None
    supports_response_schema: bool | None = None
    supports_vision: bool | None = None
    supports_function_calling: bool | None = None
    supports_tool_choice: bool | None = None
    supports_assistant_prefill: bool | None = None
    supports_prompt_caching: bool | None = None
    supports_audio_input: bool | None = None
    supports_audio_output: bool | None = None
    supports_pdf_input: bool | None = None
    supports_embedding_image_input: bool | None = None
    supports_native_streaming: bool | None = None
    supports_web_search: bool | None = None
    supports_url_context: bool | None = None
    supports_reasoning: bool | None = None
    supports_computer_use: bool | None = None
    tpm: int | None = None
    rpm: int | None = None
    supported_openai_params: list[str] | None = None


class ModelDTO(BaseModel):
    model_name: str
    model_info: ModelInfoDTO
    icon: str | None = None
