"""Configuration for AgentDeveloperAgent."""

from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig


class AgentDeveloperAgentConfig(AgentConfig):
    """
    Configuration for AgentDeveloperAgent.

    This agent proxies user requests to an OpenCode server
    running in an agent development container, enabling developers
    to build AI agents through chat interface.
    """

    # OpenCode server connection
    opencode_server_url: str = Field(
        ...,  # Required
        description="URL of OpenCode server (e.g., http://agent-1-dev:8080)",
        examples=["http://localhost:8080", "http://agent-1-dev:8080"],
    )

    # Timeouts
    opencode_timeout: int = Field(
        default=300,  # 5 minutes
        description="Timeout for OpenCode operations (seconds)",
        ge=60,
        le=600,
    )

    # Model configuration
    model_id: str | None = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model ID to use in OpenCode (provider-specific)",
    )

    provider_id: str | None = Field(
        default="anthropic",
        description="Provider ID for model (e.g., 'anthropic', 'openai')",
    )

    # Initialization
    initialization_prompt: str = Field(
        default="""You are an AI agent builder for Swiss AI-Hub.

Read the following documentation to understand the architecture:
- /workspace/BUILD_GUIDE.md - Complete agent build guide
- /workspace/AGENTS.md - Platform architecture
- /workspace/aihub_agent_guide.md - Agent-specific patterns

Follow Swiss AI-Hub conventions:
- Use @step() decorators for workflow steps
- Type-hint everything (parameters AND return types)
- Use Pydantic models for configuration
- Create comprehensive tests
- Follow the guide exactly

When building an agent:
1. Create the agent class with @step methods
2. Create AgentConfig subclass
3. Create custom events if needed
4. Write tests (unit + integration)
5. Run make pr-ready to format and lint
6. Run make test to verify all tests pass

Always make agents production-ready.""",
        description="System prompt sent to OpenCode on session initialization",
    )

    # Response formatting
    show_file_changes: bool = Field(
        default=True,
        description="Show file creation/modification events",
    )

    show_tool_calls: bool = Field(
        default=True,
        description="Show tool execution events",
    )

    verbose_output: bool = Field(
        default=False,
        description="Include detailed OpenCode event information",
    )
