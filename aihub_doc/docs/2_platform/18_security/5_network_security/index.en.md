---
title: Network Security
index: 5
---

# Network Security

The AI-Hub implements a defense-in-depth network security architecture through multiple independent layers of protection.

## Single Public Endpoint Architecture

The deployment minimizes attack surface through a single entry point:

- **Public Exposure**: VM public IP on ports 80 and 443 only
- **Internal Services**: All application services run in isolated Docker containers on internal networks
- **Proxy Layer**: Traefik reverse proxy is the only component directly exposed to the internet

This dramatically reduces attack surface compared to exposing multiple service ports. Only Traefik faces the public internet—all backend services remain isolated.

## Defense in Depth

The AI-Hub implements security through multiple independent layers:

### Layer 1: Network Security

**Network Security Group (NSG) / Firewall**

- Only ports 80 and 443 accessible from public internet
- Default deny policy for all other ports
- Optional: Restrict SSH to specific IP ranges

### Layer 2: Reverse Proxy

**Traefik Configuration**

- **TLS Termination**: All connections use HTTPS with TLS 1.2 or higher
- **Security Headers**: Automatic injection of HSTS, X-Frame-Options, X-Content-Type-Options, etc.
- **Let's Encrypt Integration**: Automatic certificate provisioning and renewal
- **Rate Limiting**: Protection against brute force and DoS attempts

### Layer 3: Authentication

**Identity and Access Management**

- **Azure AD OAuth2**: All users authenticate via corporate Active Directory
- **RBAC**: Role-based access control for fine-grained permissions
- **API Keys**: Separate authentication for service-to-service communication
- **Session Management**: Secure session handling with configurable timeouts

### Layer 4: Container Isolation

**Docker Security**

- All services run in isolated containers with minimal privileges
- Container networking prevents direct access between unrelated services
- Resource limits prevent resource exhaustion attacks
- Regular image updates for security patches

### Layer 5: Data Protection

**PII and Sensitive Data Guards**

- **Presidio Integration**: Automatic detection and anonymization of PII in LLM requests
- **Sensitive Information Guards**: AI-powered scanning of responses before delivery
- **Audit Logging**: Complete audit trail of all data access and processing

## Network Architecture

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
         ├── Azure OpenAI
         ├── Azure AD
         ├── External APIs
         └── Other Integrations
```

## Related Documentation

- [Network Requirements](../../3_deployment_guide/7_network_requirements/) - Firewall rules and connectivity
- [Deployment Options](../../3_deployment_guide/1_deployment_options/) - Architecture and hosting strategies
- [Container Security](../4_container_security/) - Container isolation and hardening
- [Authentication](../1_authentication/) - Authentication mechanisms
- [Input Validation](../3_input_validation/) - Input sanitization and validation
- [Infrastructure Layers](../../2_architecture/2_infrastructure_layers/) - Detailed infrastructure component overview
