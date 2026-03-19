---
title: External system integrations
---

# External system integrations

The Swiss AI Hub connects with external systems through four integration patterns.

## Integration approaches

### 1. Direct agent API calls

Agents can call external APIs (REST, SOAP, GraphQL, etc.) directly from their workflow steps using standard Python HTTP
libraries like `httpx` or `aiohttp`. During execution, agents make API calls as part of their logic, process responses,
and incorporate the results into their outputs.

This works well for simple, single-operation API calls within agent workflows. An agent might retrieve customer data
from a CRM during conversation, submit form data to an external portal after user approval, or query a ticketing system
to answer questions. The [Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) has
implementation patterns and examples.

### 2. Platform API integration (external systems calling in)

External systems can trigger Swiss AI Hub agents through the
[Agent Interaction REST API](../18_api/2_agent_interaction_api/). The API authenticates incoming HTTP requests,
translates them into internal events, and streams agent responses back as structured results.

This approach fits bidirectional integrations where external systems need to trigger AI capabilities. A document portal
might trigger AI classification when files are uploaded, a web application might request AI-generated summaries for its
dashboard, or an external workflow system could delegate analysis tasks to AI agents.

### 3. Data pipeline integration (batch synchronization)

[Data Pipelines](../6_pipelines/) continuously synchronize data from external systems into Swiss AI Hub knowledge bases.
Dagster pipelines connect to external data sources, extract and transform the data, then load it into Swiss AI Hub where
it's indexed for RAG (Retrieval-Augmented Generation). Pipelines can run on schedules or be triggered by events.

This handles read-heavy integrations where AI primarily analyzes external data, large-scale document indexing, or
scheduled data synchronization from enterprise systems. You might sync SharePoint documents nightly into a knowledge
base, continuously ingest support tickets for trend analysis, or import product catalogs on a schedule for customer
service agents.

### 4. MCP integration (development tools)

[Model Context Protocol (MCP)](../19_mcp/) lets AI coding assistants like Claude Code, Gemini CLI, and Cursor interact
with Swiss AI Hub during development. This provides read-only observation of platform state for development and
debugging workflows.

## Choosing the right approach

| Approach                  | Latency   | Direction     | Complexity  | Best for                               |
| ------------------------- | --------- | ------------- | ----------- | -------------------------------------- |
| Direct agent API calls    | Real-time | Outbound      | Low         | Simple API calls within agent logic    |
| Platform API integration  | Real-time | Inbound       | Medium      | External systems triggering AI         |
| Data pipeline integration | Batch     | Inbound       | Medium-High | Large-scale data sync, knowledge bases |
| MCP integration           | Real-time | Bidirectional | Low         | Development tools only                 |

## Network and security considerations

### Outbound connectivity (for direct agent API calls and pipelines)

The Swiss AI Hub VM needs outbound HTTPS (port 443) access to external systems. Configure firewall rules to allow
outbound connections to specific endpoints. The platform supports API keys, OAuth tokens, and certificate-based
authentication. All external connections use encrypted HTTPS.

[Network Requirements](../3_deployment_guide/7_network_requirements/) has more details.

### Inbound connectivity (for platform API integration)

External systems connect to Swiss AI Hub using standard HTTPS (port 443). Authentication options include OAuth 2.0, API
keys, or Azure AD integration. Traefik reverse proxy provides built-in rate limiting protection, and Let's Encrypt
handles automatic certificate management for TLS termination.

[Network Security](../20_security/4_network_security/) covers the security architecture.

## General integration principles

Match your integration approach to latency, volume, and direction requirements. Deploy Swiss AI Hub in Switzerland if
you need Swiss data residency. Use TLS encryption, RBAC, and comprehensive audit logging. Leverage enterprise SSO
through OAuth 2.0, SAML, or Azure AD. Configure proper firewall rules for inbound and outbound connectivity. Follow
[Swiss Data Protection](../21_compliance/3_dsg/) guidelines.

## Related documentation

- Agents: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) - Implementing direct
  API calls
- API: [Agent Interaction REST API](../18_api/2_agent_interaction_api/) - Platform HTTP interface
- Pipelines: [Data Pipelines](../6_pipelines/) - Automated data synchronization
- MCP: [Model Context Protocol](../19_mcp/) - AI assistant integration
- Network: [Network Requirements](../3_deployment_guide/7_network_requirements/) - Firewall and connectivity
- Security: [Network Security](../20_security/4_network_security/) - Security architecture
- Authentication: [Authentication Setup](../11_access_management/1_authentication_setup/) - Configure SSO
