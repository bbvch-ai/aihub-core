import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.topic_managers.pipeline.pipeline_type_topic_manager import PipelineTypeTopicManager
from swiss_ai_hub.core.topics.pipeline.pipeline_topic import PipelineTopic


def _manager(pipeline_type: str = "rag") -> PipelineTypeTopicManager:
    return PipelineTypeTopicManager(pipeline_type=pipeline_type)


class TestStream:
    def test_one_stream_and_filter_per_ingestor_regardless_of_database_count(self):
        assert _manager().get_stream() == ("pipeline_rag_stream", "pipeline.rag.>")

    def test_two_ingestors_get_non_overlapping_stream_filters(self):
        """JetStream rejects overlapping subject filters, so two pipelines must never share a namespace."""
        _, rag_filter = _manager("rag").get_stream()
        _, acme_filter = _manager("acme_rag").get_stream()

        assert rag_filter != acme_filter
        assert not acme_filter.startswith(rag_filter.removesuffix(">"))


class TestSubject:
    def test_the_bucket_survives_a_round_trip_through_the_subject(self):
        subject = _manager().get_subject_for_source_updated(
            bucket_name="researchdocs",
            db_name="researchdocs",
            run_key="rk",
            event_name="SourceUpdatedEvent",
            event_id="eid",
        )

        assert subject == "pipeline.rag.researchdocs.to.knowledge.researchdocs.rk.SourceUpdatedEvent.eid"
        assert PipelineTypeTopicManager.bucket_from_subject(subject) == "researchdocs"

    def test_the_subject_still_parses_as_a_pipeline_topic(self):
        """The grammar is unchanged — only the source-type token now names the ingestor."""
        subject = _manager().get_subject_for_source_updated("bucket", "db", "rk", "Event", "eid")

        topic = PipelineTopic.from_subject(subject)

        assert (topic.source_type, topic.source_id, topic.target_type, topic.target_id) == (
            "rag",
            "bucket",
            "knowledge",
            "db",
        )


class TestReservedTokens:
    def test_rejects_datalake_because_it_would_overlap_the_legacy_streams(self):
        with pytest.raises(ValidationError, match="reserved"):
            _manager("datalake")

    @pytest.mark.parametrize("token", ["", "rag.pipeline", "rag*", "rag>", "two words"])
    def test_rejects_tokens_that_are_not_usable_in_a_subject(self, token):
        with pytest.raises(ValidationError):
            _manager(token)
