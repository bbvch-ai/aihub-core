---
title: Network Security
index: 5
---

# Network Security

The AI-Hub implements a **defense-in-depth** network security architecture, using multiple independent layers of protection to secure the platform, its data, and its users.

All internal application services (like the AI-Hub API, Web UI, LiteLLM Proxy, and databases) run in isolated Docker containers on private networks. The **Traefik reverse proxy** is the only component directly accessible from the internet, accepting public traffic only on ports 80 and 443.

This proxy is responsible for routing requests to the correct internal service. All backend services remain completely isolated and are never directly exposed to the public internet.

```
Internet
    ↓
[Firewall/NSG]
    ↓ (ports 80, 443)
[VM Public IP]
    ↓
[Traefik Reverse Proxy]
    ↓
[Docker Internal Network]
    ├── AI-Hub API
    ├── Web UI
    ├── LiteLLM Proxy
    ├── Database Services
    └── Background Workers
         ↓
    (Outbound to External Services)
         ├── LLM Providers (Azure OpenAI, Google Gemini, OpenAI)
         ├── Azure Cognitive Services (AI Search, Document Intelligence, Speech)
         ├── Authentication (Microsoft Entra ID, Azure AD)
         ├── Jina AI (Web Search & Embeddings)
         └── Customer APIs (SharePoint, Confluence, Custom REST APIs)
```

## Defense in Depth Layers

Security is applied at every stage of a request, from the network edge to the application logic.

### Layer 1: Network Firewall (NSG)

The first layer of defense is the Network Security Group (NSG) or firewall. It enforces a **default deny** policy, ensuring that only necessary ports (80 for HTTP and 443 for HTTPS) are accessible from the public internet. All other ports are blocked. Optionally, administrative access (like SSH) can be restricted to specific, trusted IP ranges.

### Layer 2: Reverse Proxy (Traefik)

As the single entry point, the Traefik reverse proxy secures all incoming connections. It **terminates TLS** (requiring HTTPS with TLS 1.2+), automatically provisions and renews certificates via Let's Encrypt, and injects critical **security headers** (like HSTS and X-Frame-Options). It also provides **rate limiting** to protect backend services from brute-force and simple Denial of Service (DoS) attacks.

### Layer 3: Authentication (IAM)

Access to the hub is managed through robust Identity and Access Management (IAM). User authentication is handled via **Azure AD OAuth2**, integrating with corporate identity. This enables **Role-Based Access Control (RBAC)** for defining fine-grained permissions. Separate **API keys** are used to authenticate service-to-service communication, while secure session management with configurable timeouts protects user sessions.

### Layer 4: Container Isolation

All application services run as non-root users in **isolated Docker containers** with minimal privileges. Container networking rules prevent direct communication between unrelated services, and resource limits mitigate resource exhaustion attacks. Images are regularly updated with the latest security patches to protect against known vulnerabilities.

### Layer 5: Data Protection

The final layer protects sensitive data. The hub integrates **Presidio** to automatically detect and anonymize Personally Identifiable Information (PII) in LLM requests. AI-powered **sensitive information guards** scan responses before they are delivered to the user. A comprehensive **audit trail** logs all data access and processing for accountability.


## Related Documentation

- [Network Requirements](../../3_deployment_guide/7_network_requirements/) - Firewall rules and connectivity
- [Deployment Options](../../3_deployment_guide/1_deployment_options/) - Architecture and hosting strategies
- [Container Security](../4_container_security/) - Container isolation and hardening
- [Authentication](../1_authentication/) - Authentication mechanisms
- [Input Validation](../3_input_validation/) - Input sanitization and validation
- [Infrastructure Layers](../../2_architecture/2_infrastructure_layers/) - Detailed infrastructure component overview
