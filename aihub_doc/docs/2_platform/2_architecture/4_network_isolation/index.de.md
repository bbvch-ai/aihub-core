---
title: Docker-Netzwerkisolation
source_sha: "38efec0d96aee1a4529469d6c990a16fc6152e1d29e60930a05c28cceeeb8416"
---

# Docker-Netzwerkisolation

Die AI-Hub Plattform implementiert Netzwerksegmentierung, um Sicherheitsgrenzen zwischen Services durchzusetzen. Dieser Defense-in-Depth-Ansatz begrenzt den "Blast Radius" potenzieller Sicherheitsverletzungen und erzwingt das Prinzip der geringsten Rechte auf der Netzwerkebene.

## Netzwerkzonen

Die Plattform verwendet fünf isolierte Docker-Netzwerke:

| Netzwerk  | Zweck                             | Externer Zugriff | ICC aktiviert |
| --------- | --------------------------------- | ---------------- | ------------- |
| `proxy`   | Externer Traffic über Traefik     | Ingress + Egress | Ja            |
| `backend` | Interne Anwendungs-Services       | Nein             | Ja            |
| `data`    | Datenbanken und Message Broker    | Nein             | Ja            |
| `storage` | SeaweedFS Objekt-Speicher         | Nein             | Ja            |
| `egress`  | Nur ausgehender Internetzugriff   | Egress only      | Nein          |

Das `egress`-Netzwerk ist für Services konzipiert, die das Internet erreichen müssen (ausgehend), aber nicht aus dem Internet erreichbar sein sollen (kein Ingress). Die Inter-Container-Kommunikation (ICC) ist in diesem Netzwerk deaktiviert, was bedeutet, dass Container über dieses Netzwerk nicht miteinander kommunizieren können – sie können es nur für den ausgehenden Internetzugriff nutzen.

## Service-Netzwerkzuweisungen

Jeder Service wird nur den Netzwerken zugewiesen, die er für den Betrieb benötigt:

### Proxy-Netzwerk-Services

Services, die von außerhalb des Docker-Netzwerks zugänglich sind:

- **traefik**: Reverse Proxy und API-Gateway
- **api**: REST-API- und WebSocket-Endpunkte
- **web**: Admin-UI-Frontend
- **open-webui**: Chat-Interface
- **bot**: MS Teams/Slack-Integration
- **seaweedfs-s3**: S3-kompatible Speicher-API
- **oauth2proxy-**\*: Authentifizierungs-Proxys

### Backend-Netzwerk-Services

Interne Anwendungs- und Verarbeitungs-Services:

- **litellm**: LLM-Gateway und Anfrage-Routing
- **mineru-api**: Dokumenten-Parsing und -Extraktion
- **presidio-analyzer/anonymizer**: PII-Erkennung und -Anonymisierung
- **llama-cpp-**\*: Lokale LLM-Inferenz (Chat, Embedding, Reranking)
- **speaches**: Speech-to-Text und Text-to-Speech
- **jupyter**: Code-Ausführungsumgebung
- **playwright**: Web-Scraping und Automatisierung (auch im `egress`-Netzwerk für Internetzugriff)
- **agents**: Alle Agent-Worker (RAG, Expert, Wrapping)
- **pipelines**: Datenverarbeitungs-Pipelines
- **dagster-**\*: Pipeline-Orchestrierung
- **phoenix**: KI-Observability
- **otel-collector**: Telemetrie-Aggregation

### Daten-Netzwerk-Services

Persistenz- und Messaging-Infrastruktur:

- **postgres**: Primäre PostgreSQL-Datenbank
- **pgbouncer**: Connection Pooler für Dagster
- **postgres-ferretdb**: PostgreSQL-Backend für FerretDB
- **ferretdb**: MongoDB-kompatibler Dokumentenspeicher
- **neo4j**: Graphdatenbank für Mem0-Speicher
- **milvus-standalone**: Vektordatenbank
- **etcd**: Verteiltes Schlüssel-Wert-Speicher (Milvus-Metadaten)
- **valkey**: Redis-kompatibler In-Memory-Cache
- **nats**: Message Broker für ereignisgesteuerte Kommunikation

### Speicher-Netzwerk-Services

Verteilter Objekt-Speicher-Cluster:

- **seaweedfs-master**: Cluster-Koordinator
- **seaweedfs-volume**: Daten-Speicherknoten
- **seaweedfs-filer**: Dateisystem-Interface
- **seaweedfs-s3**: S3-API-Gateway
- **etcd**: Filer-Metadaten-Backend

### Egress-Netzwerk-Services

Services, die ausgehenden Internetzugriff, aber keinen eingehenden Zugriff benötigen:

- **playwright**: Web-Scraping und Browser-Automatisierung (muss Webseiten abrufen)

Dieses Netzwerk hat ICC (Inter-Container-Kommunikation) deaktiviert, wodurch die horizontale Bewegung zwischen Containern in diesem Netzwerk verhindert wird. Services nutzen `egress` ausschließlich für den ausgehenden Internetzugriff und müssen andere Netzwerke (z.B. `backend`) für die Inter-Service-Kommunikation verwenden.

## Netzwerktopologie

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
        llama[llama-cpp-*]
        agents[agents]
        jupyter[jupyter]
        playwright[playwright]
        dagster[dagster-*]
        pipelines[pipelines]
        phoenix[phoenix]
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
    phoenix --> postgres
    litellm --> postgres

    milvus --> etcd
    milvus --> s3proxy
    swfiler --> etcd
    s3proxy --> swfiler
    swfiler --> swvolume
    swvolume --> swmaster

    playwright_egress -->|outbound only| websites
```

## Sicherheitsaspekte

### Was jede Netzwerkgrenze schützt

**Proxy → Backend-Grenze**

- Externe Benutzer können nicht direkt auf interne Verarbeitungs-Services zugreifen
- Ein kompromittierter Traefik kann Datenbanken nicht erreichen, ohne die API zu durchlaufen

**Backend → Daten-Grenze**

- Verarbeitungs-Services greifen über definierte Schnittstellen auf Datenbanken zu
- Ein kompromittierter KI-Service kann andere Datenbanken nicht direkt manipulieren

**Daten → Speicher-Grenze**

- Die interne Cluster-Kommunikation von SeaweedFS ist isoliert
- Datenbank-Services können Speicheroperationen nicht beeinträchtigen

### Service-Sichtbarkeitsmatrix

| Von \\ Nach | proxy | backend | data | storage | egress | Internet |
| ----------- | ----- | ------- | ---- | ------- | ------ | -------- |
| Extern      | ✓     | ✗       | ✗    | ✗       | ✗      | -        |
| proxy       | ✓     | ✓       | ✗    | ✗       | ✗      | ✓        |
| backend     | ✗     | ✓       | ✓    | ✓       | ✗      | ✗        |
| data        | ✗     | ✗       | ✓    | ✓       | ✗      | ✗        |
| storage     | ✗     | ✗       | ✗    | ✓       | ✗      | ✗        |
| egress      | ✗     | ✗       | ✗    | ✗       | ✗\*    | ✓        |

\*ICC im egress-Netzwerk deaktiviert – Container können über dieses Netzwerk nicht miteinander kommunizieren.

## Betriebliche Überlegungen

### Neue Services hinzufügen

Beim Hinzufügen eines neuen Services legen Sie fest, welche Netzwerke er benötigt:

1. **Benötigt externen Zugriff (Ingress)?** → Zum `proxy`-Netzwerk hinzufügen
2. **Ist es ein Anwendungs-Service?** → Zum `backend`-Netzwerk hinzufügen
3. **Benötigt Datenbankzugriff?** → Zum `data`-Netzwerk hinzufügen
4. **Benötigt Objekt-Speicher?** → Zum `storage`-Netzwerk hinzufügen
5. **Benötigt nur ausgehenden Internetzugriff (kein Ingress)?** → Zum `egress`-Netzwerk hinzufügen

Hinweis: Das `egress`-Netzwerk ist speziell für Services gedacht, die externe Websites/APIs erreichen müssen, aber nicht von außen erreichbar sein sollen. Es hat ICC deaktiviert, sodass Services im `egress`-Netzwerk nicht miteinander kommunizieren können – verwenden Sie `backend` für die Inter-Service-Kommunikation.

### Fehlerbehebung bei Netzwerkproblemen

Wenn ein Service einen anderen Service nicht erreichen kann:

1. Verifizieren Sie, dass beide Services in einem gemeinsamen Netzwerk sind
2. Prüfen Sie, ob das Zielnetzwerk als `internal: true` markiert ist
3. Verwenden Sie `docker network inspect <network>`, um verbundene Container anzuzeigen
4. Prüfen Sie, ob die Service-Namen den DNS-Erwartungen entsprechen (container_name)

### Befehle zur Netzwerkprüfung

```bash
# List all networks
docker network ls

# Inspect a specific network
docker network inspect backend

# See which networks a container is connected to
docker inspect <container> --format '{{json .NetworkSettings.Networks}}'
```
