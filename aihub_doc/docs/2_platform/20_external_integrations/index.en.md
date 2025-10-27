---
title: 'External system integrations'
index: 20
---

# External system integrations

The Swiss AI-Hub connects with external systems through multiple integration approaches, bringing AI capabilities into existing business workflows and tools.

## Integration approaches

The platform supports three integration patterns, each suited for different use cases:

### 1. Direct agent API calls

Agents can directly call external APIs (REST, SOAP, GraphQL, etc.) from within their workflow steps using standard Python HTTP libraries.

How it works:
- Implement HTTP calls within agent `@step` methods using `httpx` or `aiohttp`
- Agents make API calls as part of their workflow logic during execution
- Responses are processed and incorporated into agent outputs

Best for:
- Simple, single-operation API calls as part of agent workflows
- Real-time data retrieval during agent conversations
- Write operations to external systems based on agent decisions

Example use cases:
- Agent retrieves customer data from CRM during conversation
- Agent submits form data to external portal after user approval
- Agent queries status from ticketing system to answer user questions

Developer guide: See the [Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) for implementation patterns and examples.

### 2. Platform API integration (external systems calling in)

External systems can trigger AI-Hub agents and receive results through the [Agent Interaction REST API](../16_api/2_agent_interaction_api/).

How it works:
- External systems make HTTP requests to AI-Hub REST API
- API authenticates requests and translates them into internal events
- Agents process requests and stream responses back
- External systems receive structured results

Best for:
- Bidirectional integration where external systems trigger AI capabilities
- Portal or application UI embedding AI functionality
- Event-driven architectures with webhook integration

Example use cases:
- Document portal triggers AI classification on file upload
- Web application requests AI-generated summaries for dashboard
- External workflow system delegates analysis tasks to AI agents

### 3. Data pipeline integration (batch synchronization)

Use [Data Pipelines](../6_pipelines/) for continuous synchronization of data from external systems into AI-Hub knowledge bases.

How it works:
- Dagster pipelines connect to external data sources
- Data is extracted, transformed, and loaded into AI-Hub
- Knowledge bases are indexed for RAG (Retrieval-Augmented Generation)
- Pipelines run on schedules or triggered by events

Best for:
- Read-heavy integrations where AI primarily analyzes external data
- Large-scale document indexing for search and retrieval
- Scheduled data synchronization from enterprise systems

Example use cases:
- Nightly sync of SharePoint documents into knowledge base
- Continuous ingestion of support tickets for trend analysis
- Scheduled import of product catalog for customer service agents

### 4. MCP integration (development tools)

Use [Model Context Protocol (MCP)](../17_mcp/) to let AI development assistants interact with AI-Hub during development.

Best for:
- AI coding assistants (Claude Code, Gemini CLI, Cursor)
- Development and debugging workflows
- Read-only observation of platform state

## Choosing the right approach

| Approach | Latency | Direction | Complexity | Best for |
|----------|---------|-----------|------------|----------|
| Direct agent API calls | Real-time | Outbound | Low | Simple API calls within agent logic |
| Platform API integration | Real-time | Inbound | Medium | External systems triggering AI |
| Data pipeline integration | Batch | Inbound | Medium-High | Large-scale data sync, knowledge bases |
| MCP integration | Real-time | Bidirectional | Low | Development tools only |

## Network and security considerations

When integrating with external systems, ensure proper network configuration:

### Outbound connectivity (for direct agent API calls and pipelines)

The AI-Hub VM requires outbound HTTPS (port 443) access to external systems:

- External APIs: Configure firewall rules to allow outbound connections to specific endpoints
- Authentication: Support for API keys, OAuth tokens, and certificate-based authentication
- TLS/SSL: All external connections use encrypted HTTPS

See [Network Requirements](../3_deployment_guide/7_network_requirements/) for more details.

### Inbound connectivity (for platform API integration)

External systems connecting to AI-Hub use standard HTTPS (port 443):

- Authentication: OAuth 2.0, API keys, or Azure AD integration
- Rate limiting: Built-in protection via Traefik reverse proxy
- TLS termination: Automatic certificate management with Let's Encrypt

See [Network Security](../18_security/5_network_security/) for more details.

## General integration principles

When integrating AI-Hub with external systems:

1. Choose the right pattern: Match integration approach to your latency, volume, and direction requirements
2. Data sovereignty: Deploy AI-Hub in Switzerland for Swiss data residency requirements
3. Security: Use TLS encryption, RBAC, and comprehensive audit logging
4. Authentication: Leverage enterprise SSO (OAuth 2.0, SAML, Azure AD)
5. Network configuration: Ensure proper firewall rules for inbound/outbound connectivity
6. Compliance: Follow [Swiss Data Protection](../19_compliance/3_dsg/) guidelines

## Related documentation

- Agents: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) - Implementing direct API calls
- API: [Agent Interaction REST API](../16_api/2_agent_interaction_api/) - Platform HTTP interface
- Pipelines: [Data Pipelines](../6_pipelines/) - Automated data synchronization
- MCP: [Model Context Protocol](../17_mcp/) - AI assistant integration
- Network: [Network Requirements](../3_deployment_guide/7_network_requirements/) - Firewall and connectivity
- Security: [Network Security](../18_security/5_network_security/) - Security architecture
- Authentication: [Authentication Setup](../11_access_management/1_authentication_setup/) - Configure SSO
