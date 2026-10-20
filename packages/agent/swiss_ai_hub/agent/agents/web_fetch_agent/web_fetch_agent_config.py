from typing import Annotated

from pydantic import Field

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig


class WebFetchAgentConfig(LLMWrappingAgentConfig):
    """
    Configuration for WebFetchAgent: the instructed assistant's settings with web fetch required.

    Reading links is what this blueprint is for, so the form shows the limits without an enable toggle and no
    profile can switch reading off.
    """

    web_fetch: Annotated[
        WebFetchConfig,
        Field(
            description="How the web pages a message links, pasted or referenced with #, are read.",
            title="Read Linked Web Pages",
        ),
    ] = WebFetchConfig()
