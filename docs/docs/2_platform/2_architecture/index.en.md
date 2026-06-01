---
title: Platform Architecture
description: Technical architecture of the Swiss AI Hub platform — C4 model, communication protocol, network isolation, runtime scenarios, and deployment topology.
---

# Platform Architecture

This section documents the technical architecture of Swiss AI Hub. The content here is a deep dive — for the
marketing-level platform overview, see [Core Components](../../1_vision_and_positioning/3_core_components/) and
[Infrastructure Layers](../../1_vision_and_positioning/4_infrastructure_layers/) under Vision & Positioning.

The architecture is modelled with [LikeC4](https://likec4.dev), rendered as interactive diagrams via web components.
Source files live in `docs/likec4/` and are regenerated automatically by the docs dev server. Use the C4 hierarchy to
navigate:

- **[System Context](./1_system_context/)** — L1: people and external systems that interact with Swiss AI Hub
- **[Containers](./2_containers/)** — L2: the platform's first-party packages, infrastructure, and how they connect;
  includes tier breakdowns
- **[Swiss AI Agent Protocol](./3_swiss_ai_agent_protocol/)** — Control / Display event model over NATS
- **[Network Isolation](./4_network_isolation/)** — Docker network zones and traffic policy

Coming soon as the LikeC4 model expands:

- **Runtime Scenarios** — dynamic views of chat streaming, document ingestion, bot-in-the-loop, agent discovery
- **Deployment Topology** — prod deployment with per-class agent instances, OIDC middleware, host-network OpenWebUI
- **Component Internals** — L3 component views for each first-party package (these will live on the per-package pages
  under [Code Deep Dive](../../6_code_deep_dive/))

@joelbarmettlerUZH @mhoegger
