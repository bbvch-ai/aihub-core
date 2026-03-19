---
title: Integrationen externer Systeme
source_sha: "a043435759e41d7d710aaa1182423e4065cc0c37ec455cc9da1d7ad9f522ef6b"
---

# Integrationen externer Systeme

Der Swiss AI Hub verbindet sich über vier Integrationsmuster mit externen Systemen.

## Integrationsansätze

### 1. Direkte Agenten-API-Aufrufe

Agents können externe APIs (REST, SOAP, GraphQL usw.) direkt aus ihren Workflow-Schritten mittels standardmäßiger Python HTTP-Bibliotheken wie `httpx` oder `aiohttp` aufrufen. Während der Ausführung tätigen Agents API-Aufrufe als Teil ihrer Logik, verarbeiten Antworten und integrieren die Ergebnisse in ihre Ausgaben.

Dies eignet sich gut für einfache API-Aufrufe mit einer einzigen Operation innerhalb von Agenten-Workflows. Ein Agent könnte während einer Konversation Kundendaten aus einem CRM abrufen, nach Benutzergenehmigung Formulardaten an ein externes Portal senden oder ein Ticketsystem abfragen, um Fragen zu beantworten. Das [Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) enthält Implementierungsmuster und Beispiele.

### 2. Plattform-API-Integration (externe Systeme rufen auf)

Externe Systeme können Swiss AI Hub Agents über die [Agent Interaction REST API](../18_api/2_agent_interaction_api/) triggern. Die API authentifiziert eingehende HTTP-Anfragen, übersetzt sie in interne Events und streamt Agenten-Antworten als strukturierte Ergebnisse zurück.

Dieser Ansatz eignet sich für bidirektionale Integrationen, bei denen externe Systeme KI-Funktionen triggern müssen. Ein Dokumentenportal könnte eine KI-Klassifizierung triggern, wenn Dateien hochgeladen werden, eine Webanwendung könnte KI-generierte Zusammenfassungen für ihr Dashboard anfordern, oder ein externes Workflow-System könnte Analyseaufgaben an KI-Agents delegieren.

### 3. Datenpipeline-Integration (Batch-Synchronisation)

[Daten-Pipelines](../6_pipelines/) synchronisieren kontinuierlich Daten aus externen Systemen in die Wissensdatenbanken des Swiss AI Hubs. Dagster-Pipelines verbinden sich mit externen Datenquellen, extrahieren und transformieren die Daten und laden sie dann in den Swiss AI Hub, wo sie für RAG (Retrieval-Augmented Generation) indiziert werden. Pipelines können nach Zeitplänen ausgeführt oder durch Events getriggert werden.

Dies deckt leseintensive Integrationen ab, bei denen die KI primär externe Daten analysiert, umfangreiche Dokumentenindizierung oder geplante Datensynchronisation von Unternehmenssystemen vorgenommen wird. Sie könnten SharePoint-Dokumente nächtlich in eine Wissensdatenbank synchronisieren, Support-Tickets kontinuierlich für die Trendanalyse erfassen oder Produktkataloge nach Zeitplan für Kundendienst-Agents importieren.

### 4. MCP-Integration (Entwicklungstools)

[Model Context Protocol (MCP)](../19_mcp/) ermöglicht es KI-Codierungsassistenten wie Claude Code, Gemini CLI und Cursor, während der Entwicklung mit dem Swiss AI Hub zu interagieren. Dies bietet eine schreibgeschützte Beobachtung des Plattformstatus für Entwicklungs- und Debugging-Workflows.

## Wahl des richtigen Ansatzes

| Ansatz                            | Latenz    | Richtung        | Komplexität | Am besten geeignet für                             |
| :-------------------------------- | :-------- | :-------------- | :---------- | :------------------------------------------------- |
| Direkte Agenten-API-Aufrufe       | Echtzeit  | Outbound        | Gering      | Einfache API-Aufrufe innerhalb der Agentenlogik    |
| Plattform-API-Integration         | Echtzeit  | Inbound         | Mittel      | Externe Systeme triggern KI                        |
| Datenpipeline-Integration         | Batch     | Inbound         | Mittel-Hoch | Groß angelegte Datensynchronisation, Wissensdatenbanken |
| MCP-Integration                   | Echtzeit  | Bidirektional   | Gering      | Nur für Entwicklungstools                          |

## Netzwerk- und Sicherheitsüberlegungen

### Outbound-Konnektivität (für direkte Agenten-API-Aufrufe und Pipelines)

Die Swiss AI Hub VM benötigt Outbound-HTTPS-Zugriff (Port 443) auf externe Systeme. Konfigurieren Sie Firewall-Regeln, um Outbound-Verbindungen zu spezifischen Endpunkten zu erlauben. Die Plattform unterstützt API-Schlüssel, OAuth-Tokens und zertifikatbasierte Authentifizierung. Alle externen Verbindungen verwenden verschlüsseltes HTTPS.

[Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) enthält weitere Details.

### Inbound-Konnektivität (für Plattform-API-Integration)

Externe Systeme verbinden sich mit dem Swiss AI Hub über standardmäßiges HTTPS (Port 443). Authentifizierungsoptionen umfassen OAuth 2.0, API-Schlüssel oder Azure AD-Integration. Traefik Reverse Proxy bietet integrierten Rate-Limiting-Schutz, und Let's Encrypt übernimmt die automatische Zertifikatsverwaltung für die TLS-Terminierung.

[Netzwerksicherheit](../20_security/4_network_security/) behandelt die Sicherheitsarchitektur.

## Allgemeine Integrationsprinzipien

Passen Sie Ihren Integrationsansatz an die Anforderungen hinsichtlich Latenz, Volumen und Richtung an. Deployen Sie den Swiss AI Hub in der Schweiz, wenn Sie Schweizer Datenresidenz benötigen. Nutzen Sie TLS-Verschlüsselung, RBAC und umfassendes Audit-Logging. Nutzen Sie Enterprise SSO über OAuth 2.0, SAML oder Azure AD. Konfigurieren Sie geeignete Firewall-Regeln für Inbound- und Outbound-Konnektivität. Befolgen Sie die [Schweizer Datenschutz-Richtlinien](../21_compliance/3_dsg/).

## Verwandte Dokumentation

- Agents: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) - Implementierung direkter API-Aufrufe
- API: [Agent Interaction REST API](../18_api/2_agent_interaction_api/) - HTTP-Schnittstelle der Plattform
- Pipelines: [Daten-Pipelines](../6_pipelines/) - Automatisierte Datensynchronisation
- MCP: [Model Context Protocol](../19_mcp/) - KI-Assistenten-Integration
- Netzwerk: [Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) - Firewall und Konnektivität
- Sicherheit: [Netzwerksicherheit](../20_security/4_network_security/) - Sicherheitsarchitektur
- Authentifizierung: [Authentifizierungs-Setup](../11_access_management/1_authentication_setup/) - SSO konfigurieren
