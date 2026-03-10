from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
        extend_chat_history_with_organization_memory,
    )
    from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_user_memory import (
        extend_chat_history_with_user_memory,
    )
    from swiss_ai_hub.core.generative_ai.chat_history.format_expert_conversation import format_expert_conversation
    from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history import limit_chat_history
    from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history_with_context import (
        limit_chat_history_with_context,
    )
    from swiss_ai_hub.core.generative_ai.document.accessor.S3AnonymousFileAccessService import (
        S3AnonymousFileAccessService,
    )
    from swiss_ai_hub.core.generative_ai.document.loaders.MarkItDownLoader import MarkItDownLoader
    from swiss_ai_hub.core.generative_ai.document.loaders.MineruLoader import MineruLoader
    from swiss_ai_hub.core.generative_ai.document.loaders.RawLoader import RawLoader
    from swiss_ai_hub.core.generative_ai.document.parsers.MarkdownStructuralNodeParser import (
        MarkdownStructuralNodeParser,
    )
    from swiss_ai_hub.core.generative_ai.document.parsers.RecursiveSummaryParser import RecursiveNodeSummarizer
    from swiss_ai_hub.core.generative_ai.document.refinement import refine_document_tables_with_metadata
    from swiss_ai_hub.core.generative_ai.document.types.FileTypeConfig import FileTypeConfig
    from swiss_ai_hub.core.generative_ai.document.types.IngestedDocument import IngestedDocument
    from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
    from swiss_ai_hub.core.generative_ai.guards.agent_description_guard import agent_description_guard
    from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
    from swiss_ai_hub.core.generative_ai.guards.few_shot_guard import few_shot_guard
    from swiss_ai_hub.core.generative_ai.memory.AgentMemory import AgentMemory
    from swiss_ai_hub.core.generative_ai.memory.MemorySettings import MemorySettings
    from swiss_ai_hub.core.generative_ai.memory.OrganizationMemory import OrganizationMemory
    from swiss_ai_hub.core.generative_ai.memory.UserMemory import UserMemory
    from swiss_ai_hub.core.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
    from swiss_ai_hub.core.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
    from swiss_ai_hub.core.generative_ai.prompting.few_shot.create_few_shot_messages import create_few_shot_messages
    from swiss_ai_hub.core.generative_ai.prompting.few_shot.FewShotExample import FewShotExample
    from swiss_ai_hub.core.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
    from swiss_ai_hub.core.generative_ai.rerank.rerank_nodes import rerank_nodes
    from swiss_ai_hub.core.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
    from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
    from swiss_ai_hub.core.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages
    from swiss_ai_hub.core.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
    from swiss_ai_hub.core.generative_ai.retrieval.combine_nodes_in_order import combine_nodes_in_order
    from swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
    from swiss_ai_hub.core.generative_ai.retrieval.retrieve_from_all_sources import retrieve_from_all_sources
    from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
    from swiss_ai_hub.core.generative_ai.retrieval.retrieve_prev_next_nodes import retrieve_prev_next_nodes
    from swiss_ai_hub.core.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
    from swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
    from swiss_ai_hub.core.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
    from swiss_ai_hub.core.generative_ai.utils.filter_retrievers_by_namespace import filter_retrievers_by_namespace
    from swiss_ai_hub.core.generative_ai.utils.image_processor import replace_s3_paths_with_signed_urls

__all__ = [
    "AgentMemory",
    "BucketNamespacePair",
    "EmbeddingModelConfig",
    "FewShotExample",
    "FewShotGuardExample",
    "FileTypeConfig",
    "IngestedDocument",
    "IngestedNode",
    "KnowledgeRetrieverConfig",
    "LLMConfig",
    "LLMParameter",
    "MarkItDownLoader",
    "MarkdownStructuralNodeParser",
    "MemorySettings",
    "MineruLoader",
    "ModeOptions",
    "OrganizationMemory",
    "RawLoader",
    "RecursiveNodeSummarizer",
    "RerankingModelConfig",
    "RetrievePrevNextConfig",
    "S3AnonymousFileAccessService",
    "UserMemory",
    "agent_description_guard",
    "combine_nodes_in_order",
    "condense_standalone_question",
    "context_sufficient_guard",
    "create_few_shot_messages",
    "extend_chat_history_with_organization_memory",
    "extend_chat_history_with_user_memory",
    "few_shot_guard",
    "filter_retrievers_by_namespace",
    "format_expert_conversation",
    "limit_chat_history",
    "limit_chat_history_with_context",
    "merge_consecutive_messages",
    "refine_document_tables_with_metadata",
    "replace_s3_paths_with_signed_urls",
    "rerank_nodes",
    "retrieve_from_all_sources",
    "retrieve_nodes",
    "retrieve_prev_next_nodes",
    "route_to_event_using_llm",
]

_LAZY_IMPORTS = {
    "AgentMemory": "swiss_ai_hub.core.generative_ai.memory.AgentMemory",
    "BucketNamespacePair": "swiss_ai_hub.core.generative_ai.retrievers.BucketNamespacePair",
    "EmbeddingModelConfig": "swiss_ai_hub.core.generative_ai.resources.models.llm.EmbeddingModelConfig",
    "FewShotExample": "swiss_ai_hub.core.generative_ai.prompting.few_shot.FewShotExample",
    "FewShotGuardExample": "swiss_ai_hub.core.generative_ai.prompting.few_shot.FewShotGuardExample",
    "FileTypeConfig": "swiss_ai_hub.core.generative_ai.document.types.FileTypeConfig",
    "IngestedDocument": "swiss_ai_hub.core.generative_ai.document.types.IngestedDocument",
    "IngestedNode": "swiss_ai_hub.core.generative_ai.document.types.IngestedNode",
    "KnowledgeRetrieverConfig": "swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetrieverConfig",
    "LLMConfig": "swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig",
    "LLMParameter": "swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig",
    "MarkItDownLoader": "swiss_ai_hub.core.generative_ai.document.loaders.MarkItDownLoader",
    "MarkdownStructuralNodeParser": "swiss_ai_hub.core.generative_ai.document.parsers.MarkdownStructuralNodeParser",
    "MemorySettings": "swiss_ai_hub.core.generative_ai.memory.MemorySettings",
    "MineruLoader": "swiss_ai_hub.core.generative_ai.document.loaders.MineruLoader",
    "ModeOptions": "swiss_ai_hub.core.generative_ai.processors.VectorPrevNextPostProcessor",
    "OrganizationMemory": "swiss_ai_hub.core.generative_ai.memory.OrganizationMemory",
    "RawLoader": "swiss_ai_hub.core.generative_ai.document.loaders.RawLoader",
    "RecursiveNodeSummarizer": "swiss_ai_hub.core.generative_ai.document.parsers.RecursiveSummaryParser",
    "RerankingModelConfig": "swiss_ai_hub.core.generative_ai.resources.models.llm.RerankingModelConfig",
    "RetrievePrevNextConfig": "swiss_ai_hub.core.generative_ai.processors.models.RetrievePrevNextConfig",
    "S3AnonymousFileAccessService": "swiss_ai_hub.core.generative_ai.document.accessor.S3AnonymousFileAccessService",
    "UserMemory": "swiss_ai_hub.core.generative_ai.memory.UserMemory",
    "agent_description_guard": "swiss_ai_hub.core.generative_ai.guards.agent_description_guard",
    "combine_nodes_in_order": "swiss_ai_hub.core.generative_ai.retrieval.combine_nodes_in_order",
    "condense_standalone_question": "swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question",
    "context_sufficient_guard": "swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard",
    "create_few_shot_messages": "swiss_ai_hub.core.generative_ai.prompting.few_shot.create_few_shot_messages",
    "extend_chat_history_with_organization_memory": "swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory",
    "extend_chat_history_with_user_memory": "swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_user_memory",
    "few_shot_guard": "swiss_ai_hub.core.generative_ai.guards.few_shot_guard",
    "filter_retrievers_by_namespace": "swiss_ai_hub.core.generative_ai.utils.filter_retrievers_by_namespace",
    "format_expert_conversation": "swiss_ai_hub.core.generative_ai.chat_history.format_expert_conversation",
    "limit_chat_history": "swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history",
    "limit_chat_history_with_context": "swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history_with_context",
    "merge_consecutive_messages": "swiss_ai_hub.core.generative_ai.resources.models.llm.message_preprocessor",
    "refine_document_tables_with_metadata": "swiss_ai_hub.core.generative_ai.document.refinement",
    "replace_s3_paths_with_signed_urls": "swiss_ai_hub.core.generative_ai.utils.image_processor",
    "rerank_nodes": "swiss_ai_hub.core.generative_ai.rerank.rerank_nodes",
    "retrieve_from_all_sources": "swiss_ai_hub.core.generative_ai.retrieval.retrieve_from_all_sources",
    "retrieve_nodes": "swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes",
    "retrieve_prev_next_nodes": "swiss_ai_hub.core.generative_ai.retrieval.retrieve_prev_next_nodes",
    "route_to_event_using_llm": "swiss_ai_hub.core.generative_ai.routing.route_to_event_using_llm",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
