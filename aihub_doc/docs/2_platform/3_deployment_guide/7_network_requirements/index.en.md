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
| Service       | Endpoint                            | Port | Purpose                                   |
| ------------- | ----------------------------------- | ---- | ----------------------------------------- |
| Azure OpenAI  | `*.openai.azure.com`                | 443  | LLM inference, embeddings, vision, audio  |
| Google Gemini | `generativelanguage.googleapis.com` | 443  | LLM inference                             |
| Jina AI       | `api.jina.ai`                       | 443  | Web search and embeddings                 |
| Hugging Face  | `huggingface.co`                    | 443  | Model downloads for self-hosted inference |
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

### Microsoft services

User authentication and management use Microsoft Entra ID.

| Service            | Endpoint                    | Purpose                            |
| ------------------ | --------------------------- | ---------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2 user authentication         |
| Microsoft Graph    | `graph.microsoft.com`       | User profiles and group membership |

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

## DNS configuration

Production deployments require proper DNS configuration for both external access and internal service communication.

### External DNS records

Create DNS records for all six subdomains pointing to your VM's public IP:

```bash
# A records (or CNAMEs to your VM's hostname)
aihub.example.com           → 203.0.113.10
openwebui.aihub.example.com → 203.0.113.10
dagster.aihub.example.com   → 203.0.113.10
datalake.aihub.example.com  → 203.0.113.10
datalake-api.aihub.example.com → 203.0.113.10
traefik.aihub.example.com   → 203.0.113.10
```

### Internal DNS resolution

The VM must be able to resolve its own domain names. This is critical for OAuth callbacks and internal service communication.

**Common issue**: DNS records configured externally but not resolvable from the VM itself. This causes authentication timeouts and OAuth failures.

If external DNS works but internal resolution fails, the VM's nameserver configuration may be blocking requests.

### Nameserver configuration

Check `/etc/resolv.conf` on your VM:

```bash
cat /etc/resolv.conf
```

**Common issue**: Nameservers not in your subnet may block DNS requests, causing authentication timeouts. If you experience OAuth timeout errors, verify your nameserver can resolve your domain.

### DNS propagation

After creating DNS records, allow time for propagation:

- Internal corporate DNS: 5-15 minutes
- Public DNS: 1-48 hours (depends on TTL)

Let's Encrypt certificate provisioning requires globally accessible DNS records on ports 80 and 443.

## Related documentation

- [Deployment options](../1_deployment_options/) - Architecture and hosting strategies
- [Network security](../../18_security/4_network_security/) - Security architecture and defense-in-depth
- [Authentication](../../18_security/1_authentication/) - Identity provider integration details
- [Infrastructure layers](../../2_architecture/2_infrastructure_layers/) - Infrastructure component overview
