---
title: Netzwerksicherheit
source_sha: 644cb843fce4095dcc771ebce28ee7253546c6fd0b9fff56f28b688a53fb175a
---

# Netzwerksicherheit

Der AI-Hub verwendet eine mehrschichtige Netzwerksicherheit (Defense-in-Depth). Mehrere unabhängige Schichten schützen
die Plattform, ihre Daten und ihre Nutzer.

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
         ├── LLM Providers (Azure OpenAI, Google Gemini, OpenAI)
         ├── Azure Cognitive Services (AI Search, Document Intelligence, Speech)
         ├── Authentication (Microsoft Entra ID, Azure AD)
         ├── Jina AI (Web Search & Embeddings)
         └── Customer APIs (SharePoint, Confluence, Custom REST APIs)
```

## Sicherheitsschichten

Sicherheit wird in jeder Phase einer Anfrage angewendet, vom Netzwerkrand bis zur Anwendungslogik.

### Netzwerk-Firewall (NSG)

Die Network Security Group (NSG) oder Firewall erzwingt eine standardmäßige "Deny"-Richtlinie. Nur die Ports 80 (HTTP)
und 443 (HTTPS) sind aus dem öffentlichen Internet zugänglich. Alle anderen Ports sind blockiert. Sie können den
administrativen Zugriff wie SSH auf spezifische vertrauenswürdige IP-Bereiche beschränken.

### Reverse Proxy (Traefik)

Traefik dient als einziger Eintrittspunkt und sichert alle eingehenden Verbindungen. Er terminiert TLS (erfordert HTTPS
mit TLS 1.2+), provisioniert und erneuert automatisch Zertifikate über Let's Encrypt und injiziert Security-Header wie
HSTS und X-Frame-Options. Rate Limiting schützt Backend-Services vor Brute-Force- und einfachen DoS-Angriffen.

### Authentifizierung (IAM)

Azure AD OAuth2 übernimmt die Benutzerauthentifizierung und integriert sich in die Unternehmensidentität. Dies
ermöglicht Role-Based Access Control (RBAC) für fein granulierte Berechtigungen. API-Keys authentifizieren die
Service-zu-Service-Kommunikation. Das Session-Management mit konfigurierbaren Timeouts schützt Benutzersessions.

### Container-Isolation

Anwendungs-Services laufen als Nicht-Root-Benutzer in isolierten Docker-Containern mit minimalen Privilegien.
Container-Netzwerkregeln verhindern die direkte Kommunikation zwischen nicht verwandten Services. Ressourcengrenzen
mindern Ressourcenerschöpfungsangriffe. Images werden regelmäßig mit Sicherheitspatches aktualisiert.

### Netzwerksegmentierung

Die Plattform verwendet fünf isolierte Docker-Netzwerke (`proxy`, `backend`, `data`, `storage`, `egress`), um das
Prinzip der geringsten Rechte auf der Netzwerkebene durchzusetzen. Services werden nur den Netzwerken zugewiesen, die
sie benötigen:

- **Interne Netzwerke** (`backend`, `data`, `storage`) haben keinen externen Internetzugang.
- Das **Egress-Netzwerk** ermöglicht nur ausgehenden Internetzugang, wobei die Inter-Container Communication (ICC)
  deaktiviert ist.
- Services, die externe Websites durchsuchen müssen (z.B. Playwright), nutzen das `egress`-Netzwerk, ohne Ingress
  offenzulegen.

Siehe [Netzwerk-Isolation](../../2_architecture/4_network_isolation/) für detaillierte Netzwerktopologie und
Service-Zuweisungen.

### Datenschutz

Presidio erkennt und anonymisiert automatisch persönlich identifizierbare Informationen (PII) in LLM-Anfragen.
KI-gestützte Schutzmechanismen für sensible Informationen scannen Antworten, bevor sie an Benutzer ausgeliefert werden.
Ein Audit Trail protokolliert alle Datenzugriffe und -verarbeitungen.

## Verwandte Dokumentation

- [Netzwerk-Isolation](../../2_architecture/4_network_isolation/) – Docker-Netzwerkzonen und Service-Zuweisungen
- [Netzwerkanforderungen](../../3_deployment_guide/7_network_requirements/) – Firewall-Regeln und Konnektivität
- [Deployment-Optionen](../../3_deployment_guide/1_deployment_options/) – Architektur- und Hosting-Strategien
- [Container-Sicherheit](../3_container_security/) – Container-Isolation und -Härtung
- [Authentifizierung](../1_authentication/) – Authentifizierungsmechanismen
- [Eingabevalidierung](../2_input_validation/) – Eingabe-Sanitisierung und -Validierung
- [Infrastruktur-Schichten](../../2_architecture/2_infrastructure_layers/) – Überblick über Infrastrukturkomponenten
