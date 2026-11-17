"""Unit tests for PatchedMilvusDB._create_filter and PatchedMilvusDB.get.

mem0's MilvusDB renders any non-string filter value literally, so the
`{"in": [...]}` namespace allow-list becomes `== {'in': [...]}` and Milvus
rejects the query plan. These tests pin the corrected `in [...]` translation.
"""

from unittest.mock import MagicMock

from swiss_ai_hub.core.infrastructure.mem0.patched_milvus_db import PatchedMilvusDB


def _db_returning(rows: list[dict]) -> PatchedMilvusDB:
    database = PatchedMilvusDB.__new__(PatchedMilvusDB)
    database.collection_name = "mem0"
    database.client = MagicMock()
    database.client.get.return_value = rows
    return database


def test_get_unknown_id_returns_none():
    """Upstream raised IndexError here, so an unknown id surfaced as a 500 instead of "not found"."""
    assert _db_returning([]).get("missing") is None


def test_get_known_id_returns_payload():
    result = _db_returning([{"id": "m1", "metadata": {"user_id": "u1"}}]).get("m1")
    assert result.id == "m1"
    assert result.payload == {"user_id": "u1"}


def _filter(filters: dict) -> str:
    return PatchedMilvusDB._create_filter(PatchedMilvusDB.__new__(PatchedMilvusDB), filters)


def test_scalar_string_uses_quoted_equality():
    assert _filter({"_tenant_id": "ACME"}) == '(metadata["_tenant_id"] == "ACME")'


def test_in_operator_renders_milvus_in_clause():
    expression = _filter({"_tenant_namespace": {"in": ["bbv vietnam", "QC Community"]}})
    assert expression == '(metadata["_tenant_namespace"] in ["bbv vietnam", "QC Community"])'


def test_string_values_escape_quotes():
    assert _filter({"_tenant_namespace": 'say "hi"'}) == '(metadata["_tenant_namespace"] == "say \\"hi\\"")'


def test_string_values_escape_backslashes():
    assert _filter({"_tenant_namespace": "a\\b"}) == '(metadata["_tenant_namespace"] == "a\\\\b")'


def test_mixed_filters_join_with_and():
    expression = _filter(
        {
            "_type": "organization_memory",
            "_tenant_namespace": {"in": ["dept-x", "dept-y"]},
        }
    )
    assert expression == (
        '(metadata["_type"] == "organization_memory") and (metadata["_tenant_namespace"] in ["dept-x", "dept-y"])'
    )
