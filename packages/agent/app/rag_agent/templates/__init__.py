from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig

from .shared_knowledge_rag import TEMPLATE as SHARED_KNOWLEDGE_RAG

ALL_TEMPLATES: list[RAGAgentConfig] = [
    SHARED_KNOWLEDGE_RAG,
]
