from unittest.mock import MagicMock

import pytest
from dagster import InputContext, OpExecutionContext

from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG, bucket_from_partition_key, bucket_from_run_tag

BUCKET = "researchdocs"


class TestBucketFromRunTag:
    def test_reads_the_tag_from_an_op_context(self):
        context = MagicMock(spec=OpExecutionContext)
        context.run_tags = {BUCKET_RUN_TAG: BUCKET}

        assert bucket_from_run_tag(context) == BUCKET

    def test_reads_the_tag_from_an_input_context(self):
        context = MagicMock(spec=InputContext)
        context.step_context.run_tags = {BUCKET_RUN_TAG: BUCKET}

        assert bucket_from_run_tag(context) == BUCKET

    def test_an_untagged_run_fails_loudly_rather_than_guessing_a_database(self):
        """Silently defaulting would ingest one knowledge database's documents into another."""
        context = MagicMock(spec=OpExecutionContext)
        context.run_tags = {}

        with pytest.raises(ValueError, match=BUCKET_RUN_TAG):
            bucket_from_run_tag(context)


class TestDagsterInternalsRelianceIsPinned:
    def test_op_execution_context_still_exposes_run_tags_publicly(self):
        assert hasattr(OpExecutionContext, "run_tags")

    def test_input_context_still_has_no_public_run_tags_accessor(self):
        """If this starts failing, Dagster has given InputContext a public accessor and
        ``bucket_from_run_tag`` should stop reaching into ``step_context``."""
        assert not hasattr(InputContext, "run_tags")

    def test_input_context_still_exposes_step_context(self):
        """The non-public accessor the IO managers depend on. A Dagster upgrade that removes or renames
        it breaks routing on the non-partitioned read path, so fail here rather than at runtime."""
        assert hasattr(InputContext, "step_context")


class TestBucketFromPartitionKey:
    def test_reads_the_bucket_out_of_a_composite_key(self):
        assert bucket_from_partition_key(f"{BUCKET}|s3:%2F%2Fresearchdocs%2Fa.pdf") == BUCKET
