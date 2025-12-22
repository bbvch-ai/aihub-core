---
title: Docker Network Isolation
---

# Docker Network Isolation

The AI-Hub platform implements network segmentation to enforce security boundaries between services. This defense-in-depth
approach limits the blast radius of potential security breaches and enforces the principle of least privilege at the
network layer.

## Network Zones

The platform uses four isolated Docker networks:

| Network   | Purpose                              | External Access |
|-----------|--------------------------------------|-----------------|
| `proxy`   | External traffic via Traefik         | Yes             |
| `backend` | Internal application services        | No              |
| `data`    | Databases and message broker         | No              |
| `storage` | SeaweedFS object storage             | No              |

## Service Network Assignments

Each service is assigned to only the networks it requires for operation:

### Proxy Network Services

Services accessible from outside the Docker network:

- **traefik**: Reverse proxy and API gateway
- **api**: REST API and WebSocket endpoints
- **web**: Admin UI frontend
- **open-webui**: Chat interface
- **bot**: MS Teams/Slack integration
- **seaweedfs-s3**: S3-compatible storage API
- **oauth2proxy-***: Authentication proxies

### Backend Network Services

Internal application and processing services:

- **litellm**: LLM gateway and request routing
- **docling**: Document parsing and extraction
- **presidio-analyzer/anonymizer**: PII detection and anonymization
- **llama-cpp-***: Local LLM inference (chat, embedding, reranking)
- **speaches**: Speech-to-text and text-to-speech
- **jupyter**: Code execution environment
- **playwright**: Web scraping and automation
- **agents**: All agent workers (rag, expert, wrapping)
- **pipelines**: Data processing pipelines
- **dagster-***: Pipeline orchestration
- **phoenix**: AI observability
- **otel-collector**: Telemetry aggregation

### Data Network Services

Persistence and messaging infrastructure:

- **postgres**: Primary PostgreSQL database
- **pgbouncer**: Connection pooler for Dagster
- **postgres-ferretdb**: PostgreSQL backend for FerretDB
- **ferretdb**: MongoDB-compatible document store
- **milvus-standalone**: Vector database
- **etcd**: Distributed key-value store (Milvus metadata)
- **valkey**: Redis-compatible in-memory cache
- **nats**: Message broker for event-driven communication

### Storage Network Services

Distributed object storage cluster:

- **seaweedfs-master**: Cluster coordinator
- **seaweedfs-volume**: Data storage nodes
- **seaweedfs-filer**: File system interface
- **seaweedfs-s3**: S3 API gateway
- **etcd**: Filer metadata backend

## Network Topology

```mermaid
flowchart TB
    subgraph Internet
        ext[External Traffic]
    end

    subgraph proxy[PROXY NETWORK]
        traefik[traefik]
        api[api]
        web[web]
        openwebui[open-webui]
        bot[bot]
        s3proxy[seaweedfs-s3]
    end

    subgraph backend[BACKEND NETWORK]
        litellm[litellm]
        docling[docling]
        presidio[presidio]
        llama[llama-cpp-*]
        agents[agents]
        jupyter[jupyter]
        playwright[playwright]
        dagster[dagster-*]
        pipelines[pipelines]
        phoenix[phoenix]
        otel[otel-collector]
    end

    subgraph data[DATA NETWORK]
        postgres[postgres]
        ferretdb[ferretdb]
        milvus[milvus]
        valkey[valkey]
        nats[nats]
        etcd[etcd]
    end

    subgraph storage[STORAGE NETWORK]
        swmaster[seaweed-master]
        swvolume[seaweed-volume]
        swfiler[seaweed-filer]
    end

    ext -->|:80, :443| traefik
    traefik --> api
    traefik --> web
    traefik --> openwebui
    traefik --> bot
    traefik --> s3proxy

    api --> litellm
    api --> agents
    openwebui --> litellm
    agents --> nats
    agents --> milvus
    pipelines --> nats
    dagster --> postgres
    phoenix --> postgres
    litellm --> postgres

    milvus --> etcd
    milvus --> s3proxy
    swfiler --> etcd
    s3proxy --> swfiler
    swfiler --> swvolume
    swvolume --> swmaster
```

## Security Implications

### What Each Network Boundary Protects

**Proxy → Backend Boundary**
- External users cannot directly access internal processing services
- Compromised Traefik cannot reach databases without going through API

**Backend → Data Boundary**
- Processing services access databases through defined interfaces
- Compromised AI service cannot directly manipulate other databases

**Data → Storage Boundary**
- SeaweedFS internal cluster communication is isolated
- Database services cannot interfere with storage operations

### Service Visibility Matrix

| From \ To | proxy | backend | data | storage |
|-----------|-------|---------|------|---------|
| External  | ✓     | ✗       | ✗    | ✗       |
| proxy     | ✓     | ✓       | ✗    | ✗       |
| backend   | ✗     | ✓       | ✓    | ✓       |
| data      | ✗     | ✗       | ✓    | ✓       |
| storage   | ✗     | ✗       | ✗    | ✓       |

## Operational Considerations

### Adding New Services

When adding a new service, determine which networks it needs:

1. **Needs external access?** → Add to `proxy`
2. **Is an application service?** → Add to `backend`
3. **Needs database access?** → Add to `data`
4. **Needs object storage?** → Add to `storage`

### Debugging Network Issues

If a service cannot reach another service:

1. Verify both services are on a common network
2. Check if the target network is marked `internal: true`
3. Use `docker network inspect <network>` to see connected containers
4. Check service names match DNS expectations (container_name)

### Network Inspection Commands

```bash
# List all networks
docker network ls

# Inspect a specific network
docker network inspect aihub-core_backend

# See which networks a container is connected to
docker inspect <container> --format '{{json .NetworkSettings.Networks}}'
```
