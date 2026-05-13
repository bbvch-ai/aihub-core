import pytest

from swiss_ai_hub.core.generative_ai.memory.org_memory_namespace_resolver import OrgMemoryNamespaceResolver


class TestResolveForWrite:
    def test_unrestricted_uses_event_override(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(event_override="a", default="b", allowed=[]) == "a"

    def test_unrestricted_falls_back_to_default(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(event_override=None, default="b", allowed=[]) == "b"

    def test_unrestricted_returns_none_when_no_override_or_default(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(event_override=None, default=None, allowed=[]) is None

    def test_allow_list_accepts_event_override_inside(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(event_override="a", default="b", allowed=["a", "b"]) == "a"

    def test_allow_list_accepts_default_inside(self):
        assert OrgMemoryNamespaceResolver.resolve_for_write(event_override=None, default="b", allowed=["a", "b"]) == "b"

    def test_allow_list_rejects_event_override_outside(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_write(event_override="c", default="a", allowed=["a", "b"])

    def test_allow_list_rejects_default_outside(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_write(event_override=None, default="c", allowed=["a", "b"])

    def test_allow_list_rejects_unscoped_write(self):
        with pytest.raises(ValueError, match="allow-list"):
            OrgMemoryNamespaceResolver.resolve_for_write(event_override=None, default=None, allowed=["a", "b"])


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
