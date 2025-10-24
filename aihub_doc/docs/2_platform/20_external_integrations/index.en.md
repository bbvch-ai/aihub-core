---
title: 'External System Integrations'
index: 20
---

# External System Integrations

The Swiss AI-Hub provides multiple integration approaches for connecting with external systems, enabling AI capabilities within existing business workflows and tools.

## Integration Approaches

The platform supports three primary integration patterns, each suited for different use cases:

### 1. Direct Agent API Calls

Agents can directly call external APIs (REST, SOAP, GraphQL, etc.) from within their workflow steps using standard Python HTTP libraries.

**How It Works:**
- Implement HTTP calls within agent `@step` methods using `httpx` or `aiohttp`
- Agents make API calls as part of their workflow logic during execution
- Responses are processed and incorporated into agent outputs

**Best For:**
- Simple, single-operation API calls as part of agent workflows
- Real-time data retrieval during agent conversations
- Write operations to external systems based on agent decisions

**Example Use Cases:**
- Agent retrieves customer data from CRM during conversation
- Agent submits form data to external portal after user approval
- Agent queries status from ticketing system to answer user questions

**Developer Guide:** See the [Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) for implementation patterns and examples.

### 2. Platform API Integration (External Systems Calling In)

External systems can trigger AI-Hub agents and receive results through the [Agent Interaction REST API](../16_api/2_agent_interaction_api/).

**How It Works:**
- External systems make HTTP requests to AI-Hub REST API
- API authenticates requests and translates them into internal events
- Agents process requests and stream responses back
- External systems receive structured results

**Best For:**
- Bidirectional integration where external systems trigger AI capabilities
- Portal or application UI embedding AI functionality
- Event-driven architectures with webhook integration

**Example Use Cases:**
- Document portal triggers AI classification on file upload
- Web application requests AI-generated summaries for dashboard
- External workflow system delegates analysis tasks to AI agents

### 3. Data Pipeline Integration (Batch Synchronization)

Use [Data Pipelines](../6_pipelines/) for continuous synchronization of data from external systems into AI-Hub knowledge bases.

**How It Works:**
- Dagster pipelines connect to external data sources
- Data is extracted, transformed, and loaded into AI-Hub
- Knowledge bases are indexed for RAG (Retrieval-Augmented Generation)
- Pipelines run on schedules or triggered by events

**Best For:**
- Read-heavy integrations where AI primarily analyzes external data
- Large-scale document indexing for search and retrieval
- Scheduled data synchronization from enterprise systems

**Example Use Cases:**
- Nightly sync of SharePoint documents into knowledge base
- Continuous ingestion of support tickets for trend analysis
- Scheduled import of product catalog for customer service agents

### 4. MCP Integration (Development Tools)

Use [Model Context Protocol (MCP)](../17_mcp/) for enabling AI development assistants to interact with AI-Hub during development.

**Best For:**
- AI coding assistants (Claude Code, Gemini CLI, Cursor)
- Development and debugging workflows
- Read-only observation of platform state

## Choosing the Right Approach

| Approach | Latency | Direction | Complexity | Best For |
|----------|---------|-----------|------------|----------|
| **Direct Agent API Calls** | Real-time | Outbound | Low | Simple API calls within agent logic |
| **Platform API Integration** | Real-time | Inbound | Medium | External systems triggering AI |
| **Data Pipeline Integration** | Batch | Inbound | Medium-High | Large-scale data sync, knowledge bases |
| **MCP Integration** | Real-time | Bidirectional | Low | Development tools only |

## Network and Security Considerations

When integrating with external systems, ensure proper network configuration:

### Outbound Connectivity (for Direct Agent API Calls and Pipelines)

The AI-Hub VM requires outbound HTTPS (port 443) access to external systems:

- **External APIs**: Configure firewall rules to allow outbound connections to specific endpoints
- **Authentication**: Support for API keys, OAuth tokens, and certificate-based authentication
- **TLS/SSL**: All external connections use encrypted HTTPS

See [Network Requirements](../3_deployment_guide/7_network_requirements/) for more details.

### Inbound Connectivity (for Platform API Integration)

External systems connecting to AI-Hub use standard HTTPS (port 443):

- **Authentication**: OAuth 2.0, API keys, or Azure AD integration
- **Rate Limiting**: Built-in protection via Traefik reverse proxy
- **TLS Termination**: Automatic certificate management with Let's Encrypt

See [Network Security](../18_security/5_network_security/) for more details.

## General Integration Principles

When integrating AI-Hub with external systems:

1. **Choose the Right Pattern**: Match integration approach to your latency, volume, and direction requirements
2. **Data Sovereignty**: Deploy AI-Hub in Switzerland for Swiss data residency requirements
3. **Security**: Use TLS encryption, RBAC, and comprehensive audit logging
4. **Authentication**: Leverage enterprise SSO (OAuth 2.0, SAML, Azure AD)
5. **Network Configuration**: Ensure proper firewall rules for inbound/outbound connectivity
6. **Compliance**: Follow [Swiss Data Protection](../19_compliance/3_dsg/) guidelines

## Related Documentation

- **Agents**: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) - Implementing direct API calls
- **API**: [Agent Interaction REST API](../16_api/2_agent_interaction_api/) - Platform HTTP interface
- **Pipelines**: [Data Pipelines](../6_pipelines/) - Automated data synchronization
- **MCP**: [Model Context Protocol](../17_mcp/) - AI assistant integration
- **Network**: [Network Requirements](../3_deployment_guide/7_network_requirements/) - Firewall and connectivity
- **Security**: [Network Security](../18_security/5_network_security/) - Security architecture
- **Authentication**: [Authentication Setup](../11_access_management/1_authentication_setup/) - Configure SSO
