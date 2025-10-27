---
title: Network Requirements
index: 7
---

# Network Requirements

This section covers network connectivity, firewall configuration, and security requirements for deploying the Swiss
AI-Hub in production environments.

## External Service Connectivity

The AI-Hub VM may be able to communicate with several external services for full functionality. All external
connections use HTTPS (port 443) for security.

### AI Service Providers

The platform connects to various AI service providers based on deployment configuration.

::: details AI Service Endpoints
| Service | Endpoint | Port | Purpose |
|---------|----------|------|---------|
| Azure OpenAI | `*.openai.azure.com` | 443 | LLM inference, embeddings, vision, audio |
| Google Gemini | `generativelanguage.googleapis.com` | 443 | LLM inference |
| Jina AI | `api.jina.ai` | 443 | Web search and embeddings |
| Hugging Face | `huggingface.co` | 443 | Model downloads for self-hosted inference |
:::

### Azure Cognitive Services

When deployed with Azure integration, the platform uses multiple cognitive services.

::: details Azure Service Endpoints
| Service | Endpoint | Port | Purpose |
|---------|----------|------|---------|
| Azure AI Search | `*.search.windows.net` | 443 | Vector search and retrieval (RAG) |
| Azure Document Intelligence | `*.cognitiveservices.azure.com` | 443 | Document analysis and OCR |
| Azure Speech Services | `*.cognitiveservices.azure.com` | 443 | Speech-to-text, text-to-speech |
| Azure Data Lake Storage | `*.dfs.core.windows.net` | 443 | Scalable file storage |
| Azure Blob Storage | `*.blob.core.windows.net` | 443 | Object storage |
:::

### Customer Integrations

Organizations integrate the AI-Hub with existing enterprise systems via agent API calls or data pipelines.

::: details Example Customer Integration Endpoints
| Service | Endpoint | Port | Protocol | Authentication |
|---------|----------|------|----------|----------------|
| SharePoint | `<tenant>.sharepoint.com` | 443 | Graph API | OAuth2 (Azure AD App) |
| Confluence | `<company>.atlassian.net` | 443 | REST | API Token |
| Custom REST APIs | Customer-specific | 443 | REST | Various (API Key, OAuth2, mTLS) |
| SOAP Services | Customer-specific | 443 | SOAP | WS-Security, Basic Auth |
:::


### Microsoft Services

Authentication and user management rely on Microsoft Entra ID services.
| Service | Endpoint | Purpose 
| -----------------| --------------------------- | ---------------------------------- |
| Microsoft Entra ID| `login.microsoftonline.com` | OAuth2 user authentication |
| Microsoft Graph   | `graph.microsoft.com`        | User profiles and group membership |


### Inbound Connections

The AI-Hub accepts inbound connections on standard HTTPS ports, plus optional webhook endpoints and administrative
access.

| Source                   | Destination  | Port | Purpose                   |
| ------------------------ | ------------ | ---- |---------------------------|
| User Browsers            | VM Public IP | 443  | Web UI and chat interface |
| Administrators           | VM Public IP | 22   | SSH administrative access |


## Firewall Configuration

Production deployments require only three inbound ports to be publicly accessible, significantly reducing the attack
surface.

### Inbound Rules

Configure these rules in your network security group (NSG) or firewall:

| Priority | Name           | Port | Protocol | Purpose                                             |
| -------- | -------------- | ---- | -------- | --------------------------------------------------- |
| 100      | AllowHTTPS     | 443  | TCP      | Primary access to AI-Hub services                   |
| 110      | AllowHTTP      | 80   | TCP      | ACME/Let's Encrypt validation + HTTP→HTTPS redirect |
| 120      | AllowSSH       | 22   | TCP      | Administrative access (restrict source IPs)         |
| 65000    | DenyAllInbound | \*   | \*       | Default deny all other inbound traffic              |

::: tip
Restrict SSH access (port 22) to specific administrator IP addresses or VPN ranges rather than
allowing from any source.
::: 

### Outbound Rules

The AI-Hub requires outbound connectivity for external integrations and updates:

| Priority | Name       | Port | Protocol | Purpose                                       |
| -------- | ---------- | ---- | -------- | --------------------------------------------- |
| 100      | AllowHTTPS | 443  | TCP      | API calls to LLM providers, external services |
| 110      | AllowHTTP  | 80   | TCP      | Let's Encrypt certificate validation          |
| 120      | AllowDNS   | 53   | UDP      | DNS resolution                                |

::: info
No additional outbound restrictions are applied beyond these. The platform needs to reach various external
APIs based on your integration requirements.
:::

## Related Documentation

- [Deployment Options](../1_deployment_options/) - Architecture and hosting strategies
- [Network Security](../../18_security/5_network_security/) - Security architecture and defense-in-depth
- [Authentication](../../18_security/1_authentication/) - Identity provider integration details
- [Infrastructure Layers](../../2_architecture/2_infrastructure_layers/) - Detailed infrastructure component overview
