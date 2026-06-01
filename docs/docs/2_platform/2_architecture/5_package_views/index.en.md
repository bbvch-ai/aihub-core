---
title: Package-Centered Views
description: Developer-onboarding architecture views — one per first-party package, centered on its direct neighbours.
---

# Package-Centered Views

For developers about to work on a specific package, each view here centres on one container and shows its direct L2
neighbours (inbound + outbound) plus any L1 externals it talks to. Each diagram answers:

> *"If I work on package X, what L2 surface will I touch?"*

These views are intentionally separate from the [Code Deep Dive](../../../6_code_deep_dive/) section, which mirrors each
package's `README.md` (the end-user view that also appears on PyPI / npm). The diagrams here serve a different audience
— engineers building **inside** the platform.

For the layered architecture story (what's in the Data tier, what's in the LLM tier, etc.) see
[Containers](../2_containers/).

## API Gateway

The API is the most-connected first-party container; its view is split into outbound (what it calls) and inbound (who
calls it) for legibility.

### Outbound — what the API calls

<likec4-view view-id="centered_api_outbound" style="display:block;height:560px"></likec4-view>

### Inbound — who calls the API

<likec4-view view-id="centered_api_inbound" style="display:block;height:480px"></likec4-view>

## Sysadmin API

Narrower surface than the main API: tenant lifecycle, Keycloak admin, OpenWebUI provisioning.

<likec4-view view-id="centered_sysadmin_api" style="display:block;height:480px"></likec4-view>

## Admin UI

Frontend developer onboarding view. Nuxt 3 SPA hitting the API via the generated TypeScript SDK and Keycloak for OIDC.

<likec4-view view-id="centered_web" style="display:block;height:480px"></likec4-view>

## Sysadmin UI

Nuxt Layer on top of Admin UI. Same-origin to Sysadmin API; the cross-origin call only exists for the non-sysadmin user
bounce-out.

<likec4-view view-id="centered_sysadmin_web" style="display:block;height:480px"></likec4-view>

## Agent Runtime

Long-running NATS subscriber executing agent workflows step-by-step. Touches RAG (Milvus), memory (Neo4j), LLM gateway
(LiteLLM), and external MCP tools.

<likec4-view view-id="centered_agent" style="display:block;height:560px"></likec4-view>

## Pipeline Orchestrator

Document ingestion + RAG embedding via Dagster. Reaches out to document sources (Rclone backends + direct MS Graph for
SharePoint), MinerU for parsing, LiteLLM for embeddings, Milvus for vector storage.

<likec4-view view-id="centered_pipeline" style="display:block;height:560px"></likec4-view>

## Bot Service

Multi-channel collaboration bot. NATS bridges for agent chat + BITL, direct Slack/Teams API calls for content
extraction, per-message Keycloak lookup, LiteLLM direct path for non-agent LLM completions.

<likec4-view view-id="centered_bot" style="display:block;height:560px"></likec4-view>

## Backup Service

Scheduled backup/restore/maintenance of stateful stores. Talks to every backed-up store (Postgres, FerretDB, Milvus,
Neo4j, Valkey, ClickHouse, NATS) plus SeaweedFS as the backup destination and the Docker socket for container lifecycle
control.

<likec4-view view-id="centered_backup" style="display:block;height:560px"></likec4-view>

## OpenWebUI

The custom `aihub-pipeline` bridges OpenWebUI chat to the Swiss AI Agent Protocol via SSE — distinct from the
OpenAI-compat fallback path used for non-chat (image, speech, embeddings). Also calls Milvus directly for OpenWebUI's
own RAG feature.

<likec4-view view-id="centered_openwebui" style="display:block;height:560px"></likec4-view>
