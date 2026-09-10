---
title: Netzwerksicherheit
source_sha: 2984c296f0ae3bd0076102bf4a50253bf0b7ae232877f428447259e8a12dd9b3
---

# Netzwerksicherheit

Der Swiss AI Hub nutzt eine mehrschichtige Netzwerksicherheit (Defense-in-Depth). Mehrere unabhängige Schichten schützen
die Plattform, ihre Daten und ihre Benutzer.

Alle internen Services (Swiss AI Hub API, Web UI, LiteLLM Proxy, Datenbanken) laufen in isolierten Docker-Containern auf
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
    ├── Swiss AI Hub API
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

Sicherheit wird in jeder Phase einer Anfrage angewendet, vom Netzwerkrand bis zur Anwendungslogik.

### Netzwerk-Firewall (NSG)

Die Network Security Group (NSG) oder Firewall erzwingt eine standardmäßige "Deny"-Richtlinie. Nur die Ports 80 (HTTP)
und 443 (HTTPS) sind aus dem öffentlichen Internet zugänglich. Alle anderen Ports sind blockiert. Sie können den
administrativen Zugriff wie SSH auf bestimmte vertrauenswürdige IP-Bereiche beschränken.

### Reverse Proxy (Traefik)

Traefik dient als einziger Eintrittspunkt und sichert alle eingehenden Verbindungen. Er terminiert TLS (erfordert HTTPS
mit TLS 1.2+), provisioniert und erneuert Zertifikate automatisch über Let's Encrypt und injiziert Sicherheits-Header
wie HSTS und X-Frame-Options. Rate Limiting schützt Backend-Services vor Brute-Force- und einfachen DoS-Angriffen.

### Authentifizierung (IAM)

Azure AD OAuth2 übernimmt die Benutzerauthentifizierung und integriert sich in die Unternehmensidentität. Dies
ermöglicht Role-Based Access Control (RBAC) für fein granulierte Berechtigungen. API-Keys authentifizieren die
Service-zu-Service-Kommunikation. Das Session-Management mit konfigurierbaren Timeouts schützt Benutzersessions.

### Container-Isolation

Anwendungs-Services laufen als Nicht-Root-Benutzer in isolierten Docker-Containern mit minimalen Privilegien.
Container-Netzwerkregeln verhindern die direkte Kommunikation zwischen nicht verwandten Services.
Ressourcenbeschränkungen mildern Angriffe durch Ressourcenerschöpfung. Images werden regelmäßig mit Sicherheitspatches
aktualisiert.

### Netzwerksegmentierung

Die Plattform verwendet fünf isolierte Docker-Netzwerke (`proxy`, `backend`, `data`, `storage`, `egress`), um das
Prinzip der geringsten Rechte auf der Netzwerkebene durchzusetzen. Services werden nur den Netzwerken zugewiesen, die
sie benötigen:

- **Interne Netzwerke** (`backend`, `data`, `storage`) haben keinen externen Internetzugang
- **Egress-Netzwerk** erlaubt nur ausgehenden Internetzugang, wobei die Inter-Container Communication (ICC) deaktiviert
  ist
- Services, die externe Websites durchsuchen müssen (z.B. Playwright), verwenden das `egress`-Netzwerk, ohne Ingress
  offenzulegen

Siehe [Netzwerk-Isolation](../../2_architecture/4_network_isolation/) für detaillierte Netzwerktopologie und
Service-Zuweisungen.

### Datenschutz

Presidio erkennt und anonymisiert automatisch persönlich identifizierbare Informationen (PII) in LLM-Anfragen.
KI-gestützte Schutzvorrichtungen für sensible Informationen scannen Antworten, bevor sie an Benutzer übermittelt werden.
Ein Audit-Trail protokolliert alle Datenzugriffe und -verarbeitungen.

## Zugehörige Dokumentation

- [Netzwerk-Isolation](../../2_architecture/4_network_isolation/) – Docker-Netzwerkzonen und Service-Zuweisungen
- [Netzwerkanforderungen](../../3_deployment_guide/7_network_requirements/) – Firewall-Regeln und Konnektivität
- [Deployment-Optionen](../../3_deployment_guide/1_deployment_options/) – Architektur- und Hosting-Strategien
- [Container-Sicherheit](../3_container_security/) – Container-Isolation und -Härtung
- [Authentifizierung](../1_authentication/) – Authentifizierungsmechanismen
- [Eingabevalidierung](../2_input_validation/) – Eingabebereinigung und -validierung
- [Infrastrukturschichten](../../../1_vision_and_positioning/4_infrastructure_layers/) – Überblick über
  Infrastrukturkomponenten
