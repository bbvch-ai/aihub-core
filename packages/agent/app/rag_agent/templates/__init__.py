from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig


def get_all_templates() -> list[RAGAgentConfig]:
    from .jira_story_assistant import build as build_jira_story_assistant
    from .shared_knowledge_rag import build as build_shared_knowledge_rag

    return [
        build_shared_knowledge_rag(),
        build_jira_story_assistant(),
    ]
