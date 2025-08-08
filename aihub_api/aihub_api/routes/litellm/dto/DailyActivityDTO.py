from pydantic import BaseModel
from typing import Dict, List, Optional


class MetricsDTO(BaseModel):
    spend: float
    prompt_tokens: int
    completion_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    total_tokens: int
    successful_requests: int
    failed_requests: int
    api_requests: int


class ApiKeyBreakdownDTO(BaseModel):
    metrics: MetricsDTO
    metadata: Dict[str, Optional[str]]


class ModelBreakdownDTO(BaseModel):
    metrics: MetricsDTO
    metadata: Dict
    api_key_breakdown: Dict[str, ApiKeyBreakdownDTO]


class BreakdownDTO(BaseModel):
    mcp_servers: Dict
    models: Dict[str, ModelBreakdownDTO]
    model_groups: Dict[str, ModelBreakdownDTO]
    providers: Dict[str, ModelBreakdownDTO]
    api_keys: Dict[str, ApiKeyBreakdownDTO]
    entities: Dict[str, ModelBreakdownDTO]


class DailyActivityResultDTO(BaseModel):
    date: str
    metrics: MetricsDTO
    breakdown: BreakdownDTO


class DailyActivityMetadataDTO(BaseModel):
    total_spend: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_api_requests: int
    total_successful_requests: int
    total_failed_requests: int
    total_cache_read_input_tokens: int
    total_cache_creation_input_tokens: int
    page: int
    total_pages: int
    has_more: bool


class DailyActivityResponseDTO(BaseModel):
    results: List[DailyActivityResultDTO]
    metadata: DailyActivityMetadataDTO