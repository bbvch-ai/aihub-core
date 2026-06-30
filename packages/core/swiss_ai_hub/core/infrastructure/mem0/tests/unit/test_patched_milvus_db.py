"""Unit tests for PatchedMilvusDB._create_filter.

mem0's MilvusDB renders any non-string filter value literally, so the
`{"in": [...]}` namespace allow-list becomes `== {'in': [...]}` and Milvus
rejects the query plan. These tests pin the corrected `in [...]` translation.
"""

from swiss_ai_hub.core.infrastructure.mem0.patched_milvus_db import PatchedMilvusDB


def _filter(filters: dict) -> str:
    return PatchedMilvusDB._create_filter(PatchedMilvusDB.__new__(PatchedMilvusDB), filters)


def test_scalar_string_uses_quoted_equality():
    assert _filter({"_tenant_id": "ACME"}) == '(metadata["_tenant_id"] == "ACME")'


def test_in_operator_renders_milvus_in_clause():
    expression = _filter({"_tenant_namespace": {"in": ["bbv vietnam", "QC Community"]}})
    assert expression == '(metadata["_tenant_namespace"] in ["bbv vietnam", "QC Community"])'


def test_mixed_filters_join_with_and():
    expression = _filter(
        {
            "_type": "organization_memory",
            "_tenant_namespace": {"in": ["dept-x", "dept-y"]},
        }
    )
    assert expression == (
        '(metadata["_type"] == "organization_memory") '
        'and (metadata["_tenant_namespace"] in ["dept-x", "dept-y"])'
    )
