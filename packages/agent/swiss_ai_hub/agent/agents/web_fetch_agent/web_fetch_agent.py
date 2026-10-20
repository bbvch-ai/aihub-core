from typing import ClassVar

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class WebFetchAgent(LLMWrappingAgent):
    """An instructed assistant for answering from the web pages a message links.

    The steps are `LLMWrappingAgent`'s, which read the linked pages next to memory, attached files and referenced
    knowledge. What sets this blueprint apart is `WebFetchAgentConfig`, which requires web fetch, so every profile
    reads the pages, and an admin looking for an assistant that reads links finds it as a blueprint of its own.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.web_fetch_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.web_fetch_agent.metadata.description"
    )
    icon: ClassVar[str] = "mdi:web"
