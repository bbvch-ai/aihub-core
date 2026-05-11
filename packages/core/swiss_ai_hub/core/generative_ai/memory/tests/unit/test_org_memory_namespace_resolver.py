import pytest

from swiss_ai_hub.core.generative_ai.memory.org_memory_namespace_resolver import OrgMemoryNamespaceResolver


class TestResolveForSearch:
    def test_unrestricted_no_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=[], configured=[]) is None

    def test_unrestricted_with_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=["x"], configured=[]) == ["x"]

    def test_unrestricted_with_multiple_requested(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=["x", "y"], configured=[]) == ["x", "y"]

    def test_whitelist_no_request_returns_full_set(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=[], configured=["a", "b"]) == ["a", "b"]

    def test_whitelist_request_subset(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=["a"], configured=["a", "b"]) == ["a"]

    def test_whitelist_request_multiple_subset(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=["a", "b"], configured=["a", "b", "c"]) == [
            "a",
            "b",
        ]

    def test_whitelist_request_outside_raises(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_search(requested=["c"], configured=["a", "b"])

    def test_whitelist_request_partial_outside_raises(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_search(requested=["a", "c"], configured=["a", "b"])
