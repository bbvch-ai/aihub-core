from llama_index.core.vector_stores.types import VectorStoreQueryMode
from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    KnowledgeRetrieverConfig,
    LLMConfig,
    LLMParameter,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)

_SYSTEM_PROMPT_EN = """<role>
You are a story assistant for product owners. You draft new Jira stories and review existing ones. The reference \
documents you are given come from the team's Jira issues, Confluence pages and product handbooks.
</role>

<story_templates>
Use the template of the project the user names. Use the default template when no project is named or the project \
has no template of its own, and say which template you used.

<template project="default">
## Title
A short title naming the capability, without an issue key.

## User story
As a <role>, I want <capability>, so that <benefit>.

## Context
Why the story is needed and what it builds on.

## Acceptance criteria
Numbered, each one testable, written as Given / When / Then.

## Out of scope
What this story deliberately does not cover.

## Dependencies and open questions
Other stories, systems or decisions this depends on, and what the product owner still has to clarify.
</template>
</story_templates>

<tasks>
Decide from the user's message whether they want a new story drafted or an existing story reviewed. Ask when it is \
unclear.

Drafting:
1. Fill every section of the template from the user's description and the reference documents.
2. Reuse the terms, roles and system names the reference documents use.
3. When the description and the documents leave something open, list it under open questions instead of guessing.
4. After the story, add a section "Context used" listing the reference documents the draft relies on, and a \
section "Related issues" naming existing issues that overlap with the new story.

Reviewing:
1. Check the story against its template section by section. Give a table with the columns Section, Status \
(present, weak or missing) and Comment.
2. List contradictions and overlaps with the reference documents: other stories, specifications, handbook rules. \
Name the document for each one.
3. Suggest concrete rewrites for weak or missing sections, and the questions the product owner should clarify.
</tasks>

<rules>
- Product facts, names, numbers, rules and system behaviour come only from the user's message or the reference \
documents. Never invent them.
- If no reference document relates to the request, say so in one sentence before the draft or the review.
- Keep citation markers out of the story text itself. Put them in "Context used" and in the review comments.
- You only produce text. Never claim to have created, changed or commented on anything in Jira; the product owner \
applies your suggestions.
- Answer in the language of the user's message.
</rules>
"""


def build() -> RAGAgentConfig:
    settings = AIHubSettings()
    return RAGAgentConfig(
        agent_id="jira-story-assistant",
        name=LocaleString(
            en="Jira Story Assistant",
            de="Jira-Story-Assistent",
            fr="Assistant de stories Jira",
            it="Assistente per storie Jira",
        ),
        description=LocaleString(
            en=(
                "Drafts Jira stories from a short description and reviews existing ones for completeness and "
                "contradictions, grounded in your Jira, Confluence and handbook knowledge."
            ),
            de=(
                "Entwirft Jira-Stories aus einer kurzen Beschreibung und prüft bestehende auf Vollständigkeit und "
                "Widersprüche, gestützt auf Ihr Wissen aus Jira, Confluence und Handbüchern."
            ),
            fr=(
                "Rédige des stories Jira à partir d'une courte description et vérifie les stories existantes "
                "(complétude, contradictions) à partir de vos connaissances Jira, Confluence et manuels."
            ),
            it=(
                "Redige storie Jira da una breve descrizione e verifica quelle esistenti (completezza, "
                "contraddizioni) basandosi sulle vostre conoscenze in Jira, Confluence e nei manuali."
            ),
        ),
        icon="mage:edit",
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.3, timeout=120.0),
        ),
        number_of_input_tokens=128000,
        system_prompt=LocaleString(en=_SYSTEM_PROMPT_EN),
        # Drafting has no document that answers it, and a rejecting guard withholds every retrieved document.
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=False),
        # A stand-in: a template may only name a collection every deployment seeds, so the admin swaps in the
        # Jira, Confluence and handbook databases after creating the profile.
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
                vector_store=MilvusVectorStoreConfig(
                    collection_name=settings.SHARED_BUCKET_NAME,
                    index_namespaces=[settings.SHARED_NAMESPACE_NAME],
                ),
                retrieve_k=5,
                # Keyword matching finds overlapping stories and the team's working agreements, which a draft
                # request phrased as an instruction misses on vector similarity alone.
                query_mode=VectorStoreQueryMode.HYBRID,
                node_types=["content"],
            ),
        ],
        # Set explicitly: the class default (off) would override the form's checkbox when the template prefills it.
        restrict_to_user_access=True,
        # Memories of earlier drafts would leak facts into an unrelated story.
        user_memory=UserMemoryConfig(
            enable_user_memory_retrieval=False,
            enable_user_memory_storage=False,
        ),
        org_memory=None,
    )
