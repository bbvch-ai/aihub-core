---
title: Network security
---

# Network security

The AI-Hub uses defense-in-depth network security. Multiple independent layers protect the platform, its data, and its
users.

All internal services (AI-Hub API, Web UI, LiteLLM Proxy, databases) run in isolated Docker containers on private
networks. The Traefik reverse proxy is the only component accessible from the internet, accepting public traffic on
ports 80 and 443.

Traefik routes requests to the correct internal service. Backend services remain isolated and never get exposed directly
to the public internet.

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

## Security layers

Security applies at every stage of a request, from network edge to application logic.

### Network firewall (NSG)

The Network Security Group (NSG) or firewall enforces a default deny policy. Only ports 80 (HTTP) and 443 (HTTPS) are
accessible from the public internet. All other ports are blocked. You can restrict administrative access like SSH to
specific trusted IP ranges.

### Reverse proxy (Traefik)

Traefik serves as the single entry point and secures all incoming connections. It terminates TLS (requiring HTTPS with
TLS 1.2+), automatically provisions and renews certificates via Let's Encrypt, and injects security headers like HSTS
and X-Frame-Options. Rate limiting protects backend services from brute-force and simple DoS attacks.

### Authentication (IAM)

Azure AD OAuth2 handles user authentication, integrating with corporate identity. This enables Role-Based Access Control
(RBAC) for fine-grained permissions. API keys authenticate service-to-service communication. Session management with
configurable timeouts protects user sessions.

### Container isolation

Application services run as non-root users in isolated Docker containers with minimal privileges. Container networking
rules prevent direct communication between unrelated services. Resource limits mitigate resource exhaustion attacks.
Images get updated regularly with security patches.

### Network segmentation

The platform uses five isolated Docker networks (`proxy`, `backend`, `data`, `storage`, `egress`) to enforce the
principle of least privilege at the network layer. Services are assigned only to the networks they require:

- **Internal networks** (`backend`, `data`, `storage`) have no external internet access
- **Egress network** allows outbound internet access only, with Inter-Container Communication (ICC) disabled
- Services needing to browse external websites (e.g., playwright) use the `egress` network without exposing ingress

See [Network Isolation](../../2_architecture/4_network_isolation/) for detailed network topology and service assignments.

### Data protection

Presidio automatically detects and anonymizes Personally Identifiable Information (PII) in LLM requests. AI-powered
sensitive information guards scan responses before delivery to users. An audit trail logs all data access and
processing.

## Related documentation

- [Network isolation](../../2_architecture/4_network_isolation/) - Docker network zones and service assignments
- [Network requirements](../../3_deployment_guide/7_network_requirements/) - Firewall rules and connectivity
- [Deployment options](../../3_deployment_guide/1_deployment_options/) - Architecture and hosting strategies
- [Container security](../3_container_security/) - Container isolation and hardening
- [Authentication](../1_authentication/) - Authentication mechanisms
- [Input validation](../2_input_validation/) - Input sanitization and validation
- [Infrastructure layers](../../2_architecture/2_infrastructure_layers/) - Infrastructure component overview
