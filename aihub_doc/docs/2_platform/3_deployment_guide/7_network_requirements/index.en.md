---
title: Network requirements
---

# Network requirements

This page covers network connectivity, firewall rules, and security requirements for production deployments.

## External service connectivity

The AI-Hub VM connects to external services depending on your configuration. All external connections use HTTPS (port
443).

Which providers you need depends on your deployment configuration.

::: details AI service endpoints
| Service         | Endpoint                                      | Port | Purpose                                             |
| --------------- | --------------------------------------------- | ---- | --------------------------------------------------- |
| Swiss LLM Cloud | Configured via `SWISS_LLM_CLOUD_API_BASE_URL` | 443  | Text generation, embedding, reranking, whisper, OCR |
| Jina AI         | `api.jina.ai`                                 | 443  | Web search and embeddings                           |
| Hugging Face    | `huggingface.co`                              | 443  | Model downloads for self-hosted inference           |

GPU deployments running local vLLM do not require outbound connectivity to LLM providers.
:::

Agents and pipelines can call your existing enterprise systems.

::: details Example customer integration endpoints
| Service          | Endpoint                  | Port | Protocol  | Authentication                  |
| ---------------- | ------------------------- | ---- | --------- | ------------------------------- |
| SharePoint       | `<tenant>.sharepoint.com` | 443  | Graph API | OAuth2 (Azure AD App)           |
| Confluence       | `<company>.atlassian.net` | 443  | REST      | API Token                       |
| Custom REST APIs | Customer-specific         | 443  | REST      | Various (API Key, OAuth2, mTLS) |
| SOAP Services    | Customer-specific         | 443  | SOAP      | WS-Security, Basic Auth         |
:::

### Identity provider services

User authentication requires connectivity to your configured OIDC provider. The example below shows Microsoft Entra ID
endpoints; substitute with your provider's endpoints as needed.

| Service            | Endpoint                    | Purpose                                                         |
| ------------------ | --------------------------- | --------------------------------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2/OIDC user authentication                                 |
| Microsoft Graph    | `graph.microsoft.com`       | Only needed for SharePoint/OneDrive pipeline sources (not auth) |

### Inbound connections

Users and administrators connect to the AI-Hub on these ports.

| Source         | Destination  | Port | Purpose                   |
| -------------- | ------------ | ---- | ------------------------- |
| User Browsers  | VM Public IP | 443  | Web UI and chat interface |
| Administrators | VM Public IP | 22   | SSH administrative access |

## Firewall configuration

Production deployments expose three inbound ports. This minimizes the attack surface.

### Inbound rules

Configure these rules in your network security group (NSG) or firewall:

| Priority | Name           | Port | Protocol | Purpose                                             |
| -------- | -------------- | ---- | -------- | --------------------------------------------------- |
| 100      | AllowHTTPS     | 443  | TCP      | Primary access to AI-Hub services                   |
| 110      | AllowHTTP      | 80   | TCP      | ACME/Let's Encrypt validation + HTTP→HTTPS redirect |
| 120      | AllowSSH       | 22   | TCP      | Administrative access (restrict source IPs)         |
| 65000    | DenyAllInbound | \*   | \*       | Default deny all other inbound traffic              |

::: tip
Restrict SSH access (port 22) to specific administrator IP addresses or VPN ranges instead of allowing from any source.
:::

### Outbound rules

The AI-Hub needs outbound connectivity for external integrations and updates:

| Priority | Name       | Port | Protocol | Purpose                                       |
| -------- | ---------- | ---- | -------- | --------------------------------------------- |
| 100      | AllowHTTPS | 443  | TCP      | API calls to LLM providers, external services |
| 110      | AllowHTTP  | 80   | TCP      | Let's Encrypt certificate validation          |
| 120      | AllowDNS   | 53   | UDP      | DNS resolution                                |

The platform reaches various external APIs based on your integrations. No additional outbound restrictions are needed.

## Related documentation

- [Deployment options](../1_deployment_options/) - Architecture and hosting strategies
- [Network security](../../20_security/4_network_security/) - Security architecture and defense-in-depth
- [Authentication](../../20_security/1_authentication/) - Identity provider integration details
- [Infrastructure layers](../../2_architecture/2_infrastructure_layers/) - Infrastructure component overview
