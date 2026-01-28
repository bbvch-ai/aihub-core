# Adopt Docker Network Isolation Strategy

## Context

The AI-Hub platform runs all Docker containers within a single default network. This flat network topology presents
security risks: if any container is compromised, an attacker gains network-level access to all other containers,
including databases and storage systems. Defense in depth requires network segmentation to limit blast radius.

## Decision Drivers

- **Security by design**: Limit network access to only what each service requires
- **Defense in depth**: Contain breaches by segmenting network zones
- **Operational simplicity**: Balance security with maintainability

## Decision

We implement Docker network isolation using five distinct networks:

| Network   | Internal | ICC     | Purpose                                    |
|-----------|----------|---------|-------------------------------------------|
| `proxy`   | No       | Yes     | External traffic via Traefik (ingress)    |
| `backend` | Yes      | Yes     | Internal application services             |
| `data`    | Yes      | Yes     | Databases, caches, message broker         |
| `storage` | Yes      | Yes     | SeaweedFS distributed storage             |
| `egress`  | No       | No      | Outbound internet access only (no ingress)|

Services are assigned to only the networks they require. The `internal: true` flag prevents direct external access. The `egress` network has ICC (Inter-Container Communication) disabled, ensuring containers can only reach the internet but not each other via this network.

**Example assignments:**
- `traefik`: proxy, backend
- `api`: proxy, backend, data, storage
- `postgres`: data
- `seaweedfs-*`: storage
- `playwright`: backend, egress (needs outbound internet for web browsing)

## Consequences

### Positive

- Network-level isolation prevents lateral movement in case of breach
- Docker enforces boundaries automatically with no performance impact
- Network assignments document service dependencies

### Negative

- Each service needs explicit network assignments
- Network issues may be harder to diagnose
- Must update assignments when adding new services
