"""Configuration for AgentDeveloperAgent."""

from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from pydantic import Field, SecretStr


class AgentDeveloperAgentConfig(AgentConfig):
    """
    Configuration for AgentDeveloperAgent.

    This agent proxies user requests to an OpenCode server, enabling developers
    to build AI agents through chat interface. The LLM configuration determines
    which model OpenCode uses via the litellm proxy.
    """

    llm: Annotated[LLMConfig, Field(description="LLM configuration for OpenCode model selection")]

    opencode_server_url: Annotated[
        str,
        Field(
            description="URL of OpenCode server (e.g., http://agent-1-dev:8080)",
            examples=["http://localhost:8080", "http://agent-1-dev:8080"],
        ),
    ]

    opencode_token: Annotated[
        SecretStr,
        Field(description="Authentication token for OpenCode server"),
    ]

    opencode_timeout: Annotated[
        int,
        Field(
            default=300,
            description="Timeout for OpenCode operations in seconds",
            ge=60,
            le=600,
        ),
    ] = 300
