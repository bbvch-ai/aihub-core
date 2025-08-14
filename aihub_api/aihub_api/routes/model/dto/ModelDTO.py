from typing import Optional, List

from pydantic import BaseModel


class ModelDTO(BaseModel):
    model_name: str
    mode: str
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_cost_per_million_token: Optional[float] = None
    output_cost_per_million_token: Optional[float] = None
    cache_creation_input_token_cost: Optional[float] = None
    cache_read_input_token_cost: Optional[float] = None
    input_cost_per_token_above_128k_tokens: Optional[float] = None
    input_cost_per_token_above_200k_tokens: Optional[float] = None
    input_cost_per_audio_token: Optional[float] = None
    input_cost_per_token_batches: Optional[float] = None
    output_cost_per_token_batches: Optional[float] = None
    output_cost_per_audio_token: Optional[float] = None
    output_cost_per_reasoning_token: Optional[float] = None
    output_cost_per_token_above_128k_tokens: Optional[float] = None
    output_cost_per_token_above_200k_tokens: Optional[float] = None
    output_cost_per_image: Optional[float] = None
    search_context_cost_per_query: Optional[float] = None
    output_vector_size: Optional[int] = None
    supports_system_messages: Optional[bool] = None
    supports_response_schema: Optional[bool] = None
    supports_vision: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_tool_choice: Optional[bool] = None
    supports_assistant_prefill: Optional[bool] = None
    supports_prompt_caching: Optional[bool] = None
    supports_audio_input: Optional[bool] = None
    supports_audio_output: Optional[bool] = None
    supports_pdf_input: Optional[bool] = None
    supports_embedding_image_input: Optional[bool] = None
    supports_native_streaming: Optional[bool] = None
    supports_web_search: Optional[bool] = None
    supports_url_context: Optional[bool] = None
    supports_reasoning: Optional[bool] = None
    supports_computer_use: Optional[bool] = None
    tpm: Optional[int] = None
    rpm: Optional[int] = None
    supported_openai_params: Optional[List[str]] = None
