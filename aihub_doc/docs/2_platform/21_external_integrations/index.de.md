---
title: Integrationen externer Systeme
source_sha: ac57ad09fe918870a99031747fecc5701c9dfbaeacf965943d62f715e5c5fcef
---

# Integrationen externer Systeme

Der Schweizer AI-Hub verbindet sich über vier Integrationsmuster mit externen Systemen.

## Integrationsansätze

### 1. Direkte Agenten-API-Aufrufe

Agenten können externe APIs (REST, SOAP, GraphQL usw.) direkt aus ihren Workflow-Schritten heraus mithilfe
standardmäßiger Python-HTTP-Bibliotheken wie `httpx` oder `aiohttp` aufrufen. Während der Ausführung tätigen Agenten
API-Aufrufe als Teil ihrer Logik, verarbeiten Antworten und integrieren die Ergebnisse in ihre Ausgaben.

Dies eignet sich gut für einfache API-Aufrufe mit einer einzigen Operation innerhalb von Agenten-Workflows. Ein Agent
könnte während einer Konversation Kundendaten aus einem CRM abrufen, Formulardaten nach Benutzerzustimmung an ein
externes Portal übermitteln oder ein Ticketsystem abfragen, um Fragen zu beantworten. Das
[Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) enthält Implementierungsmuster
und Beispiele.

### 2. Plattform-API-Integration (Aufrufe von externen Systemen)

Externe Systeme können AI-Hub Agenten über die [Agent Interaction REST API](../17_api/) auslösen. Die API
authentifiziert eingehende HTTP-Anfragen, übersetzt sie in interne Ereignisse und streamt Agenten-Antworten als
strukturierte Ergebnisse zurück.

Dieser Ansatz eignet sich für bidirektionale Integrationen, bei denen externe Systeme KI-Funktionen auslösen müssen. Ein
Dokumentenportal könnte eine KI-Klassifizierung auslösen, wenn Dateien hochgeladen werden, eine Webanwendung könnte
KI-generierte Zusammenfassungen für ihr Dashboard anfordern, oder ein externes Workflow-System könnte Analyseaufgaben an
KI-Agenten delegieren.

### 3. Datenpipeline-Integration (Stapel-Synchronisierung)

[Daten-Pipelines](../6_pipelines/) synchronisieren kontinuierlich Daten von externen Systemen in die AI-Hub
Wissensdatenbanken. Dagster Pipelines verbinden sich mit externen Datenquellen, extrahieren und transformieren die Daten
und laden sie dann in den AI-Hub, wo sie für RAG (Retrieval-Augmented Generation) indiziert werden. Pipelines können
nach Zeitplänen laufen oder durch Ereignisse ausgelöst werden.

Dies deckt leseintensive Integrationen ab, bei denen die KI hauptsächlich externe Daten analysiert, großflächige
Dokumentenindizierung oder geplante Datensynchronisierung aus Unternehmenssystemen. Sie könnten SharePoint-Dokumente
nächtlich in eine Wissensdatenbank synchronisieren, kontinuierlich Support-Tickets für Trendanalysen erfassen oder
Produktkataloge nach Zeitplan für Kundendienstmitarbeiter importieren.

### 4. MCP-Integration (Entwicklungstools)

Das [Model Context Protocol (MCP)](../18_mcp/) ermöglicht es KI-Codierungsassistenten wie Claude Code, Gemini CLI und
Cursor, während der Entwicklung mit dem AI-Hub zu interagieren. Dies bietet eine schreibgeschützte Beobachtung des
Plattformzustands für Entwicklungs- und Debugging-Workflows.

## Wahl des richtigen Ansatzes

| Ansatz                      | Latenz   | Richtung      | Komplexität | Am besten geeignet für                          |
| :-------------------------- | :------- | :------------ | :---------- | :---------------------------------------------- |
| Direkte Agenten-API-Aufrufe | Echtzeit | Ausgehend     | Niedrig     | Einfache API-Aufrufe innerhalb der Agentenlogik |
| Plattform-API-Integration   | Echtzeit | Eingehend     | Mittel      | Externe Systeme, die KI auslösen                |
| Datenpipeline-Integration   | Stapel   | Eingehend     | Mittel-Hoch | Große Datensynchronisierung, Wissensdatenbanken |
| MCP-Integration             | Echtzeit | Bidirektional | Niedrig     | Nur Entwicklungstools                           |

## Netzwerk- und Sicherheitsaspekte

### Ausgehende Konnektivität (für direkte Agenten-API-Aufrufe und Pipelines)

Die AI-Hub VM benötigt ausgehenden HTTPS-Zugriff (Port 443) auf externe Systeme. Konfigurieren Sie Firewall-Regeln, um
ausgehende Verbindungen zu bestimmten Endpunkten zu erlauben. Die Plattform unterstützt API-Schlüssel, OAuth-Tokens und
zertifikatsbasierte Authentifizierung. Alle externen Verbindungen verwenden verschlüsseltes HTTPS.

[Netzwerkanforderungen](../3_deployment_guide/) enthält weitere Details.

### Eingehende Konnektivität (für Plattform-API-Integration)

Externe Systeme verbinden sich mit dem AI-Hub über Standard-HTTPS (Port 443). Authentifizierungsoptionen umfassen OAuth
2.0, API-Schlüssel oder Azure AD-Integration. Der Traefik Reverse Proxy bietet integrierten Rate-Limiting-Schutz, und
Let's Encrypt übernimmt die automatische Zertifikatsverwaltung für die TLS-Terminierung.

[Netzwerksicherheit](../19_security/) behandelt die Sicherheitsarchitektur.

## Allgemeine Integrationsprinzipien

Passen Sie Ihren Integrationsansatz an die Anforderungen an Latenz, Volumen und Richtung an. Deployen Sie den AI-Hub in
der Schweiz, wenn Sie Schweizer Datenresidenz benötigen. Verwenden Sie TLS-Verschlüsselung, RBAC und umfassende
Audit-Protokollierung. Nutzen Sie Enterprise SSO über OAuth 2.0, SAML oder Azure AD. Konfigurieren Sie entsprechende
Firewall-Regeln für eingehende und ausgehende Konnektivität. Befolgen Sie die
[Schweizer Datenschutzrichtlinien](../20_compliance/).

## Zugehörige Dokumentation

- Agents: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) – Implementierung
  direkter API-Aufrufe
- API: [Agent Interaction REST API](../17_api/) – Plattform-HTTP-Schnittstelle
- Pipelines: [Daten-Pipelines](../6_pipelines/) – Automatisierte Datensynchronisierung
- MCP: [Model Context Protocol](../18_mcp/) – KI-Assistenten-Integration
- Network: [Netzwerkanforderungen](../3_deployment_guide/) – Firewall und Konnektivität
- Security: [Netzwerksicherheit](../19_security/) – Sicherheitsarchitektur
- Authentication: [Authentication Setup](../11_access_management/) – SSO konfigurieren
