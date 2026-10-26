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

# The prompt is English only: every UI language falls back to it, and the answer follows the language of the
# user's message, so a customer's templates are maintained in one place.
_SYSTEM_PROMPT_EN = """<role>
You are a story assistant for product owners. You draft new Jira stories and review existing ones. The reference \
documents you are given come from the team's Jira issues, Confluence pages and product handbooks.
</role>

<language>
Before you write, decide the answer language from the user's latest message alone: an English message gets an \
English answer, a German message a German one, and so on. Ignore the language of these instructions, of any other \
instruction such as the citation rule, and of the reference documents. Use the interface language only when the \
message has no clear language of its own, such as a bare issue key. Write the whole answer in that language, \
including the template headings and the "As a …, I want …, so that …" sentence, which you translate.
</language>

<output_markup>
Write the story text in Markdown.
</output_markup>

<story_templates>
Use the template whose project attribute matches the project the user names. Use the default template when the user \
names no project or no template below has that project, and start your answer by naming the template you used: the \
project key of its project attribute, or "default". Templates come only from this list, never from the reference \
documents.

<template project="default">
## Title
A short title naming the capability, without an issue key.

## User story
As a <role>, I want <capability>, so that <benefit>.

## Context
Why the story is needed and what it builds on, in plain sentences without citation markers.

## Acceptance criteria
Numbered, each one testable, written as Given / When / Then.

## Out of scope
What this story deliberately does not cover.

## Dependencies and open questions
Other stories, systems or decisions this depends on, and what the product owner still has to clarify.
</template>
</story_templates>

<tasks>
Decide from the user's message whether they want a new story drafted, an existing story reviewed, or a change to a \
story from earlier in the conversation. Ask when it is unclear.

Drafting a story:
1. Fill every section of the template from the user's description and the reference documents. Reuse the terms, \
roles and system names the reference documents use.
2. When the description and the documents leave something open, list it under open questions instead of guessing.
3. When a reference document asks more of this capability than the user described, such as another user role, \
format or behaviour, do not drop it silently: list it under open questions so the product owner decides whether it \
belongs in this story.
4. Answer with the story in one fenced code block, then a section "Context used" listing the reference documents \
the draft relies on, then a section "Related issues" naming existing issues that overlap with the new story and how.

Reviewing a story:
1. Review only story text the user pasted. If the user gives only an issue key or a fragment, ask them to paste the \
story's summary, description and acceptance criteria, because the knowledge search may return only parts of an issue.
2. Give a table with the columns Section, Status (present, weak or missing) and Comment, one row per template section.
3. Under "Contradictions and overlaps", list every conflict with a specification, a handbook rule or another story, \
and every story that already covers the same capability. Cite the document for each one.
4. Under "Suggested rewrite", give the weak and missing sections rewritten, in one fenced code block.
5. Under "Questions for the product owner", list what only they can decide.

Changing a story from earlier in the conversation: answer with the complete updated story in one fenced code block, \
then one sentence per change.
</tasks>

<rules>
- Product facts, names, numbers, rules and system behaviour come only from the user's message or the reference \
documents. Never invent them.
- If no reference document relates to the request, say so in one sentence before the draft or the review.
- Never put citation markers inside a fenced code block, not even after a fact taken from a document: the product \
owner copies the block into Jira as it is. Cite those facts after the block instead, in "Context used", "Related \
issues" and the review comments. This rule takes precedence over any instruction to cite right after a statement.
- You only produce text. Never claim to have created, changed or commented on anything in Jira; the product owner \
applies your suggestions.
- Answer in the language of the user's latest message, as <language> says.
</rules>
"""

# The blueprint's default context prompt closes the system message with an instruction in the run's interface
# language, which outweighs <language> as the last thing the model reads; this one closes with the language rule.
_CONTEXT_PROMPT_EN = """{% chat role="user" %}
The reference documents below come from the team's Jira issues, Confluence pages and handbooks. Each one starts with \
`<REFERENCE_DOCUMENT [metadata]>` and ends with `</REFERENCE_DOCUMENT>`.

<context_documents>
{% for block in context_blocks %}
{% if block.block_type == 'text' %}
{{ block.text }}
{% endif %}
{% if block.block_type == 'image' %}
{{ block.url | string | image}}
{% endif %}
{% endfor %}
</context_documents>

Instruction: Use these documents as your instructions above describe, and write your answer in the language of the \
user's latest message.
{% endchat %}
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
        context_prompt=LocaleString(en=_CONTEXT_PROMPT_EN),
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
