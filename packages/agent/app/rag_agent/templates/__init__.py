from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig


def get_all_templates() -> list[RAGAgentConfig]:
    from .shared_knowledge_rag import build as build_shared_knowledge_rag

    return [
        build_shared_knowledge_rag(),
    ]
