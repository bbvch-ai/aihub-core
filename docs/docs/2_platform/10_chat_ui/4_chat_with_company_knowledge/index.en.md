---
title: Chat with your company knowledge
---

# Chat with your company knowledge

The Swiss AI Hub shows users which knowledge documents and passages informed AI responses. This transparency helps users
verify accuracy and understand the basis for AI conclusions.

## Why this matters

When AI systems use Retrieval-Augmented Generation (RAG) with organizational knowledge bases, users need to verify where
information comes from. Standard chat interfaces, including native Open WebUI, don't systematically show which documents
or passages informed responses.

Regulated industries and quality-critical domains require evidence chains for AI-generated content. Decision-makers need
to verify that responses align with authoritative sources and current policies. Without source attribution, verification
requires manual research.

Organizations maintaining knowledge bases need feedback on retrieval quality. Source attribution shows whether agents
access appropriate documents and reveals knowledge gaps for common queries.

## How it works

A custom source display panel activates when AI responses reference organizational knowledge. The interface provides a
control for viewing sources without leaving the conversation.

Activating source display opens an adjacent panel. Users see their conversation on one side and source details on the
other, enabling simultaneous review of responses and supporting materials.

Sources organize by document. For each document, users see metadata - database location, namespace, title - followed by
specific passages that contributed to the response.

The system shows specific passages (nodes) retrieved and provided to the AI. Users see exact text chunks, their context
within source documents, and relevance scores.

## Interactive exploration

Source entries link directly to full documents within the knowledge management service. Users can click through from a
retrieved passage to view the complete document.

Each passage includes surrounding context like heading hierarchies and document structure. This helps users understand
where the passage sits within its source.

The display differentiates between sources used in response generation and sources retrieved but not selected. A toggle
controls this distinction. This helps users understand the AI's source selection.

Repeated interactions reveal which documents address specific topics, where knowledge gaps exist, and how information
organizes.

## Technical implementation

During agent execution, the platform captures retrieval events documenting which documents and nodes were accessed.
These events include identifiers linking content to specific documents in knowledge management systems. When users
request source display, the platform queries these events to construct the view.

Source display coordinates data from thread management (conversation context), event tracking (retrieval records), and
knowledge management (document details). The architecture maintains service boundaries while enabling this coordination.

Source data loads on-demand when users request visibility rather than preloading for every message. Users get immediate
access when requested. The system doesn't load source data for conversations where users don't need verification.

When retrieval accesses numerous sources, the display prioritizes the most relevant content. Sources directly
contributing to responses appear first. Lower-relevance or unused sources are available through expanded views or
filters.

## What this provides

When users can verify AI responses against authoritative sources, trust increases. Verification addresses the "black
box" concern.

For regulated industries, source attribution provides evidence chains for AI-assisted decisions. Compliance audits can
trace recommendations to approved materials.

Knowledge managers validate retrieval quality through source attribution. Consistently irrelevant sources or knowledge
gaps guide improvement - adding documents, refining organization, or adjusting retrieval parameters.

Users learn how knowledge bases organize and what information exists. This reduces dependency on AI as users develop
direct knowledge of organizational resources.

For high-stakes decisions - regulatory compliance, financial commitments, operational changes - users can verify AI
suggestions before acting.

## Knowledge management feedback

When users examine sources and find irrelevant content, this feeds back into retrieval system tuning. Patterns of source
examination followed by revised queries indicate quality issues.

When conversations reveal no appropriate sources for common queries, this signals knowledge base gaps. Organizations
prioritize document acquisition based on these signals.

Source attribution generates usage data showing which documents AI systems reference most frequently. This informs
curation priorities. Frequently accessed documents need careful maintenance. Unused documents may indicate organization
issues.

When source attribution shows responses drawing on outdated versions, organizations receive signals to update knowledge
bases.
