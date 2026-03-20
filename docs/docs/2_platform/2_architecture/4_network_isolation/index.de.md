---
title: Docker-Netzwerkisolation
source_sha: 886435d094ebafec0f27145bc526bcf15419bb3c9b98b0e697541e7203c63b67
---

# Docker-Netzwerkisolation

Die Swiss AI Hub-Plattform implementiert Netzwerksegmentierung, um Sicherheitsgrenzen zwischen Services durchzusetzen.
Dieser Defence-in-Depth-Ansatz begrenzt den Auswirkungsbereich potenzieller Sicherheitsverletzungen und erzwingt das
Prinzip der geringsten Rechte auf der Netzwerkebene.

## Netzwerkzonen

Die Plattform verwendet fünf isolierte Docker-Netzwerke:

| Netzwerk  | Zweck                           | Externer Zugriff | ICC aktiviert |
| --------- | ------------------------------- | ---------------- | ------------- |
| `proxy`   | Externer Traffic über Traefik   | Ingress + Egress | Ja            |
| `backend` | Interne Anwendungs-Services     | Nein             | Ja            |
| `data`    | Datenbanken und Message Broker  | Nein             | Ja            |
| `storage` | SeaweedFS Objekt-Speicher       | Nein             | Ja            |
| `egress`  | Nur ausgehender Internetzugriff | Nur Egress       | Nein          |

Das `egress`-Netzwerk ist für Services konzipiert, die das Internet erreichen müssen (ausgehend), aber nicht aus dem
Internet erreichbar sein sollten (kein Ingress). Die Inter-Container-Kommunikation (ICC) ist in diesem Netzwerk
deaktiviert, was bedeutet, dass Container über dieses Netzwerk nicht miteinander kommunizieren können – sie können es
nur für den ausgehenden Internetzugriff nutzen.

## Service-Netzwerkzuweisungen

Jeder Service wird nur den Netzwerken zugewiesen, die er für den Betrieb benötigt:

### Proxy-Netzwerk-Services

Services, die von außerhalb des Docker-Netzwerks zugänglich sind:

- **traefik**: Reverse Proxy und API-Gateway
- **api**: REST API und WebSocket-Endpunkte
- **web**: Admin UI Frontend
- **open-webui**: Chat-Oberfläche
- **bot**: MS Teams/Slack-Integration
- **seaweedfs-s3**: S3-kompatible Speicher-API
- **oauth2proxy-**\*: Authentifizierungs-Proxys

### Backend-Netzwerk-Services

Interne Anwendungs- und Verarbeitungs-Services:

- **litellm**: LLM-Gateway und Request-Routing
- **mineru-api**: Dokumenten-Parsing und -Extraktion
- **presidio-analyzer/anonymizer**: PII-Erkennung und -Anonymisierung
- **vLLM**: Lokale LLM-Inferenz (Chat, Embedding, Reranking) – nur GPU Deployments
- **speaches**: Spracherkennung und Text-zu-Sprache
- **jupyter**: Code-Ausführungsumgebung
- **playwright**: Web-Scraping und Automatisierung (auch im `egress` für Internetzugriff)
- **agents**: Alle Agent Workers (RAG, Expert, Wrapping)
- **pipelines**: Datenverarbeitungs-Pipelines
- **dagster-**\*: Pipeline-Orchestrierung
- **langfuse**: KI-Observability
- **otel-collector**: Telemetrie-Aggregation

### Daten-Netzwerk-Services

Persistenz- und Messaging-Infrastruktur:

- **postgres**: Primäre PostgreSQL-Datenbank
- **pgbouncer**: Connection Pooler für Dagster
- **postgres-ferretdb**: PostgreSQL-Backend für FerretDB
- **ferretdb**: MongoDB-kompatibler Dokumentenspeicher
- **neo4j**: Graphdatenbank für Mem0-Speicher
- **milvus-standalone**: Vektordatenbank
- **etcd**: Verteilter Key-Value-Speicher (Milvus-Metadaten)
- **valkey**: Redis-kompatibler In-Memory-Cache
- **nats**: Message Broker für ereignisgesteuerte Kommunikation

### Speicher-Netzwerk-Services

Verteilter Objektspeicher-Cluster:

- **seaweedfs-master**: Cluster-Koordinator
- **seaweedfs-volume**: Datenspeicherknoten
- **seaweedfs-filer**: Dateisystem-Schnittstelle
- **seaweedfs-s3**: S3-API-Gateway
- **etcd**: Filer-Metadaten-Backend

### Egress-Netzwerk-Services

Services, die ausgehenden Internetzugriff, aber keinen eingehenden Zugriff benötigen:

- **playwright**: Web-Scraping und Browser-Automatisierung (muss Webseiten abrufen)

Dieses Netzwerk hat die ICC (Inter-Container Communication) deaktiviert, was die laterale Bewegung zwischen Containern
in diesem Netzwerk verhindert. Services nutzen `egress` ausschließlich für den ausgehenden Internetzugriff und müssen
andere Netzwerke (z.B. `backend`) für die Inter-Service-Kommunikation verwenden.

## Netzwerk-Topologie

```mermaid
flowchart TB
    subgraph Internet
        ext[External Traffic]
        websites[External Websites]
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
        mineru-api[mineru-api]
        presidio[presidio]
        vllm[vLLM]
        agents[agents]
        jupyter[jupyter]
        playwright[playwright]
        dagster[dagster-*]
        pipelines[pipelines]
        langfuse[langfuse]
        otel[otel-collector]
    end

    subgraph egress[EGRESS NETWORK - ICC Disabled]
        playwright_egress[playwright]
    end

    subgraph data[DATA NETWORK]
        postgres[postgres]
        ferretdb[ferretdb]
        neo4j[neo4j]
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
    openwebui --> playwright
    agents --> nats
    agents --> milvus
    agents --> neo4j
    pipelines --> nats
    dagster --> postgres
    langfuse --> postgres
    litellm --> postgres

    milvus --> etcd
    milvus --> s3proxy
    swfiler --> etcd
    s3proxy --> swfiler
    swfiler --> swvolume
    swvolume --> swmaster

    playwright_egress -->|outbound only| websites
```

## Sicherheitsimplikationen

### Was jede Netzwerkgrenze schützt

**Proxy → Backend-Grenze**

- Externe Benutzer können nicht direkt auf interne Verarbeitungs-Services zugreifen
- Kompromittiertes Traefik kann Datenbanken nicht erreichen, ohne die API zu durchlaufen

**Backend → Daten-Grenze**

- Verarbeitungs-Services greifen über definierte Schnittstellen auf Datenbanken zu
- Kompromittierter KI-Service kann andere Datenbanken nicht direkt manipulieren

**Daten → Speicher-Grenze**

- Die interne Cluster-Kommunikation von SeaweedFS ist isoliert
- Datenbank-Services können Speicheroperationen nicht beeinträchtigen

### Service-Sichtbarkeitsmatrix

| Von \\ Nach | proxy | backend | data | storage | egress | Internet |
| ----------- | ----- | ------- | ---- | ------- | ------ | -------- |
| External    | ✓     | ✗       | ✗    | ✗       | ✗      | -        |
| proxy       | ✓     | ✓       | ✗    | ✗       | ✗      | ✓        |
| backend     | ✗     | ✓       | ✓    | ✓       | ✗      | ✗        |
| data        | ✗     | ✗       | ✓    | ✓       | ✗      | ✗        |
| storage     | ✗     | ✗       | ✗    | ✓       | ✗      | ✗        |
| egress      | ✗     | ✗       | ✗    | ✗       | ✗\*    | ✓        |

\*ICC im Egress-Netzwerk deaktiviert – Container können über dieses Netzwerk nicht miteinander kommunizieren.

## Betriebliche Überlegungen

### Neue Services hinzufügen

Wenn Sie einen neuen Service hinzufügen, bestimmen Sie, welche Netzwerke dieser benötigt:

1. **Benötigt externen Zugriff (Ingress)?** → Zum `proxy` hinzufügen
2. **Ist es ein Anwendungs-Service?** → Zum `backend` hinzufügen
3. **Benötigt Datenbankzugriff?** → Zum `data` hinzufügen
4. **Benötigt Objektspeicher?** → Zum `storage` hinzufügen
5. **Benötigt nur ausgehenden Internetzugriff (kein Ingress)?** → Zum `egress` hinzufügen

Hinweis: Das `egress`-Netzwerk ist speziell für Services gedacht, die externe Websites/APIs erreichen müssen, aber nicht
von außen erreichbar sein sollten. Es hat ICC deaktiviert, sodass Services auf `egress` nicht miteinander kommunizieren
können – verwenden Sie `backend` für die Inter-Service-Kommunikation.

### Netzwerkprobleme debuggen

Wenn ein Service einen anderen Service nicht erreichen kann:

1. Überprüfen Sie, ob beide Services in einem gemeinsamen Netzwerk sind
2. Überprüfen Sie, ob das Zielnetzwerk als `internal: true` markiert ist
3. Verwenden Sie `docker network inspect <network>`, um verbundene Container anzuzeigen
4. Überprüfen Sie, ob die Service-Namen den DNS-Erwartungen entsprechen (container_name)

### Befehle zur Netzwerkprüfung

```bash
# List all networks
docker network ls

# Inspect a specific network
docker network inspect backend

# See which networks a container is connected to
docker inspect <container> --format '{{json .NetworkSettings.Networks}}'
```
