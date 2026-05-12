from swiss_ai_hub.agent.agents.expert_rag_agent import ExpertRAGAgentConfig


def get_all_templates() -> list[ExpertRAGAgentConfig]:
    from .engineering_expert_rag import build as build_engineering_expert_rag

    return [
        build_engineering_expert_rag(),
    ]
