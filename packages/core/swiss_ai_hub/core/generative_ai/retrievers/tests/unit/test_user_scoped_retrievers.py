"""A run's retrievers narrowed to what the asking user may read, by the knowledge UI's own rules."""

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.generative_ai.retrievers.retrieval_runtime_config import RetrievalRuntimeConfig
from swiss_ai_hub.core.generative_ai.retrievers.user_scoped_retrievers import UserScopedRetrievers
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig

TENANT = ["aihub.user.>"]
CATALOGUE = {"hr": ["policies", "salaries"], "engineering": ["runbooks"]}


def _runtime(database: str, namespaces: list[str] | None = None) -> RetrievalRuntimeConfig:
    return RetrievalRuntimeConfig.from_config(
        KnowledgeRetrieverConfig(
            embed_model=EmbeddingModelConfig(model_name="embedding/test"),
            vector_store=MilvusVectorStoreConfig(
                collection_name=database,
                dimensions=1024,
                index_namespaces=namespaces or [],
                all_namespaces=namespaces is None,
            ),
            retrieve_k=5,
        )
    )


def _restrict(rules: list[str], *runtime_configs: RetrievalRuntimeConfig) -> list[RetrievalRuntimeConfig]:
    return UserScopedRetrievers.restrict(list(runtime_configs), AccessChecker(rules, TENANT), CATALOGUE.__getitem__)


def _scope(runtime_configs: list[RetrievalRuntimeConfig]) -> list[tuple[str, list[str], bool]]:
    return [
        (
            c.config.vector_store.collection_name,
            c.config.vector_store.index_namespaces,
            c.config.vector_store.all_namespaces,
        )
        for c in runtime_configs
    ]


class TestNamedNamespaces:
    def test_only_the_readable_namespaces_are_searched(self):
        restricted = _restrict(["aihub.user.knowledge.hr.policies"], _runtime("hr", ["policies", "salaries"]))

        assert _scope(restricted) == [("hr", ["policies"], False)]

    def test_a_retriever_fully_readable_is_kept_as_it_is(self):
        runtime = _runtime("hr", ["policies"])

        assert _restrict(["aihub.user.knowledge.hr.>"], runtime) == [runtime]

    def test_a_retriever_with_nothing_readable_is_dropped(self):
        assert _restrict(["aihub.user.knowledge.engineering.>"], _runtime("hr", ["policies"])) == []


class TestWholeDatabase:
    def test_stays_whole_for_a_user_who_may_read_all_of_it(self):
        runtime = _runtime("hr")

        assert _restrict(["aihub.user.knowledge.hr.*"], runtime) == [runtime]

    def test_falls_back_to_the_readable_namespaces_otherwise(self):
        restricted = _restrict(["aihub.user.knowledge.hr.salaries"], _runtime("hr"))

        assert _scope(restricted) == [("hr", ["salaries"], False)]


class TestTwoUsers:
    def test_each_user_gets_their_own_collections_from_one_profile(self):
        profile = [_runtime("hr", ["policies", "salaries"]), _runtime("engineering", ["runbooks"])]

        anna = _restrict(["aihub.user.knowledge.engineering.>"], *profile)
        bob = _restrict(["aihub.user.knowledge.hr.policies"], *profile)

        assert _scope(anna) == [("engineering", ["runbooks"], False)]
        assert _scope(bob) == [("hr", ["policies"], False)]


def test_the_knowledge_listing_sees_a_database_through_one_namespace():
    checker = AccessChecker(["aihub.user.knowledge.hr.policies"], TENANT)

    assert checker.has_access_to_knowledge_database("hr")
    assert not checker.has_access_to_knowledge_database("engineering")


def test_namespace_routing_is_offered_only_what_the_user_may_read():
    checker = AccessChecker(["aihub.user.knowledge.hr.policies"], TENANT)

    readable = UserScopedRetrievers.readable_namespaces(checker, CATALOGUE)

    assert readable == {"hr": ["policies"]}
