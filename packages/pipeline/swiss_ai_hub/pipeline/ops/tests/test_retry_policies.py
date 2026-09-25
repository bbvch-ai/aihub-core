from dagster import Backoff

from swiss_ai_hub.pipeline.ops.data_lake.parse_document_from_data_lake import parse_document_from_data_lake
from swiss_ai_hub.pipeline.ops.nodes.embed_nodes import embed_nodes
from swiss_ai_hub.pipeline.ops.nodes.insert_nodes_into_vector_store import insert_nodes_into_vector_store
from swiss_ai_hub.pipeline.ops.source.routed.write_data_lake_file_to_bucket import write_data_lake_file_to_bucket


def test_parse_document_retry_policy_stays_small():
    policy = parse_document_from_data_lake.retry_policy
    assert policy is not None
    assert policy.max_retries == 2
    assert policy.delay == 30
    assert policy.backoff == Backoff.EXPONENTIAL


def test_insert_nodes_retry_policy():
    policy = insert_nodes_into_vector_store.retry_policy
    assert policy is not None
    assert policy.max_retries == 2
    assert policy.delay == 10
    assert policy.backoff == Backoff.EXPONENTIAL


def test_embed_nodes_keeps_retries_for_transient_failures():
    """Retries stay for 5xx/timeouts. Deterministic 400s are handled in the op, so they never reach the policy."""
    policy = embed_nodes.retry_policy
    assert policy is not None
    assert policy.max_retries == 6
    assert policy.delay == 1
    assert policy.backoff == Backoff.EXPONENTIAL


def test_write_data_lake_file_retries_transient_storage_failures():
    policy = write_data_lake_file_to_bucket.retry_policy
    assert policy is not None
    assert policy.max_retries == 2
    assert policy.delay == 5
    assert policy.backoff == Backoff.EXPONENTIAL
