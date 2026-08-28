---
title: Feature overview
---

# Feature overview

Through Open WebUI integration, the Swiss AI Hub provides a comprehensive feature set. This section documents key
capabilities available through the chat interface.

## Core chat capabilities

Messages stream in real-time as AI generates responses. Users can begin reading before generation completes rather than
waiting for complete responses.

The interface maintains conversation context across multiple turns. Users can ask follow-up questions or request
clarifications without re-establishing context.

Users can edit previous messages to refine queries, delete messages to remove irrelevant content, or regenerate
responses to explore alternative outputs.

The interface provides conversation categorization through tags, searchable history, and archiving. Users can maintain
organized libraries of interactions, finding and resuming previous conversations. Conversations can be deleted, shared
with others, or cloned to split off in different directions.

Full markdown rendering enables rich text formatting in both user messages and AI responses - headers, lists, tables,
code blocks with syntax highlighting. LaTeX support enables mathematical notation for technical and scientific
applications.

## Multi-modal interaction

Users can dictate messages rather than typing. Supported languages include English, German, and Swiss-German.

AI responses can be rendered as speech, supporting accessibility requirements and enabling audio-based consumption. This
benefits visually impaired users and scenarios where audio consumption is preferable.

Users can upload documents directly into conversations, asking questions about document content or requesting analysis.
The interface handles PDFs, Office documents, and text files.

For AI models supporting vision capabilities, users can include images in conversations, requesting analysis,
description, or processing.

## Model management

Users can interact with multiple AI models within the same interface, selecting models based on capability requirements,
cost considerations, or performance characteristics.

Advanced users can adjust model parameters - temperature for creativity control, token limits for response length,
presence penalties for repetition reduction.

Organizations can define their own "models" with custom system prompts added to base models, similar to GPTs in OpenAI.
All parameters can be preset, knowledge through RAG can be provided, and custom tools made for specific models. Users
select presets rather than configuring manually.

## Retrieval-augmented generation

Organizations can provide AI models with access to custom document collections called knowledge in Open WebUI. The
interface handles document upload, processing, and retrieval configuration.

When RAG capabilities are enabled, AI responses incorporate information from configured knowledge bases, providing
answers grounded in organizational knowledge rather than generic training data.

The native interface provides indicators when responses incorporate retrieved information. The Swiss AI Hub's enhanced
source attribution extends these capabilities as documented in the source attribution section.

Administrators can manage document collections and configure retrieval parameters through integrated management
interfaces.

## Collaboration and sharing

Users can share conversations with colleagues, enabling collaborative AI interaction. Shared conversations maintain full
context, allowing recipients to review history and continue conversations.

Users can annotate AI responses with feedback - marking responses as helpful or problematic, providing correction
guidance, or adding contextual notes.

For deployments enabling community interaction, users can participate in leaderboards recognizing productive usage,
share effective prompts or interaction patterns, and learn from colleagues' successful applications.

Multiple users can work within shared workspace environments, accessing common conversation histories, shared knowledge
bases, and collaborative interactions that support team-based work patterns.

## Administration and security

Administrators define user roles with granular permissions controlling access to specific models, features, or
administrative functions.

Administrative interfaces provide user provisioning, authentication configuration, and access revocation capabilities.
Integration with enterprise authentication systems - OAuth, LDAP - enables centralized user management.

For programmatic access, administrators can generate and manage API keys enabling external systems to interact with chat
capabilities. API key permissions can be scoped to specific models or operations.

Comprehensive logging captures user activities, model interactions, and administrative operations, creating audit trails
supporting compliance requirements and security monitoring.

## User experience

The interface adapts to different screen sizes and devices - desktop, tablet, mobile - maintaining functionality and
usability across form factors. Users can initiate conversations on desktop and continue them on mobile seamlessly.

The interface can install as a progressive web app, providing native application-like experiences including offline
capability, push notifications, and home screen presence without requiring app store distribution.

Users can select from multiple visual themes - light mode, dark mode, high-contrast options - matching interface
appearance to personal preferences and environmental lighting.

## Advanced capabilities

For supported models and configurations, the interface can execute code snippets, enabling interactive programming
assistance, computational problem solving, and algorithm prototyping within conversational contexts.

The same execution path lets models produce files — reports, spreadsheets, slide decks, charts, audio and video — which
appear in the Files panel for download. This needs no code from the user; see [File generation](../13_file_generation/)
for the supported formats and the recommended model.

Mermaid diagram support enables AI-generated visualizations - flowcharts, sequence diagrams, state machines - rendered
directly within conversations. This supports systems design, process documentation, and visual explanation.

The extensibility framework enables integration of custom processing pipelines, tools, and functions. Organizations can
extend chat functionality with business-specific operations without modifying core interface code.

When configured, AI models can access web search capabilities to incorporate current information beyond training data.
This supports queries requiring up-to-date information or verification against current sources.

## What this provides

Organizations deploying the Swiss AI Hub gain these Open WebUI capabilities immediately, without development investment.
As the Open WebUI community adds new features, the Swiss AI Hub benefits through standard update cycles.

Organizations gain mature functionality developed by global communities, extended with enterprise-specific capabilities
like source attribution and execution tracing.
