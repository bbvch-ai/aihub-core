from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from pydantic import Field


class OrganizationMemoryAgentConfig(AgentConfig):
    """Configuration for OrganizationMemoryAgent.

    Defines the LLM used for memory-aware responses and the tenant context
    (ID and namespace) for memory scoping.
    """

    llm: Annotated[LLMConfig, Field(description="LLM configuration for memory-aware responses")]
    tenant_id: Annotated[str, Field(description="Tenant ID for memory scoping")]
    tenant_namespace: Annotated[str, Field(description="Tenant namespace for memory scoping")]
