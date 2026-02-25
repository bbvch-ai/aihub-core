---
title: Netzwerksicherheit
source_sha: 8718c031f06d37bc10bf2aa0c905175f054e7ad5034186a09d4e960d2f06035a
---

# Netzwerksicherheit

Der AI-Hub nutzt eine gestaffelte Netzwerksicherheit (Defense-in-Depth). Mehrere unabhängige Schichten schützen die
Plattform, ihre Daten und ihre Benutzer.

Alle internen Services (AI-Hub API, Web UI, LiteLLM Proxy, Datenbanken) laufen in isolierten Docker-Containern in
privaten Netzwerken. Der Traefik Reverse Proxy ist die einzige Komponente, die aus dem Internet zugänglich ist und
öffentlichen Traffic auf den Ports 80 und 443 akzeptiert.

Traefik leitet Anfragen an den korrekten internen Service weiter. Backend-Services bleiben isoliert und werden niemals
direkt dem öffentlichen Internet ausgesetzt.

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
         ├── LLM Providers (Swiss LLM Cloud, or local vLLM for GPU deployments)
         ├── Authentication (Microsoft Entra ID, Azure AD)
         ├── Jina AI (Web Search & Embeddings)
         └── Customer APIs (SharePoint, Confluence, Custom REST APIs)
```

## Sicherheitsschichten

Sicherheit gilt in jeder Phase einer Anfrage, vom Netzwerkrand bis zur Anwendungslogik.

### Netzwerk-Firewall (NSG)

Die Network Security Group (NSG) oder Firewall erzwingt eine standardmäßige Ablehnungsrichtlinie (Default-Deny-Policy).
Nur die Ports 80 (HTTP) und 443 (HTTPS) sind aus dem öffentlichen Internet zugänglich. Alle anderen Ports sind
blockiert. Sie können den administrativen Zugriff wie SSH auf bestimmte vertrauenswürdige IP-Bereiche beschränken.

### Reverse Proxy (Traefik)

Traefik dient als einziger Entry Point und sichert alle eingehenden Verbindungen. Es terminiert TLS (erfordert HTTPS mit
TLS 1.2+), provisioniert und erneuert automatisch Zertifikate über Let's Encrypt und fügt Sicherheits-Header wie HSTS
und X-Frame-Options ein. Rate Limiting schützt Backend-Services vor Brute-Force- und einfachen DoS-Angriffen.

### Authentifizierung (IAM)

Azure AD OAuth2 handhabt die Benutzerauthentifizierung und integriert sich mit der Unternehmensidentität. Dies
ermöglicht die rollenbasierte Zugriffskontrolle (RBAC) für fein abgestufte Berechtigungen. API-Keys authentifizieren die
Service-zu-Service-Kommunikation. Das Session Management mit konfigurierbaren Timeouts schützt Benutzersessions.

### Container-Isolation

Anwendungs-Services laufen als Nicht-Root-Benutzer in isolierten Docker-Containern mit minimalen Privilegien.
Container-Netzwerkregeln verhindern die direkte Kommunikation zwischen nicht zusammengehörigen Services.
Ressourcenlimits mindern Angriffe durch Ressourcenauslastung. Images werden regelmäßig mit Sicherheitspatches
aktualisiert.

### Netzwerksegmentierung

Die Plattform verwendet fünf isolierte Docker-Netzwerke (`proxy`, `backend`, `data`, `storage`, `egress`), um das
Prinzip der geringsten Rechte auf der Netzwerkschicht durchzusetzen. Services werden nur den Netzwerken zugewiesen, die
sie benötigen:

- **Interne Netzwerke** (`backend`, `data`, `storage`) haben keinen externen Internetzugang
- **Egress-Netzwerk** ermöglicht nur ausgehenden Internetzugang, wobei die Inter-Container Communication (ICC)
  deaktiviert ist
- Services, die externe Websites durchsuchen müssen (z.B. Playwright), nutzen das `egress`-Netzwerk, ohne Ingress
  preiszugeben

Siehe [Netzwerk-Isolation](../../2_architecture/4_network_isolation/) für detaillierte Netzwerktopologie und
Service-Zuweisungen.

### Datenschutz

Presidio erkennt und anonymisiert automatisch persönlich identifizierbare Informationen (PII) in LLM-Anfragen.
KI-gestützte Schutzmechanismen für sensible Informationen scannen Antworten vor der Zustellung an Benutzer. Ein
Audit-Trail protokolliert alle Datenzugriffe und -verarbeitungen.

## Verwandte Dokumentation

- [Netzwerk-Isolation](../../2_architecture/4_network_isolation/) - Docker-Netzwerkzonen und Service-Zuweisungen
- [Netzwerkanforderungen](../../3_deployment_guide/7_network_requirements/) - Firewall-Regeln und Konnektivität
- [Deployment-Optionen](../../3_deployment_guide/1_deployment_options/) - Architektur- und Hosting-Strategien
- [Container-Sicherheit](../3_container_security/) - Container-Isolation und -Härtung
- [Authentifizierung](../1_authentication/) - Authentifizierungsmechanismen
- [Eingabevalidierung](../2_input_validation/) - Eingabebereinigung und -validierung
- [Infrastruktur-Schichten](../../2_architecture/2_infrastructure_layers/) - Übersicht der Infrastrukturkomponenten
