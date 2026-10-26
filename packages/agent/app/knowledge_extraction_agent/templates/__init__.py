from swiss_ai_hub.agent.agents.knowledge_extraction_agent import KnowledgeExtractionAgentConfig


def get_all_templates() -> list[KnowledgeExtractionAgentConfig]:
    from .document_tables import build as build_document_tables

    return [build_document_tables()]
