---
title: 'eGovernment Portal Integration'
index: 5
---

# eGovernment Portal Integration

::: info No Special eGov Integration
The Swiss AI-Hub does **not provide dedicated eGovernment portal connectors**. However, eGovernment portals can be integrated using the platform's standard integration mechanisms for external systems and APIs.
:::

## Integration Approach

eGovernment portals are external systems that can be integrated into the AI-Hub using two primary approaches:

### 1. API-Based Integration (Real-Time)

For real-time interactions where AI agents need to read from and write to eGov portals:

- **See**: [Agent Interaction REST API](../../16_api/2_agent_interaction_api/) - Learn how to integrate external APIs with AI-Hub agents
- **Use Cases**: Document classification, citizen inquiry response, case status updates

### 2. Data Pipeline Integration (Batch/Scheduled)

For read-heavy scenarios where portal data needs to be synchronized and made available to AI agents:

- **See**: [Data Pipelines](../../6_pipelines/) - Learn how to build data ingestion pipelines for external sources
- **Use Cases**: Case summarization, knowledge search across portal archives, document indexing

## Additional Considerations

When integrating eGovernment portals, consider the following platform capabilities:

- **Authentication**: Configure SSO and enterprise authentication - see [Authentication Setup](../../11_access_management/1_authentication_setup/)
- **Data Protection**: Ensure compliance with Swiss regulations - see [Swiss Data Protection](../../19_compliance/3_dsg/)
- **Security**: Follow security best practices for external system integration

## Need Help?

If you plan to integrate an eGovernment portal and need guidance on the best approach for your use case, contact the AI-Hub team or refer to the documentation sections linked above.
