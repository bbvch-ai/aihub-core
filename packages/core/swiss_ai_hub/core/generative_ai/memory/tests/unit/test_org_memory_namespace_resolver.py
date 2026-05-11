import pytest

from swiss_ai_hub.core.generative_ai.memory.org_memory_namespace_resolver import OrgMemoryNamespaceResolver


class TestResolveForSearch:
    def test_unrestricted_no_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=None, configured=[]) is None

    def test_unrestricted_with_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested="x", configured=[]) == ["x"]

    def test_whitelist_no_request_returns_full_set(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested=None, configured=["a", "b"]) == ["a", "b"]

    def test_whitelist_request_inside_narrows_to_one(self):
        assert OrgMemoryNamespaceResolver.resolve_for_search(requested="a", configured=["a", "b"]) == ["a"]

    def test_whitelist_request_outside_raises(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_search(requested="c", configured=["a", "b"])


class TestResolveForWrite:
    def test_unrestricted_no_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(requested=None, configured=[]) is None

    def test_unrestricted_with_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(requested="x", configured=[]) == "x"

    def test_single_entry_no_request_uses_that(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(requested=None, configured=["a"]) == "a"

    def test_single_entry_with_matching_request(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(requested="a", configured=["a"]) == "a"

    def test_multi_entry_no_request_is_ambiguous(self):
        with pytest.raises(ValueError, match="Ambiguous write"):
            OrgMemoryNamespaceResolver.resolve_for_write(requested=None, configured=["a", "b"])

    def test_multi_entry_request_inside(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(requested="b", configured=["a", "b"]) == "b"

    def test_multi_entry_request_outside_raises(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_write(requested="c", configured=["a", "b"])
