````yaml
---
title: Docker-Netzwerk-Isolation
source_sha: "536d4d5f2fa4f10830c3cbffaf13201789cffcb7c9ad57182c9cdaa6f661ec7f"
---

# Docker-Netzwerk-Isolation

Die Swiss AI Hub Plattform implementiert Netzwerksegmentierung, um Sicherheitsgrenzen zwischen Services durchzusetzen. Dieser
Defense-in-Depth-Ansatz begrenzt den Explosionsradius potenzieller Sicherheitsverletzungen und setzt das Prinzip der
geringsten Rechte auf der Netzwerkebene durch.

## Netzwerkzonen

Die Plattform verwendet fünf isolierte Docker-Netzwerke:

| Netzwerk  | Zweck                             | Externer Zugriff   | ICC aktiviert |
| --------- | --------------------------------- | ------------------ | ------------- |
| `proxy`   | Externer Traffic über Traefik     | Ingress + Egress   | Ja            |
| `backend` | Interne Applikations-Services     | Nein               | Ja            |
| `data`    | Datenbanken und Message Broker    | Nein               | Ja            |
| `storage` | SeaweedFS Objekt-Storage          | Nein               | Ja            |
| `egress`  | Nur ausgehender Internetzugriff   | Nur Egress         | Nein          |

Das `egress`-Netzwerk ist für Services konzipiert, die das Internet erreichen müssen (ausgehend), aber nicht aus dem
Internet erreichbar sein sollten (kein Ingress). Inter-Container-Kommunikation (ICC) ist in diesem Netzwerk
deaktiviert, was bedeutet, dass Container über dieses Netzwerk nicht miteinander kommunizieren können – sie können es
nur für ausgehenden Internetzugriff nutzen.

## Service-Netzwerk-Zuweisungen

Jeder Service wird nur den Netzwerken zugewiesen, die er für den Betrieb benötigt:

### Proxy-Netzwerk-Services

Services, die von außerhalb des Docker-Netzwerks zugänglich sind:

- **traefik**: Reverse Proxy und API-Gateway
- **api**: REST-API- und WebSocket-Endpunkte
- **web**: Admin-UI-Frontend
- **open-webui**: Chat-Oberfläche
- **bot**: MS Teams/Slack-Integration
- **seaweedfs-s3**: S3-kompatible Storage-API
- **oauth2proxy-**\*: Authentifizierungs-Proxys

### Backend-Netzwerk-Services

Interne Applikations- und Verarbeitungs-Services:

- **litellm**: LLM-Gateway und Request-Routing
- **mineru-api**: Dokumenten-Parsing und -Extraktion
- **presidio-analyzer/anonymizer**: PII-Erkennung und -Anonymisierung
- **vLLM**: Lokale LLM-Inferenz (Chat, Embedding, Reranking) — nur GPU-Deployments
- **speaches**: Sprach-zu-Text und Text-zu-Sprache
- **jupyter**: Code-Ausführungsumgebung
- **playwright**: Web Scraping und Automation (auch im `egress`-Netzwerk für Internetzugriff)
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
- **etcd**: Verteilter Schlüssel-Wert-Speicher (Milvus-Metadaten)
- **valkey**: Redis-kompatibler In-Memory-Cache
- **nats**: Message Broker für ereignisgesteuerte Kommunikation

### Storage-Netzwerk-Services

Verteilter Objekt-Storage-Cluster:

- **seaweedfs-master**: Cluster-Koordinator
- **seaweedfs-volume**: Datenspeicher-Nodes
- **seaweedfs-filer**: Dateisystem-Schnittstelle
- **seaweedfs-s3**: S3-API-Gateway
- **etcd**: Filer-Metadaten-Backend

### Egress-Netzwerk-Services

Services, die ausgehenden Internetzugriff, aber keinen eingehenden Zugriff benötigen:

- **playwright**: Web Scraping und Browser-Automation (muss Webseiten abrufen)

Dieses Netzwerk hat ICC (Inter-Container-Kommunikation) deaktiviert, wodurch laterale Bewegung zwischen Containern in
diesem Netzwerk verhindert wird. Services nutzen `egress` ausschließlich für ausgehenden Internetzugriff und müssen
andere Netzwerke (z.B. `backend`) für die Inter-Service-Kommunikation nutzen.

## Netzwerk-Topologie

```mermaid
flowchart TB
    subgraph Internet
        ext[Externer Traffic]
        websites[Externe Websites]
    end

    subgraph proxy[PROXY-NETZWERK]
        traefik[traefik]
        api[api]
        web[web]
        openwebui[open-webui]
        bot[bot]
        s3proxy[seaweedfs-s3]
    end

    subgraph backend[BACKEND-NETZWERK]
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

    subgraph egress[EGRESS-NETZWERK - ICC Deaktiviert]
        playwright_egress[playwright]
    end

    subgraph data[DATEN-NETZWERK]
        postgres[postgres]
        ferretdb[ferretdb]
        neo4j[neo4j]
        milvus[milvus]
        valkey[valkey]
        nats[nats]
        etcd[etcd]
    end

    subgraph storage[STORAGE-NETZWERK]
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

    playwright_egress -->|nur ausgehend| websites
````

## Sicherheitsimplikationen

### Was jede Netzwerkgrenze schützt

**Proxy → Backend-Grenze**

- Externe Benutzer können nicht direkt auf interne Verarbeitungs-Services zugreifen
- Ein kompromittierter Traefik kann Datenbanken nicht erreichen, ohne die API zu durchlaufen

**Backend → Daten-Grenze**

- Verarbeitungs-Services greifen über definierte Schnittstellen auf Datenbanken zu
- Ein kompromittierter KI-Service kann andere Datenbanken nicht direkt manipulieren

**Daten → Storage-Grenze**

- Die interne SeaweedFS-Cluster-Kommunikation ist isoliert
- Datenbank-Services können Storage-Operationen nicht stören

### Service-Sichtbarkeitsmatrix

| Von \\ Nach | proxy | backend | data | storage | egress | Internet |
| ----------- | ----- | ------- | ---- | ------- | ------ | -------- |
| Extern      | ✓     | ✗       | ✗    | ✗       | ✗      | -        |
| proxy       | ✓     | ✓       | ✗    | ✗       | ✗      | ✓        |
| backend     | ✗     | ✓       | ✓    | ✓       | ✗      | ✗        |
| data        | ✗     | ✗       | ✓    | ✓       | ✗      | ✗        |
| storage     | ✗     | ✗       | ✗    | ✓       | ✗      | ✗        |
| egress      | ✗     | ✗       | ✗    | ✗       | ✗\*    | ✓        |

\*ICC im Egress-Netzwerk deaktiviert - Container können über dieses Netzwerk nicht miteinander kommunizieren.

## Betriebliche Überlegungen

### Neue Services hinzufügen

Wenn Sie einen neuen Service hinzufügen, bestimmen Sie, welche Netzwerke er benötigt:

1. **Benötigt externen Zugriff (Ingress)?** → Fügen Sie es zu `proxy` hinzu
2. **Ist ein Applikations-Service?** → Fügen Sie es zu `backend` hinzu
3. **Benötigt Datenbankzugriff?** → Fügen Sie es zu `data` hinzu
4. **Benötigt Objekt-Storage?** → Fügen Sie es zu `storage` hinzu
5. **Benötigt nur ausgehenden Internetzugriff (kein Ingress)?** → Fügen Sie es zu `egress` hinzu

Hinweis: Das `egress`-Netzwerk ist speziell für Services gedacht, die externe Websites/APIs erreichen müssen, aber nicht
von außen erreichbar sein sollten. Es hat ICC deaktiviert, sodass Services auf `egress` nicht miteinander kommunizieren
können – nutzen Sie `backend` für die Inter-Service-Kommunikation.

### Netzwerkprobleme debuggen

Wenn ein Service einen anderen Service nicht erreichen kann:

1. Verifizieren Sie, dass beide Services in einem gemeinsamen Netzwerk sind
2. Überprüfen Sie, ob das Zielnetzwerk als `internal: true` markiert ist
3. Verwenden Sie `docker network inspect <network>`, um verbundene Container zu sehen
4. Überprüfen Sie, ob die Service-Namen den DNS-Erwartungen entsprechen (container_name)

### Netzwerk-Inspektionsbefehle

```bash
# Alle Netzwerke auflisten
docker network ls

# Ein bestimmtes Netzwerk inspizieren
docker network inspect backend

# Anzeigen, mit welchen Netzwerken ein Container verbunden ist
docker inspect <container> --format '{{json .NetworkSettings.Networks}}'
```
