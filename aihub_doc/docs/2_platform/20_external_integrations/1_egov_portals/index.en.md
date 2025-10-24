---
title: 'eGovernment Portal Integration'
index: 5
---

# eGovernment Portal Integration

::: info No Special eGov Integration
The Swiss AI-Hub does **not provide dedicated eGovernment portal connectors**. However, eGovernment portals can be integrated using the platform's standard integration mechanisms for external systems and APIs.
:::

## Integration Approaches

eGovernment portals are external systems that can be integrated into the AI-Hub using three primary approaches:

### 1. Direct Agent API Calls

Agents can directly call external APIs (including eGov portal APIs) from within their workflow steps using standard Python HTTP libraries:

- **How**: Implement HTTP calls within agent `@step` methods using `httpx` or `aiohttp`
- **Best For**: Simple, single-operation API calls that are part of the agent's workflow logic
- **Use Cases**: Retrieving case status, submitting forms, querying portal data as part of an agent conversation
- **Developer Guide**: See the [Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) for implementation patterns

### 2. Real-Time API Integration via Platform API

For external systems that need to trigger AI agents or integrate agent capabilities into eGov portals:

- **See**: [Agent Interaction REST API](../../16_api/2_agent_interaction_api/) - Learn how external systems can interact with AI-Hub agents
- **Best For**: Bidirectional integration where the portal triggers AI capabilities and receives results
- **Use Cases**: Portal-initiated document classification, automated response generation, AI-assisted case processing

### 3. Data Pipeline Integration (Batch/Scheduled)

For read-heavy scenarios where portal data needs to be synchronized and made available to AI agents:

- **See**: [Data Pipelines](../../6_pipelines/) - Learn how to build data ingestion pipelines for external sources
- **Best For**: Large-scale data synchronization, knowledge base building, scheduled data refresh
- **Use Cases**: Case summarization, knowledge search across portal archives, document indexing for RAG

## Additional Considerations

When integrating eGovernment portals, consider the following platform capabilities:

- **Authentication**: Configure SSO and enterprise authentication - see [Authentication Setup](../../11_access_management/1_authentication_setup/)
- **Data Protection**: Ensure compliance with Swiss regulations - see [Swiss Data Protection](../../19_compliance/3_dsg/)
- **Security**: Follow security best practices for external system integration

## Need Help?

If you plan to integrate an eGovernment portal and need guidance on the best approach for your use case, contact the AI-Hub team or refer to the documentation sections linked above.
