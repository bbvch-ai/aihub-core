---
title: 'External System Integrations'
index: 20
---

# External System Integrations

The Swiss AI-Hub provides multiple integration approaches for connecting with external systems, enabling AI capabilities within existing business workflows and tools.

## Integration Approaches

The platform supports three primary integration patterns:

### REST API Integration
Use the [Agent Interaction REST API](../16_api/2_agent_interaction_api/) for real-time, bidirectional communication between external systems and AI-Hub agents. This approach is ideal for:
- Interactive workflows requiring immediate AI responses
- Write operations that update external systems based on AI results
- Webhook-based event-driven integrations

### Data Pipeline Integration
Use [Data Pipelines](../6_pipelines/) for continuous synchronization of data from external systems into AI-Hub knowledge bases. This approach is ideal for:
- Read-heavy integrations where AI primarily analyzes external data
- Scheduled or event-triggered data synchronization
- Large-scale document indexing for RAG applications

### MCP Integration
Use [Model Context Protocol (MCP)](../17_mcp/) for enabling AI development assistants to interact with AI-Hub during development. This approach is ideal for:
- AI coding assistants (Claude Code, Gemini CLI, Cursor)
- Development and debugging workflows
- Read-only observation of platform state

## Integration Examples

The following sections provide guidance for integrating AI-Hub with specific external systems:

- **[eGovernment Portals](1_egov_portals/)**: Swiss public sector systems (CMI Axioma, RMS Gever)

## General Integration Principles

When integrating AI-Hub with external systems:

1. **Choose the Right Pattern**: Select API integration for real-time needs, pipelines for data synchronization
2. **Data Sovereignty**: Deploy AI-Hub in Switzerland for Swiss data residency requirements
3. **Security**: Use TLS encryption, RBAC, and comprehensive audit logging
4. **Authentication**: Leverage enterprise SSO (OAuth 2.0, SAML, Azure AD)
5. **Compliance**: Follow [Swiss Data Protection](../19_compliance/3_dsg/) guidelines

## Related Documentation

- **API**: [Agent Interaction REST API](../16_api/2_agent_interaction_api/) - Platform HTTP interface
- **Pipelines**: [Data Pipelines](../6_pipelines/) - Automated data synchronization
- **MCP**: [Model Context Protocol](../17_mcp/) - AI assistant integration
- **Authentication**: [Authentication Setup](../11_access_management/1_authentication_setup/) - Configure SSO
