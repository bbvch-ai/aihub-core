---
title: Netzwerksicherheit
source_sha: 9fe3e1f6d044766ebae9d338dc46aa2bae0d78d0c6328f427372389202c19854
---

# Netzwerksicherheit

Der AI-Hub verwendet eine mehrschichtige Netzwerksicherheit ("Defense-in-Depth"). Mehrere unabhängige Schichten schützen
die Plattform, ihre Daten und ihre Benutzer.

Alle internen Services (AI-Hub API, Web UI, LiteLLM Proxy, Datenbanken) laufen in isolierten Docker-Containern in
privaten Netzwerken. Der Traefik Reverse Proxy ist die einzige Komponente, die aus dem Internet zugänglich ist und
öffentlichen Traffic auf den Ports 80 und 443 annimmt.

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

Die Netzwerksicherheitsgruppe (NSG) oder Firewall erzwingt eine standardmäßige Ablehnungsrichtlinie (Default Deny
Policy). Nur die Ports 80 (HTTP) und 443 (HTTPS) sind aus dem öffentlichen Internet zugänglich. Alle anderen Ports sind
blockiert. Sie können den administrativen Zugriff wie SSH auf bestimmte vertrauenswürdige IP-Bereiche beschränken.

### Reverse Proxy (Traefik)

Traefik dient als einziger Entry Point und sichert alle eingehenden Verbindungen. Es terminiert TLS (erfordert HTTPS mit
TLS 1.2+), provisioniert und erneuert Zertifikate automatisch über Let's Encrypt und fügt Sicherheits-Header wie HSTS
und X-Frame-Options ein. Rate Limiting schützt Backend-Services vor Brute-Force- und einfachen DoS-Angriffen.

### Authentifizierung (IAM)

Azure AD OAuth2 übernimmt die Benutzerauthentifizierung und integriert sich in die Unternehmensidentität. Dies
ermöglicht eine rollenbasierte Zugriffskontrolle (RBAC) für detaillierte Berechtigungen. API-Keys authentifizieren die
Service-zu-Service-Kommunikation. Die Session-Verwaltung mit konfigurierbaren Timeouts schützt Benutzersessions.

### Container-Isolation

Anwendungsdienste laufen als Nicht-Root-Benutzer in isolierten Docker-Containern mit minimalen Rechten.
Container-Netzwerkregeln verhindern die direkte Kommunikation zwischen nicht verwandten Diensten. Ressourcenlimits
mildern Angriffe durch Ressourcenerschöpfung. Images werden regelmäßig mit Sicherheitspatches aktualisiert.

### Datenschutz

Presidio erkennt und anonymisiert automatisch persönlich identifizierbare Informationen (PII) in LLM-Anfragen.
KI-gestützte Schutzmechanismen für sensible Informationen scannen Antworten, bevor sie an Benutzer ausgeliefert werden.
Ein Audit-Trail protokolliert alle Datenzugriffe und -verarbeitungen.

## Verwandte Dokumentation

- [Netzwerkanforderungen](../../3_deployment_guide/7_network_requirements/) – Firewall-Regeln und Konnektivität
- [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) – Architektur und Hosting-Strategien
- [Container-Sicherheit](../3_container_security/) – Container-Isolation und -Härtung
- [Authentifizierung](../1_authentication/) – Authentifizierungsmechanismen
- [Eingabevalidierung](../2_input_validation/) – Eingabebereinigung und -validierung
- [Infrastrukturschichten](../../2_architecture/2_infrastructure_layers/) – Übersicht der Infrastrukturkomponenten
