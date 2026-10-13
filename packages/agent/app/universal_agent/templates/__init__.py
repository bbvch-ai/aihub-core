from swiss_ai_hub.agent.agents.universal_agent import UniversalAgentConfig


def get_all_templates() -> list[UniversalAgentConfig]:
    from .data_analyst import build as build_data_analyst
    from .knowledge_assistant import build as build_knowledge_assistant
    from .workplace_assistant import build as build_workplace_assistant

    return [
        build_workplace_assistant(),
        build_knowledge_assistant(),
        build_data_analyst(),
    ]
