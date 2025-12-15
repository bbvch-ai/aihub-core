from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig


class OrganizationMemoryAgentConfig(AgentConfig):
    """Configuration for OrganizationMemoryAgent.

    Defines the LLM used for memory-aware responses and the tenant context
    (ID and namespace) for memory scoping.
    """

    llm: LLMConfig
    tenant_id: str = "AIHub"
    tenant_namespace: str = "Engineering"
