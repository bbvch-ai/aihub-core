---
title: System Context
description: C4 Level 1 — people and external systems that interact with Swiss AI Hub.
---

# System Context

The system context view answers the broadest question: who interacts with Swiss AI Hub, and what external systems does
it integrate with? It is C4 Level 1 — the platform appears as a single box, with no internal detail. The point is to
draw a clean boundary: everyone and everything that *talks to* the platform appears here; everything *inside* it is
deferred to the [Containers](../2_containers/) view.

Read it as two rings around the central system. Above are the **people** who use the platform, each in a distinct role
with a distinct surface. Around the edges are the **external system categories** the platform integrates with — and a
key idea of Swiss AI Hub is that these are *pluggable capabilities*, not fixed vendor choices. The platform ships
preconfigured with sensible defaults but federates, routes, or adapts to whatever conforming implementation a customer
brings.

<likec4-view view-id="index" style="display:block;height:600px"></likec4-view>

## Actors

- **Enterprise User** — Any tenant member. Covers both regular users and tenant administrators, who share the same
  surface (Admin UI + OpenWebUI + Main API) with feature visibility gated by tenant-scoped roles.
- **System Administrator** — Cross-tenant platform admin. Holds the `AIHubSysAdmin` realm role; uses the separate
  sysadmin plane (`sysadmin.${DOMAIN}`) to manage tenants, user-tenant assignments, and platform-level configuration.
- **Collaboration Channel User** — Subset of tenant users who interact with Swiss AI Hub agents from collaboration
  channels (Slack, Teams, Webex, email) rather than the dedicated web UI.
- **Platform Operator** — Platform DevOps / SRE engineer. Holds the `AIHubDeveloper` realm role; consumes observability
  and operational surfaces (Dagster, Langfuse, Attu, Backup, SeaweedFS Filer).

## External integrations

Each external box represents a *pluggable integration capability*, not a specific vendor. The platform ships
preconfigured for the examples listed but supports any conforming implementation through its respective gateway /
adapter:

- **Identity Provider** — Federated into our Keycloak realm via OIDC/SAML. Examples: Entra ID, Okta, on-prem LDAP/AD,
  Google, GitHub.
- **LLM Provider** — Configured per-deployment in the internal LiteLLM gateway. All tenants in a deployment share the
  same model roster. Examples: Swiss LLM Cloud, OpenAI, Anthropic, Azure OpenAI, Gemini.
- **Document Source** — Synced via Rclone (70+ supported backends) or direct integration. Examples: SharePoint (direct
  MS Graph), OneDrive, Google Drive, Azure Blob, S3, Dropbox.
- **Collaboration Platform** — Routed via the Microsoft Agents SDK. Examples: Slack, Microsoft Teams, Webex, email.
- **Observability Sink** — Customer-managed trace/log receiver via OTEL exporter. Examples: SigNoz, Grafana Cloud,
  Honeycomb.
- **Notification Target** — One-way alert destination via Apprise (80+ supported targets). Examples: Slack channels,
  Discord webhooks, email, PagerDuty.
- **External MCP Tools** — Customer-exposed MCP servers consumed by agents as tools. Examples: domain-specific APIs,
  internal CRMs, ticketing systems.

For deeper integration mechanics, see the [Container view](../2_containers/) where each external category maps to
specific containers that bridge it.
