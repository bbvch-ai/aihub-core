---
title: Containers
description: C4 Level 2 — first-party application containers plus the central infrastructure they connect through.
---

# Containers

The container view zooms into the Swiss AI Hub system box from [System Context](../1_system_context/). It shows the
platform's first-party application containers (the packages we build) plus the central infrastructure they share.

## Overview

This headline view shows the 9 first-party application containers + the NATS event spine. Infrastructure tiers (Data,
LLM, Identity, Observability, Utility) appear on their own focused views below.

<likec4-view view-id="containers_overview" style="display:block;height:600px"></likec4-view>

## Application tier

First-party packages plus OpenWebUI. NATS and shared infrastructure are visible in their own tier views — this view
focuses purely on how application containers reach each other.

<likec4-view view-id="tier_application" style="display:block;height:560px"></likec4-view>

## LLM / AI Inference tier

All upstream model calls funnel through the LiteLLM gateway, with Presidio handling PII redaction en route to external
providers.

<likec4-view view-id="tier_llm" style="display:block;height:480px"></likec4-view>

## Data tier

Stateful stores and their internal dependencies (Milvus→etcd, SeaweedFS→etcd, FerretDB→its backing Postgres,
ClickHouse→S3).

<likec4-view view-id="tier_data" style="display:block;height:520px"></likec4-view>

## Eventing tier

NATS / JetStream is the spine of the platform. The protocol distinction (Control vs Display) is documented in
[Swiss AI Agent Protocol](../3_swiss_ai_agent_protocol/).

<likec4-view view-id="tier_eventing" style="display:block;height:480px"></likec4-view>

## Identity & Edge tier

Traefik fronts everything; oauth2-proxy gates operator UIs; Keycloak federates customer identity providers. Gated
containers and OIDC-protected apps appear in their own tier views — this view focuses on the edge infrastructure itself.

<likec4-view view-id="tier_identity_edge" style="display:block;height:440px"></likec4-view>

## Observability tier

OTEL Collector aggregates traces and logs from every application container, forwarding to Langfuse by default and
optionally exporting to customer-managed sinks.

<likec4-view view-id="tier_observability" style="display:block;height:440px"></likec4-view>

## Utility tier

Auxiliary services consumed mostly by OpenWebUI and operators.

<likec4-view view-id="tier_utility" style="display:block;height:420px"></likec4-view>

## Package-centered views (for developer onboarding)

Each first-party package also has a **centered view** showing its direct neighbours — what it talks to and what talks to
it. These live on the per-package pages under [Code Deep Dive](../../../6_code_deep_dive/) and answer the question: *"If
I work on package X, what L2 surface will I touch?"*
