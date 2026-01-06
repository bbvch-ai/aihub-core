"""
Unit tests for retriever_builders module.

Tests the build_retrievers_from_sources function used by
RAGAgent and ExpertRAGAgent for dynamic retriever configuration.

Note: Tests for successful builds require integration with real Pydantic models.
Only error cases are unit tested here.
"""

from unittest.mock import MagicMock

import pytest
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.nats.events import KnowledgeSource

from aihub_agent.rag.retriever_builders import build_retrievers_from_sources


def _create_mock_retriever(bucket_name: str) -> MagicMock:
    """Create a mock retriever that passes isinstance check for KnowledgeRetrieverConfig."""
    mock = MagicMock(spec=KnowledgeRetrieverConfig)
    mock.vector_store = MagicMock()
    mock.vector_store.collection_name = bucket_name
    return mock


class TestBuildRetrieversFromSources:
    """Tests for build_retrievers_from_sources function."""

    def test_no_knowledge_retriever_config_raises(self):
        """Test error when no KnowledgeRetrieverConfig in existing retrievers."""
        sources = [KnowledgeSource(bucket_name="bucket1", namespace_name="ns1")]
        # Create a non-KnowledgeRetrieverConfig retriever (different type, not a mock with spec)
        non_knowledge_retriever = MagicMock()
        # Ensure isinstance check fails by not using spec=KnowledgeRetrieverConfig

        with pytest.raises(ValueError, match="no KnowledgeRetrieverConfig found"):
            build_retrievers_from_sources(sources, [non_knowledge_retriever])

    def test_bucket_not_configured_raises(self):
        """Test error when source bucket has no configured retriever."""
        sources = [KnowledgeSource(bucket_name="unconfigured_bucket", namespace_name="ns1")]
        existing = [_create_mock_retriever("bucket1")]

        with pytest.raises(ValueError, match="No retriever configured for bucket 'unconfigured_bucket'"):
            build_retrievers_from_sources(sources, existing)

    def test_empty_sources_returns_empty(self):
        """Test empty sources list returns empty result."""
        existing = [_create_mock_retriever("bucket1")]

        result = build_retrievers_from_sources([], existing)

        assert result == []

    def test_empty_retrievers_with_sources_raises(self):
        """Test error when retrievers list is empty but sources are provided."""
        sources = [KnowledgeSource(bucket_name="bucket1", namespace_name="ns1")]

        with pytest.raises(ValueError, match="no KnowledgeRetrieverConfig found"):
            build_retrievers_from_sources(sources, [])
