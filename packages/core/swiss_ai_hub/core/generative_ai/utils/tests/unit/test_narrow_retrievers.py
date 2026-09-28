import pytest

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.bucket_metadata_filters import BucketMetadataFilters
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
from swiss_ai_hub.core.generative_ai.utils.narrow_retrievers import narrow_retrievers
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig


def _retriever(
    bucket: str,
    index_namespaces: list[str] | None = None,
    allowed: list[str] | None = None,
) -> KnowledgeRetrieverConfig:
    return KnowledgeRetrieverConfig(
        embed_model=EmbeddingModelConfig(model_name="embedding/test"),
        vector_store=MilvusVectorStoreConfig(
            collection_name=bucket,
            dimensions=1024,
            index_namespaces=index_namespaces or [],
            all_namespaces=index_namespaces is None,
            allowed_metadata_filter_fields=allowed or [],
        ),
        retrieve_k=5,
    )


class TestNamespaceNarrowing:
    def test_empty_inputs_wrap_retrievers_unchanged(self):
        retrievers = [_retriever("bucket_a", ["ns1"])]
        runtime_configs = narrow_retrievers(retrievers, [], None)
        assert len(runtime_configs) == 1
        assert runtime_configs[0].config is retrievers[0]
        assert runtime_configs[0].additional_metadata_filters == []

    def test_selected_namespace_narrows_to_single_bucket(self):
        retrievers = [
            _retriever("bucket_a", ["ns1", "ns2"]),
            _retriever("bucket_b", ["ns3"]),
        ]
        runtime_configs = narrow_retrievers(
            retrievers,
            [BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
        )
        assert len(runtime_configs) == 1
        assert runtime_configs[0].config.vector_store.collection_name == "bucket_a"
        assert runtime_configs[0].config.vector_store.index_namespaces == ["ns1"]

    def test_all_namespaces_accepts_any_selection_and_narrows_to_it(self):
        retrievers = [_retriever("bucket_a")]
        runtime_configs = narrow_retrievers(
            retrievers,
            [BucketNamespacePair(bucket_name="bucket_a", namespace_name="anything")],
        )
        narrowed = runtime_configs[0].config.vector_store
        assert narrowed.index_namespaces == ["anything"]
        assert narrowed.all_namespaces is False

    def test_namespace_outside_configured_set_drops_retriever(self):
        retrievers = [_retriever("bucket_a", ["ns1"])]
        runtime_configs = narrow_retrievers(
            retrievers,
            [BucketNamespacePair(bucket_name="bucket_a", namespace_name="other")],
        )
        assert runtime_configs == []

    def test_several_pairs_on_one_bucket_narrow_to_all_of_them(self):
        """The multi-select emits one pair per collection, so the same bucket arrives repeatedly — keeping only the
        last would silently answer from one collection when the admin picked several."""
        retrievers = [_retriever("bucket_a", ["ns1", "ns2", "ns3"])]
        runtime_configs = narrow_retrievers(
            retrievers,
            [
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1"),
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns3"),
            ],
        )
        assert len(runtime_configs) == 1
        assert runtime_configs[0].config.vector_store.index_namespaces == ["ns1", "ns3"]

    def test_out_of_scope_namespace_is_dropped_without_dropping_its_bucket(self):
        """A selection half inside the agent's scope narrows to the half that is inside — dropping the whole
        retriever would answer from nothing instead of from the collections that are still valid."""
        retrievers = [_retriever("bucket_a", ["ns1"])]
        runtime_configs = narrow_retrievers(
            retrievers,
            [
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1"),
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="outside"),
            ],
        )
        assert len(runtime_configs) == 1
        assert runtime_configs[0].config.vector_store.index_namespaces == ["ns1"]

    def test_repeated_pair_reaches_the_filter_once(self):
        retrievers = [_retriever("bucket_a", ["ns1", "ns2"])]
        runtime_configs = narrow_retrievers(
            retrievers,
            [
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1"),
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1"),
            ],
        )
        assert runtime_configs[0].config.vector_store.index_namespaces == ["ns1"]

    def test_all_namespaces_retriever_keeps_every_selected_namespace(self):
        retrievers = [_retriever("bucket_a")]
        runtime_configs = narrow_retrievers(
            retrievers,
            [
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="one"),
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="two"),
            ],
        )
        narrowed = runtime_configs[0].config.vector_store
        assert narrowed.index_namespaces == ["one", "two"]
        assert narrowed.all_namespaces is False


class TestAdditionalFiltersThreading:
    def test_filters_attached_to_matching_runtime_config(self):
        retrievers = [
            _retriever("bucket_a", ["ns1"], allowed=["snk"]),
            _retriever("bucket_b", ["ns2"], allowed=["snk"]),
        ]
        runtime_configs = narrow_retrievers(
            retrievers,
            [
                BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1"),
                BucketNamespacePair(bucket_name="bucket_b", namespace_name="ns2"),
            ],
            [BucketMetadataFilters(bucket_name="bucket_a", filters=[MetadataFilterPair(key="snk", value="12345")])],
        )
        by_bucket = {rc.config.vector_store.collection_name: rc for rc in runtime_configs}
        assert by_bucket["bucket_a"].additional_metadata_filters == [MetadataFilterPair(key="snk", value="12345")]
        assert by_bucket["bucket_b"].additional_metadata_filters == []

    def test_missing_bucket_in_filters_keeps_retriever_without_extras(self):
        retrievers = [_retriever("bucket_a", ["ns1"], allowed=["snk"])]
        runtime_configs = narrow_retrievers(
            retrievers,
            [BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
            [],
        )
        assert len(runtime_configs) == 1
        assert runtime_configs[0].additional_metadata_filters == []

    def test_additional_filters_only_preserves_configured_index_namespaces(self):
        """Publisher sends no namespace selection but does send filters — the agent's configured
        namespace scope is preserved unchanged (this is the 'query all configured namespaces' path)."""
        retrievers = [_retriever("bucket_a", ["ns1", "ns2"], allowed=["snk"])]
        runtime_configs = narrow_retrievers(
            retrievers,
            [],
            [BucketMetadataFilters(bucket_name="bucket_a", filters=[MetadataFilterPair(key="snk", value="X")])],
        )
        assert len(runtime_configs) == 1
        assert runtime_configs[0].config.vector_store.index_namespaces == ["ns1", "ns2"]
        assert runtime_configs[0].additional_metadata_filters == [MetadataFilterPair(key="snk", value="X")]

    def test_config_untouched_when_no_narrowing_applies(self):
        """Config identity is preserved if neither namespace nor filters apply to this bucket."""
        retrievers = [_retriever("bucket_a", ["ns1"], allowed=["snk"])]
        runtime_configs = narrow_retrievers(retrievers, [], None)
        assert runtime_configs[0].config is retrievers[0]


class TestEnforcement:
    def test_unlisted_key_raises(self):
        retrievers = [_retriever("bucket_a", ["ns1"], allowed=["snk"])]
        with pytest.raises(ValueError, match="not allowed on bucket 'bucket_a'"):
            narrow_retrievers(
                retrievers,
                [BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
                [
                    BucketMetadataFilters(
                        bucket_name="bucket_a", filters=[MetadataFilterPair(key="customer", value="ACME")]
                    )
                ],
            )

    def test_reserved_namespace_key_raises(self):
        retrievers = [_retriever("bucket_a", ["ns1"], allowed=["namespace"])]
        with pytest.raises(ValueError, match="reserved"):
            narrow_retrievers(
                retrievers,
                [BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
                [
                    BucketMetadataFilters(
                        bucket_name="bucket_a", filters=[MetadataFilterPair(key="namespace", value="ns2")]
                    )
                ],
            )

    def test_unknown_bucket_raises(self):
        retrievers = [_retriever("bucket_a", ["ns1"], allowed=["snk"])]
        with pytest.raises(ValueError, match="unknown bucket"):
            narrow_retrievers(
                retrievers,
                [BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
                [BucketMetadataFilters(bucket_name="bucket_typo", filters=[MetadataFilterPair(key="snk", value="X")])],
            )

    def test_duplicate_bucket_entry_raises(self):
        retrievers = [_retriever("bucket_a", ["ns1"], allowed=["snk"])]
        with pytest.raises(ValueError, match="Duplicate additional_filters entry"):
            narrow_retrievers(
                retrievers,
                [BucketNamespacePair(bucket_name="bucket_a", namespace_name="ns1")],
                [
                    BucketMetadataFilters(bucket_name="bucket_a", filters=[MetadataFilterPair(key="snk", value="1")]),
                    BucketMetadataFilters(bucket_name="bucket_a", filters=[MetadataFilterPair(key="snk", value="2")]),
                ],
            )
