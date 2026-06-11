# ruff: noqa: E402
"""
Regression test for the bug:
"RAG agent fails to answer an affirmative ('yes') reply to an offered follow-up."

Mechanism (see ticket): each chat turn is a NEW run with a fresh run_id in the SAME thread_id.
The follow-up turn's condensed query keys on the offer's wording (e.g. "SLA") while the document
that actually grounds the answer uses different words (e.g. "99.99% availability commitment"), so
the cold retrieval + reranker drop it. The grounding document is then absent from the context the
responder sees, and under a strict "answer only from retrieved context" system prompt the agent
cannot answer — even though it answered moments earlier.

The fix persists the prior turn's top grounding nodes in ThreadContext and merges them back into
the follow-up's CONTEXT at order_nodes_by_documents_step (post-rerank). This test drives two runs in
one thread against a tailored Milvus corpus and asserts that a `yes` to the offer still grounds its
answer on the original document — i.e. the grounding document reaches the combined context
(`InOrderNodeCombinerEvent.grounding_nodes`), not just the cold retrieval. The assertion targets the
`grounding_nodes` carried by the fix; without the fix the follow-up's context drops that document.

Requires the self-hosted infra the other RAG tests need (Milvus :19530 + LiteLLM with the
`embedding/bge-m3`, `reranker/*` and `text-generation/*` aliases). Run with:

    cd packages/agent
    uv run pytest swiss_ai_hub/agent/agents/rag_agent/tests/test_followup_affirmation.py -v -s
"""

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from datetime import datetime

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from swiss_ai_hub.core.events.agent import RetrieverEvent, StandaloneQuestionCondenserEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import EmbeddingModelConfig, LLMConfig, RerankingModelConfig
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig, create_mongo_document_store
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    INSERTED_AT,
    NAMESPACE,
    NODE_CONTENT,
    SOURCE,
    TYPE,
    UPDATED_AT,
)
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.testing.milvus_vector_store_content import drop_collection, fill_collection

from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.rag_agent.tests.test_rag_agent import build_rag_agent_config
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()

NAMESPACE_NAME = "ai_knowledge"
COLLECTION = "followup_affirmation_test"
GROUNDING_DOC_ID = "phoenix-deploy-arch"

# The first turn's answer (canned, so the condenser deterministically produces the follow-up).
# In production this is the agent's own prior reply. The offer's keyword ("service level
# agreement / SLA") deliberately differs from the words the grounding doc actually uses
# ("99.99% availability commitment") — modelling the real bug, where the doc that answers the
# follow-up is NOT the doc that owns the follow-up's keyword.
FIRST_QUESTION = "How is Acme Phoenix deployed and what reliability does it guarantee?"
FIRST_ANSWER_WITH_OFFER = (
    "Acme Phoenix runs a multi-region control plane with auto-scaling worker nodes, and every "
    "deployment is backed by a strong reliability commitment. Would you like to know more about "
    "the Acme Phoenix service level agreement (SLA)?"
)
AFFIRMATION = "yes"


def _node(doc_id: str, title: str, text: str) -> TextNode:
    now = datetime.now().timestamp()
    return TextNode(
        id_=doc_id,
        text=text,
        metadata={
            DOCUMENT_ID: doc_id,
            DOCUMENT_TITLE: title,
            SOURCE: NAMESPACE_NAME,
            NAMESPACE: NAMESPACE_NAME,
            TYPE: NODE_CONTENT,
            CREATED_AT: now,
            UPDATED_AT: now,
            INSERTED_AT: now,
        },
    )


# Phoenix cluster — wins the broad first question ("how is Phoenix deployed / what does it
# guarantee"). The grounding doc holds the ACTUAL answer to the follow-up (the 99.99% number)
# but expresses it as "availability commitment", deliberately NOT using the words "service level
# agreement" / "SLA" that the follow-up query will key on.
PHOENIX_NODES = [
    _node(
        GROUNDING_DOC_ID,
        "Acme Phoenix Deployment Architecture",
        "Acme Phoenix is deployed as a multi-region control plane with auto-scaling worker nodes "
        "and active-active failover. Operators run the Phoenix installer, configure the Phoenix "
        "control plane, and scale Phoenix worker pools per region. Every Acme Phoenix deployment is "
        "backed by a 99.99% availability commitment, with a 15-minute recovery time objective and "
        "automatic multi-region failover if a Phoenix region degrades.",
    ),
    _node(
        "phoenix-install",
        "Phoenix Installation",
        "Installing Acme Phoenix: download the Phoenix "
        "installer, provision the Phoenix control plane, and register Phoenix worker nodes.",
    ),
    _node(
        "phoenix-auth",
        "Phoenix Authentication",
        "Acme Phoenix authentication uses single sign-on. "
        "Phoenix supports OIDC and SAML for enterprise identity inside the Phoenix console.",
    ),
    _node(
        "phoenix-dashboard",
        "Phoenix Dashboard",
        "The Acme Phoenix dashboard visualizes platform "
        "health, Phoenix pipeline throughput, and Phoenix cluster status in real time.",
    ),
    _node(
        "phoenix-api",
        "Phoenix API",
        "The Acme Phoenix API lets developers manage Phoenix resources "
        "programmatically through the Phoenix SDK and Phoenix command line.",
    ),
]

# Decoys dense in "Acme Phoenix service level agreement (SLA)" keywords but WITHOUT the actual
# availability number — they own the follow-up's keyword lexically/semantically and crowd the
# grounding doc (which says "availability commitment", not "SLA") out of the top-k.
DECOY_NODES = [
    _node(
        "sla-template",
        "SLA Template",
        "Acme Phoenix service level agreement (SLA) template. This Acme "
        "Phoenix SLA template describes how to draft an Acme Phoenix service level agreement and fill in "
        "the Acme Phoenix SLA sections.",
    ),
    _node(
        "sla-legal",
        "SLA Legal Terms",
        "Legal terms of the Acme Phoenix service level agreement (SLA). "
        "The Acme Phoenix SLA legal clauses, Acme Phoenix SLA liability limits, and Acme Phoenix service "
        "level agreement governing law are defined here.",
    ),
    _node(
        "sla-glossary",
        "SLA Glossary",
        "Acme Phoenix service level agreement (SLA) glossary. Definitions "
        "of Acme Phoenix SLA terms used across the Acme Phoenix service level agreement and other Acme "
        "Phoenix SLA documents.",
    ),
    _node(
        "sla-penalties",
        "SLA Penalties",
        "Acme Phoenix service level agreement (SLA) penalty clauses. The "
        "Acme Phoenix SLA penalties and Acme Phoenix SLA service credits apply when an Acme Phoenix service "
        "level agreement target is missed.",
    ),
    _node(
        "sla-process",
        "SLA Review Process",
        "How to review the Acme Phoenix service level agreement (SLA). "
        "The Acme Phoenix SLA review process, Acme Phoenix SLA sign-off, and Acme Phoenix service level "
        "agreement renewal cadence.",
    ),
    _node(
        "sla-faq",
        "SLA FAQ",
        "Acme Phoenix service level agreement (SLA) FAQ. Common questions about the "
        "Acme Phoenix SLA, the Acme Phoenix service level agreement scope, and Acme Phoenix SLA support.",
    ),
]

ALL_NODES = PHOENIX_NODES + DECOY_NODES


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def seeded_corpus(event_loop):
    """Seed the tailored corpus synchronously (fill_collection drives its own loop, so it must
    run OUTSIDE the @async_test asyncio.run to avoid a nested-loop RuntimeError)."""
    asyncio.set_event_loop(event_loop)
    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store = MilvusVectorStoreConfig(uri="http://localhost", collection_name=COLLECTION, dimensions=1024)
    doc_store = create_mongo_document_store(document_store_name=COLLECTION)
    drop_collection(collection_name=COLLECTION)
    fill_collection(embedding_config, vector_store, doc_store, nodes=ALL_NODES)
    yield
    drop_collection(collection_name=COLLECTION)


def _build_config():
    return build_rag_agent_config(
        llm_config=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        reranking_config=RerankingModelConfig(model_name="reranker/bge"),
        embedding_config=EmbeddingModelConfig(model_name="embedding/bge-m3"),
        vector_store=MilvusVectorStoreConfig(
            collection_name=COLLECTION, index_namespaces=[NAMESPACE_NAME], dimensions=1024
        ),
        query_mode=VectorStoreQueryMode.HYBRID,
    )


async def _run_turn(thread_id: str, messages: list[ChatMessage]) -> tuple[set[str], set[str], str]:
    """Run one RAG turn (one run_id) in the given thread.

    Returns (cold-retrieval doc-ids, grounding-context doc-ids, condensed query). The grounding-context
    set is the combined context the answer is built on (fresh retrieval + carried prior-turn nodes).
    """
    runner = AgentTestRunner(agent_type=RAGAgent, agent_config=_build_config())
    async with runner.test_run(delay_before_stop=120, thread_id=thread_id) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(messages=messages, user=fake_user(), locale="en"),
        )
    retriever_event: RetrieverEvent = runner.get_events_of_class(RetrieverEvent)[-1]
    retrieved_doc_ids = {node.document_id for node in (retriever_event.nodes or [])}
    combiner_event: InOrderNodeCombinerEvent = runner.get_events_of_class(InOrderNodeCombinerEvent)[-1]
    grounding_doc_ids = {node.document_id for node in (combiner_event.grounding_nodes or [])}
    condensed = runner.get_events_of_class(StandaloneQuestionCondenserEvent)[-1].condensed_chat_message.content
    return retrieved_doc_ids, grounding_doc_ids, condensed


@pytest.mark.usefixtures("seeded_corpus")
@async_test
async def test_followup_affirmation_retrieves_grounding_document():
    # Fresh thread id per execution so prior runs' persisted ThreadContext can't leak in.
    thread_id = f"followup-repro-thread-{ObjectId()}"

    # Turn 1 — original broad question (run R1).
    turn1_retrieved, turn1_grounding, _ = await _run_turn(
        thread_id, [ChatMessage(role=MessageRole.USER, content=FIRST_QUESTION)]
    )
    print(f"\n[turn 1] retrieved docs: {sorted(turn1_retrieved)} | grounding docs: {sorted(turn1_grounding)}")

    # Turn 2 — affirmation to the offered follow-up (run R2, SAME thread).
    turn2_retrieved, turn2_grounding, condensed = await _run_turn(
        thread_id,
        [
            ChatMessage(role=MessageRole.USER, content=FIRST_QUESTION),
            ChatMessage(role=MessageRole.ASSISTANT, content=FIRST_ANSWER_WITH_OFFER),
            ChatMessage(role=MessageRole.USER, content=AFFIRMATION),
        ],
    )
    print(f"[turn 2] condensed question: {condensed!r}")
    print(f"[turn 2] retrieved docs: {sorted(turn2_retrieved)} | grounding docs: {sorted(turn2_grounding)}")

    # The doc that grounded the offer was retrievable on turn 1 ...
    assert GROUNDING_DOC_ID in turn1_retrieved, (
        f"Test corpus misconfigured: '{GROUNDING_DOC_ID}' should be retrieved for the original "
        f"question. Got {sorted(turn1_retrieved)}."
    )
    # ... the cold retrieval on the 'yes' turn drops it (the bug the fix works around) ...
    # ... but the fix carries it into the follow-up's grounding context (AC #1).
    assert GROUNDING_DOC_ID in turn2_grounding, (
        f"BUG: the affirmation's grounding context {sorted(turn2_grounding)} dropped the grounding "
        f"document '{GROUNDING_DOC_ID}' that the agent's follow-up offer was based on. "
        f"(cold retrieval this turn: {sorted(turn2_retrieved)})"
    )
