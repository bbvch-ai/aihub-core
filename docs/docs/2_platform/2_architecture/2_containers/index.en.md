---
title: Containers
description: C4 Level 2 — first-party application containers plus the central infrastructure they connect through, organized by tier.
---

# Containers

The container view zooms into the Swiss AI Hub box from [System Context](../1_system_context/) and shows what's inside.
In C4 terminology a *container* is a separately deployable, independently runnable unit — an application process, a
database, a message broker — not necessarily a Docker container (though here they usually map one-to-one).

Swiss AI Hub runs roughly 33 containers in production. Showing all of them on one diagram would be unreadable, so this
page is organized in two layers: a **headline overview** of just the parts a developer thinks about daily, followed by
**focused tier views** that each zoom into one functional layer of the platform. Pick the view that matches the question
you're asking.

::: tip
Click any diagram to open the interactive viewer — you can pan, zoom, follow relationships, and jump between views.
:::

## Overview

This headline view shows the nine first-party application containers — the packages we build — plus the NATS event bus
that connects them. It deliberately omits the supporting infrastructure (databases, gateways, observability) so the
application topology stands out: who talks to whom, and how the event spine ties the backend services together.

If you're new to the platform, start here. It's the mental model to hang everything else on.

<likec4-view view-id="containers_overview" style="display:block;height:600px"></likec4-view>

## Application tier

The first-party packages plus OpenWebUI — everything with custom application logic. This is the tier most contributors
work in. The view focuses purely on how application containers reach each other; the infrastructure they all depend on
(databases, LLM gateway, identity) lives in the tiers below to keep this diagram legible.

Note that the Agent Runtime appears as a single logical box here but is deployed as one container *per agent class* in
production. The Process Engine is not a container at all — it runs embedded inside the API Gateway.

<likec4-view view-id="tier_application" style="display:block;height:560px"></likec4-view>

## LLM / AI Inference tier

Every model call in the platform — chat, embeddings, reranking, speech, OCR — funnels through the **LiteLLM gateway**.
This single chokepoint is what makes the platform model-agnostic: switching from Swiss LLM Cloud to OpenAI to a local
GPU model is a configuration change in LiteLLM, not a code change anywhere else. Presidio sits in the path to redact PII
before requests reach external providers, and MinerU, vLLM, and Speaches provide local parsing, GPU inference, and
speech respectively.

<likec4-view view-id="tier_llm" style="display:block;height:480px"></likec4-view>

## Data tier

The platform's stateful stores, each chosen for a specific job: PostgreSQL for relational data, FerretDB for documents,
Valkey for ephemeral agent state, Neo4j for graph-based memory, Milvus for vectors, ClickHouse for analytics, and
SeaweedFS for S3-compatible object storage. The view also shows their internal dependencies — Milvus and SeaweedFS both
use etcd for metadata, FerretDB runs on its own backing Postgres, and ClickHouse offloads to S3 — which is why "the
database tier" is more interconnected than it first appears.

<likec4-view view-id="tier_data" style="display:block;height:520px"></likec4-view>

## Eventing tier

NATS / JetStream is the spine of the platform — the single box that nearly every application container publishes to or
subscribes from. The Swiss AI Agent Protocol runs over it, distinguishing durable **Control Events** (workflow state, on
JetStream) from ephemeral **Display Events** (observability, on NATS Core). This separation is what lets the chat UI
visualize an agent's reasoning in real time without interfering with the agent's actual execution. The protocol itself
is documented in [Swiss AI Agent Protocol](../3_swiss_ai_agent_protocol/).

<likec4-view view-id="tier_eventing" style="display:block;height:480px"></likec4-view>

## Identity & Edge tier

Everything at the network boundary. Traefik is the single ingress point, terminating TLS and routing every `*.${DOMAIN}`
subdomain to the right service. Keycloak is the identity broker that federates customer identity providers and issues
the platform's OIDC tokens and realm roles. A set of oauth2-proxy instances forms a uniform OIDC gate in front of the
operator UIs (Dagster, Backup, Attu, SeaweedFS Filer), and pgbouncer pools database connections for Dagster. The
application containers these front are shown in their own tiers — this view is about the edge machinery itself.

<likec4-view view-id="tier_identity_edge" style="display:block;height:440px"></likec4-view>

## Observability tier

The OTEL Collector aggregates OpenTelemetry traces and logs from every application container and forwards them to
Langfuse, which adds AI-specific observability on top — full prompt/response capture, per-trace cost tracking, and RAG
retrieval tracing. By default everything stays inside the deployment; the collector can also be configured to export to
a customer-managed sink (SigNoz, Grafana Cloud, Honeycomb). Langfuse's own data dependencies (ClickHouse, Postgres,
Valkey, SeaweedFS) belong to the Data tier.

<likec4-view view-id="tier_observability" style="display:block;height:440px"></likec4-view>

## Utility tier

Auxiliary services that support the application tier without being core to it: SearXNG for web search, Jupyter as a
code-execution sandbox, Playwright for browser automation, and Attu as a Milvus admin console for operators. These are
consumed mostly by OpenWebUI (as agent tools) and by operators.

<likec4-view view-id="tier_utility" style="display:block;height:420px"></likec4-view>

## Package-centered views

The tier views above slice the platform horizontally — by functional layer. The
[Package-Centered Views](../5_package_views/) slice it the other way: one diagram per first-party package, centered on
that package with all its neighbours, for developers about to work inside a specific package.

@joelbarmettlerUZH @mhoegger
