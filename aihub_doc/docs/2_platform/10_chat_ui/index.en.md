---
title: Chat Interface
---

# Chat interface

The Swiss AI Hub uses **Open WebUI** as its primary chat interface. Open WebUI is an open-source project with a
comprehensive feature set that includes document handling, user management, tools, voice interaction, and collaborative
features. Rather than building a custom chat interface, the platform integrates this existing solution and extends it
with custom capabilities.

## Why use an existing solution?

Building a production-grade chat interface requires significant development effort. Open WebUI already provides this
functionality with an active maintenance community. The Swiss AI Hub team can focus on capabilities specific to
enterprise AI deployment instead of recreating standard chat features.

As Open WebUI evolves, the Swiss AI Hub receives these improvements through regular updates. The platform benefits from
community-driven development, documentation, and deployment patterns without dedicating resources to maintaining basic
chat infrastructure.

## Custom extensions

The Swiss AI Hub extends Open WebUI's functionality in three main ways.

The interface embeds directly into the Swiss AI Hub suite rather than running as a separate application. Users access
chat capabilities through unified navigation without switching contexts or re-authenticating.

When AI responses draw from organizational knowledge bases, users can view the specific documents and passages that
informed the response. This source attribution enables verification of AI-generated content.

Custom tracing shows step-by-step agent execution, including reasoning chains, tool invocations, and decision points.
This visibility supports debugging and regulatory compliance requirements.

## Deployment considerations

Organizations using the Swiss AI Hub avoid the cost of building and maintaining a custom chat interface. Development
resources go toward enterprise-specific requirements rather than commodity functionality.

The open-source foundation provides flexibility. Organizations can fork or modify the chat interface if requirements
change. Platform viability doesn't depend on a single vendor's roadmap.

The existing production deployments and active community reduce technical risk compared to custom development.
Organizations deploy proven technology with established patterns.

## Documentation structure

This section covers the chat interface integration from several angles:

- [Integration architecture](11_integration_architecture/) explains how Open WebUI connects to the suite and handles
  communication
- [Source attribution](3_chat_with_your_data/) describes the custom extensions for knowledge retrieval visibility
- [Observability](10_observability/) covers execution tracing and workflow transparency
- [Feature overview](1_feature_overview/) catalogs the capabilities inherited from Open WebUI
- [Strategic rationale](12_strategic_rationale/) analyzes the decision to integrate an existing solution
