from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
        extend_chat_history_with_organization_memory,
    )
    from swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_user_memory import (
        extend_chat_history_with_user_memory,
    )
    from swiss_ai_hub.core.generative_ai.chat_history.format_chat_history import format_chat_history
    from swiss_ai_hub.core.generative_ai.chat_history.format_expert_conversation import format_expert_conversation
    from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history import limit_chat_history
    from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history_with_context import (
        limit_chat_history_with_context,
    )
    from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
        S3AnonymousFileAccessService,
    )
    from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import DocumentIntelligenceLoader
    from swiss_ai_hub.core.generative_ai.document.loaders.image_loader import ImageLoader
    from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
    from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import MineruLoader
    from swiss_ai_hub.core.generative_ai.document.loaders.raw_loader import RawLoader
    from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
        MarkdownStructuralNodeParser,
    )
    from swiss_ai_hub.core.generative_ai.document.parsers.recursive_summary_parser import RecursiveNodeSummarizer
    from swiss_ai_hub.core.generative_ai.document.refinement import refine_document_tables_with_metadata
    from swiss_ai_hub.core.generative_ai.document.types.file_type_config import FileTypeConfig
    from swiss_ai_hub.core.generative_ai.document.types.ingested_document import IngestedDocument
    from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
    from swiss_ai_hub.core.generative_ai.guards.agent_description_guard import agent_description_guard
    from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
    from swiss_ai_hub.core.generative_ai.guards.few_shot_guard import few_shot_guard
    from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory
    from swiss_ai_hub.core.generative_ai.memory.memory_settings import MemorySettings
    from swiss_ai_hub.core.generative_ai.memory.org_memory_config import OrgMemoryConfig
    from swiss_ai_hub.core.generative_ai.memory.organization_memory import OrganizationMemory
    from swiss_ai_hub.core.generative_ai.memory.user_memory import UserMemory
    from swiss_ai_hub.core.generative_ai.processors.models.retrieve_prev_next_config import RetrievePrevNextConfig
    from swiss_ai_hub.core.generative_ai.processors.vector_prev_next_post_processor import ModeOptions
    from swiss_ai_hub.core.generative_ai.prompting.few_shot.create_few_shot_messages import create_few_shot_messages
    from swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_example import FewShotExample
    from swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_guard_example import FewShotGuardExample
    from swiss_ai_hub.core.generative_ai.rerank.rerank_nodes import rerank_nodes
    from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
    from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import (
        LLMConfig,
        LLMParameter,
    )
    from swiss_ai_hub.core.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages
    from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
    from swiss_ai_hub.core.generative_ai.retrieval.combine_nodes_in_order import combine_nodes_in_order
    from swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question import condense_standalone_question
    from swiss_ai_hub.core.generative_ai.retrieval.retrieve_from_all_sources import retrieve_from_all_sources
    from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
    from swiss_ai_hub.core.generative_ai.retrieval.retrieve_prev_next_nodes import retrieve_prev_next_nodes
    from swiss_ai_hub.core.generative_ai.retrievers.bucket_metadata_filters import BucketMetadataFilters
    from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
    from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
    from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
    from swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config import RetrievalRuntimeConfig
    from swiss_ai_hub.core.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
    from swiss_ai_hub.core.generative_ai.utils.image_processor import replace_s3_paths_with_signed_urls
    from swiss_ai_hub.core.generative_ai.utils.narrow_retrievers import (
        narrow_retrievers,
    )
    from swiss_ai_hub.core.generative_ai.utils.path_utils import (
        FIGURES_DIRECTORY_NAME,
        create_figures_folder_name,
        decode_partition_key,
        encode_partition_key,
    )

__all__ = [
    "AgentMemory",
    "BucketMetadataFilters",
    "BucketNamespacePair",
    "DocumentIntelligenceLoader",
    "EmbeddingModelConfig",
    "FIGURES_DIRECTORY_NAME",
    "FewShotExample",
    "FewShotGuardExample",
    "FileTypeConfig",
    "ImageLoader",
    "IngestedDocument",
    "IngestedNode",
    "KnowledgeRetrieverConfig",
    "LLMConfig",
    "LLMParameter",
    "MarkItDownLoader",
    "MarkdownStructuralNodeParser",
    "MemorySettings",
    "MetadataFilterPair",
    "RetrievalRuntimeConfig",
    "MineruLoader",
    "ModeOptions",
    "OrgMemoryConfig",
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
    "create_figures_folder_name",
    "decode_partition_key",
    "encode_partition_key",
    "extend_chat_history_with_organization_memory",
    "extend_chat_history_with_user_memory",
    "few_shot_guard",
    "narrow_retrievers",
    "format_chat_history",
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
    "AgentMemory": "swiss_ai_hub.core.generative_ai.memory.agent_memory",
    "BucketMetadataFilters": "swiss_ai_hub.core.generative_ai.retrievers.bucket_metadata_filters",
    "BucketNamespacePair": "swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair",
    "DocumentIntelligenceLoader": "swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader",
    "EmbeddingModelConfig": "swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config",
    "FIGURES_DIRECTORY_NAME": "swiss_ai_hub.core.generative_ai.utils.path_utils",
    "FewShotExample": "swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_example",
    "FewShotGuardExample": "swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_guard_example",
    "FileTypeConfig": "swiss_ai_hub.core.generative_ai.document.types.file_type_config",
    "ImageLoader": "swiss_ai_hub.core.generative_ai.document.loaders.image_loader",
    "IngestedDocument": "swiss_ai_hub.core.generative_ai.document.types.ingested_document",
    "IngestedNode": "swiss_ai_hub.core.generative_ai.document.types.ingested_node",
    "KnowledgeRetrieverConfig": "swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config",
    "LLMConfig": "swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config",
    "LLMParameter": "swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config",
    "MarkItDownLoader": "swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader",
    "MarkdownStructuralNodeParser": "swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser",
    "MemorySettings": "swiss_ai_hub.core.generative_ai.memory.memory_settings",
    "MetadataFilterPair": "swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair",
    "RetrievalRuntimeConfig": "swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config",
    "MineruLoader": "swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader",
    "ModeOptions": "swiss_ai_hub.core.generative_ai.processors.vector_prev_next_post_processor",
    "OrgMemoryConfig": "swiss_ai_hub.core.generative_ai.memory.org_memory_config",
    "OrganizationMemory": "swiss_ai_hub.core.generative_ai.memory.organization_memory",
    "RawLoader": "swiss_ai_hub.core.generative_ai.document.loaders.raw_loader",
    "RecursiveNodeSummarizer": "swiss_ai_hub.core.generative_ai.document.parsers.recursive_summary_parser",
    "RerankingModelConfig": "swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config",
    "RetrievePrevNextConfig": "swiss_ai_hub.core.generative_ai.processors.models.retrieve_prev_next_config",
    "S3AnonymousFileAccessService": "swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service",
    "UserMemory": "swiss_ai_hub.core.generative_ai.memory.user_memory",
    "agent_description_guard": "swiss_ai_hub.core.generative_ai.guards.agent_description_guard",
    "combine_nodes_in_order": "swiss_ai_hub.core.generative_ai.retrieval.combine_nodes_in_order",
    "condense_standalone_question": "swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question",
    "context_sufficient_guard": "swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard",
    "create_few_shot_messages": "swiss_ai_hub.core.generative_ai.prompting.few_shot.create_few_shot_messages",
    "create_figures_folder_name": "swiss_ai_hub.core.generative_ai.utils.path_utils",
    "decode_partition_key": "swiss_ai_hub.core.generative_ai.utils.path_utils",
    "encode_partition_key": "swiss_ai_hub.core.generative_ai.utils.path_utils",
    "extend_chat_history_with_organization_memory": "swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_organization_memory",
    "extend_chat_history_with_user_memory": "swiss_ai_hub.core.generative_ai.chat_history.extend_chat_history_with_user_memory",
    "few_shot_guard": "swiss_ai_hub.core.generative_ai.guards.few_shot_guard",
    "narrow_retrievers": "swiss_ai_hub.core.generative_ai.utils.narrow_retrievers",
    "format_chat_history": "swiss_ai_hub.core.generative_ai.chat_history.format_chat_history",
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

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
