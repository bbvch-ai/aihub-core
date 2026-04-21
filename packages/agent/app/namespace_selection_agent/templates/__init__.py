from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import NamespaceSelectionAgentConfig

from .shared_knowledge_selector import TEMPLATE as SHARED_KNOWLEDGE_SELECTOR

ALL_TEMPLATES: list[NamespaceSelectionAgentConfig] = [
    SHARED_KNOWLEDGE_SELECTOR,
]
