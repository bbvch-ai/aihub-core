"""A Jira issue's status or a Confluence page's space is a field of the synced record, not text of its body. RAG must
carry those fields from retrieval to the documents the model reads, or it answers that the document does not say
(aihub-core-private#362)."""

from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.generative_ai import IngestedNode
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.rag_agent.events.context_insufficient_with_query_event import (
    ContextInsufficientWithQueryEvent,
)
from swiss_ai_hub.agent.rag.step_functions import do_order_nodes_by_documents, do_retrieve

MODULE = "swiss_ai_hub.agent.rag.step_functions"

ISSUE = IngestedNode(
    id="eng-2-description",
    content="Upload a DOCX with a merged-cell table.",
    document_id="eng-2",
    source="s3://jira/ENG/ENG-2.md",
    namespace="ENG",
    document_title="ENG-2: Pipeline drops tables with merged cells",
    type="content",
    content_type="text",
    created_at="2026-10-08T03:12:55Z",
    updated_at="2026-10-19T06:10:43Z",
    inserted_at="2026-10-19T06:12:29Z",
    score=0.8,
    metadata={},
    record_fields={"issue_type": "Bug", "project": "ENG", "status": "To Do", "labels": ["backend", "urgent"]},
)


@pytest.mark.asyncio
async def test_a_retrieved_issue_reaches_the_prompt_with_its_fields():
    retry = ContextInsufficientWithQueryEvent(reason="retry", new_query="What is the status of ENG-2?")
    with patch(f"{MODULE}.retrieve_from_all_sources", AsyncMock(return_value=[ISSUE])):
        retrieved = await do_retrieve(retry, [], LocaleHandler(locale="en"), None)

    combined = await do_order_nodes_by_documents(retrieved, LocaleHandler(locale="en"), None, AsyncMock())

    assert retrieved.nodes == [ISSUE]
    prompt = combined.context_message.blocks[0].text
    assert "issue_type='Bug' project='ENG' status='To Do' labels='backend, urgent'>" in prompt
    assert "language=" not in prompt
