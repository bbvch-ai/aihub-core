"""
Unit tests for NamespaceSelectionAgent helper functions.

These tests focus on the pure logic functions that don't require
full agent infrastructure, making them faster and more reliable.
"""

from aihub_lib.nats.events import KnowledgeSource

from aihub_agent.agents.NamespaceSelectionAgent.helpers.namespace_selector import (
    AvailableNamespace,
    _build_context_text,
    _build_namespace_list_text,
    _parse_selection_response,
)
from aihub_agent.agents.NamespaceSelectionAgent.helpers.selection_validator import (
    normalize_selection,
)


class TestBuildNamespaceListText:
    """Tests for _build_namespace_list_text helper."""

    def test_empty_list(self):
        result = _build_namespace_list_text([])
        assert result == ""

    def test_single_namespace_minimal(self):
        ns = AvailableNamespace(
            bucket_name="knowledge",
            bucket_id="123",
            namespace_name="policies",
        )
        result = _build_namespace_list_text([ns])
        assert result == "- knowledge/policies"

    def test_single_namespace_with_display_name(self):
        ns = AvailableNamespace(
            bucket_name="knowledge",
            bucket_id="123",
            namespace_name="policies",
            display_name="Company Policies",
        )
        result = _build_namespace_list_text([ns])
        assert result == "- knowledge/policies (Company Policies)"

    def test_single_namespace_with_description(self):
        ns = AvailableNamespace(
            bucket_name="knowledge",
            bucket_id="123",
            namespace_name="policies",
            display_name="Company Policies",
            description="HR and company-wide policies",
        )
        result = _build_namespace_list_text([ns])
        assert result == "- knowledge/policies (Company Policies): HR and company-wide policies"

    def test_multiple_namespaces(self):
        namespaces = [
            AvailableNamespace(bucket_name="docs", bucket_id="1", namespace_name="api"),
            AvailableNamespace(bucket_name="docs", bucket_id="1", namespace_name="guides", display_name="User Guides"),
        ]
        result = _build_namespace_list_text(namespaces)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "- docs/api" in lines[0]
        assert "- docs/guides (User Guides)" in lines[1]


class TestBuildContextText:
    """Tests for _build_context_text helper."""

    def test_none_context(self):
        result = _build_context_text(None)
        assert result == ""

    def test_empty_list(self):
        result = _build_context_text([])
        assert result == ""

    def test_single_context(self):
        result = _build_context_text(["User prefers technical docs"])
        assert "Previous clarification exchanges" in result
        assert "User prefers technical docs" in result

    def test_multiple_context(self):
        result = _build_context_text(["First feedback", "Second feedback"])
        assert "First feedback" in result
        assert "Second feedback" in result


class TestParseSelectionResponse:
    """Tests for _parse_selection_response helper."""

    def setup_method(self):
        self.available_namespaces = [
            AvailableNamespace(
                bucket_name="knowledge",
                bucket_id="1",
                namespace_name="hr-policies",
                display_name="HR Policies",
            ),
            AvailableNamespace(
                bucket_name="knowledge",
                bucket_id="1",
                namespace_name="tech-docs",
                display_name="Technical Docs",
            ),
            AvailableNamespace(
                bucket_name="external",
                bucket_id="2",
                namespace_name="vendor-docs",
            ),
        ]

    def test_valid_json_response(self):
        response = """
        {
            "selected_sources": [
                {"bucket_name": "knowledge", "namespace_name": "hr-policies"}
            ],
            "reasoning": "The query is about HR policies"
        }
        """
        result = _parse_selection_response(response, self.available_namespaces)

        assert len(result.selected_sources) == 1
        assert result.selected_sources[0].bucket_name == "knowledge"
        assert result.selected_sources[0].namespace_name == "hr-policies"
        assert result.selected_sources[0].display_name == "HR Policies"
        assert result.reasoning == "The query is about HR policies"

    def test_json_with_surrounding_text(self):
        response = """
        I'll analyze the query and select relevant sources.

        {
            "selected_sources": [
                {"bucket_name": "external", "namespace_name": "vendor-docs"}
            ],
            "reasoning": "Looking for vendor information"
        }

        This selection should help answer the query.
        """
        result = _parse_selection_response(response, self.available_namespaces)

        assert len(result.selected_sources) == 1
        assert result.selected_sources[0].namespace_name == "vendor-docs"

    def test_invalid_namespace_filtered(self):
        response = """
        {
            "selected_sources": [
                {"bucket_name": "knowledge", "namespace_name": "hr-policies"},
                {"bucket_name": "unknown", "namespace_name": "invalid"}
            ],
            "reasoning": "Selected sources"
        }
        """
        result = _parse_selection_response(response, self.available_namespaces)

        # Invalid namespace should be filtered out
        assert len(result.selected_sources) == 1
        assert result.selected_sources[0].namespace_name == "hr-policies"

    def test_no_json_in_response(self):
        response = "I don't know which sources to select."
        result = _parse_selection_response(response, self.available_namespaces)

        assert len(result.selected_sources) == 0
        assert "Failed to parse" in result.reasoning

    def test_malformed_json(self):
        response = '{"selected_sources": [invalid json'
        result = _parse_selection_response(response, self.available_namespaces)

        assert len(result.selected_sources) == 0
        assert "Failed to parse" in result.reasoning


class TestNormalizeSelection:
    """Tests for normalize_selection helper."""

    def setup_method(self):
        self.available = [
            AvailableNamespace(bucket_name="bucket1", bucket_id="1", namespace_name="ns1a"),
            AvailableNamespace(bucket_name="bucket1", bucket_id="1", namespace_name="ns1b"),
            AvailableNamespace(bucket_name="bucket2", bucket_id="2", namespace_name="ns2a"),
        ]
        self.allowed_buckets = ["bucket1", "bucket2"]

    def test_empty_sources_fills_all_buckets(self):
        """Empty sources should auto-fill all allowed buckets."""
        result = normalize_selection([], self.available, self.allowed_buckets)

        assert len(result) == 2
        bucket_names = {s.bucket_name for s in result}
        assert bucket_names == {"bucket1", "bucket2"}

    def test_all_buckets_covered_unchanged(self):
        """When all buckets covered, returns exactly those sources."""
        sources = [
            KnowledgeSource(bucket_name="bucket1", namespace_name="ns1a"),
            KnowledgeSource(bucket_name="bucket2", namespace_name="ns2a"),
        ]
        result = normalize_selection(sources, self.available, self.allowed_buckets)

        assert len(result) == 2

    def test_missing_bucket_auto_filled(self):
        """Missing bucket gets first available namespace."""
        sources = [KnowledgeSource(bucket_name="bucket1", namespace_name="ns1a")]
        result = normalize_selection(sources, self.available, self.allowed_buckets)

        assert len(result) == 2
        bucket2_source = next(s for s in result if s.bucket_name == "bucket2")
        assert bucket2_source.namespace_name == "ns2a"

    def test_duplicate_bucket_keeps_first(self):
        """Multiple selections from same bucket keeps only first."""
        sources = [
            KnowledgeSource(bucket_name="bucket1", namespace_name="first"),
            KnowledgeSource(bucket_name="bucket1", namespace_name="second"),
            KnowledgeSource(bucket_name="bucket2", namespace_name="ns2a"),
        ]
        result = normalize_selection(sources, self.available, self.allowed_buckets)

        assert len(result) == 2
        bucket1_source = next(s for s in result if s.bucket_name == "bucket1")
        assert bucket1_source.namespace_name == "first"

    def test_combined_dedupe_and_fill(self):
        """Handles both deduplication and missing bucket filling."""
        sources = [
            KnowledgeSource(bucket_name="bucket1", namespace_name="first"),
            KnowledgeSource(bucket_name="bucket1", namespace_name="second"),
            # bucket2 is missing
        ]
        result = normalize_selection(sources, self.available, self.allowed_buckets)

        assert len(result) == 2
        bucket1_source = next(s for s in result if s.bucket_name == "bucket1")
        bucket2_source = next(s for s in result if s.bucket_name == "bucket2")
        assert bucket1_source.namespace_name == "first"  # Kept first
        assert bucket2_source.namespace_name == "ns2a"  # Auto-filled