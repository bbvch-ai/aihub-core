from dagster import Backoff

from swiss_ai_hub.pipeline.ops.data_lake.parse_document_from_data_lake import parse_document_from_data_lake
from swiss_ai_hub.pipeline.ops.nodes.insert_nodes_into_vector_store import insert_nodes_into_vector_store


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
