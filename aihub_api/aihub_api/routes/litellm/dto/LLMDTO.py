from pydantic import BaseModel
from typing import Optional


class LiteLLMParamsDTO(BaseModel):
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    model: str


class ModelInfoDTO(BaseModel):
    mode: str
    key: str
    max_tokens: Optional[int] = None
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_cost_per_token: Optional[float] = None
    cache_read_input_token_cost: Optional[float] = None
    output_cost_per_token: Optional[float] = None
    input_cost_per_token_batches: Optional[float] = None
    output_cost_per_token_batches: Optional[float] = None
    output_vector_size: Optional[int] = None
    input_cost_per_audio_token: Optional[float] = None
    output_cost_per_reasoning_token: Optional[float] = None
    tpm: Optional[int] = None
    rpm: Optional[int] = None


class LLMDTO(BaseModel):
    model_name: str
    litellm_params: LiteLLMParamsDTO
    model_info: ModelInfoDTO