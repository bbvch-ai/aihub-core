from typing import Annotated

from pydantic import BaseModel, Field


class LLMSpend(BaseModel):
    """LLM spend aggregated over one attribution key (a user or a tenant).

    Costs come from the platform's own `LLMCostEvent` records rather than from LiteLLM's spend log:
    the gateway can only attribute the user, so the tenant dimension exists here alone (see #1451).
    """

    user_id: Annotated[str | None, Field(description="Invoking user, None when grouping by tenant.")] = None
    tenant_id: Annotated[str | None, Field(description="Acting tenant, None for runs outside a tenant.")] = None
    calls: Annotated[int, Field(description="Number of LLM calls attributed to this key.")] = 0
    prompt_tokens_costs: Annotated[float, Field(description="Cost of prompt tokens.")] = 0.0
    completion_tokens_costs: Annotated[float, Field(description="Cost of completion tokens.")] = 0.0
    embedding_tokens_costs: Annotated[float, Field(description="Cost of embedding tokens.")] = 0.0
    total_costs: Annotated[float, Field(description="Sum of prompt, completion and embedding costs.")] = 0.0
