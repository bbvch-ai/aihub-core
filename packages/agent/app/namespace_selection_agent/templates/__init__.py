from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import NamespaceSelectionAgentConfig


def get_all_templates() -> list[NamespaceSelectionAgentConfig]:
    from .shared_knowledge_selector import build as build_shared_knowledge_selector

    return [
        build_shared_knowledge_selector(),
    ]
