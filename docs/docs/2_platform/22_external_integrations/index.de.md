---
title: Integrationen mit externen Systemen
source_sha: fe6e4d1e999397d0c0d53be3ddacdf5dff51c270cb5d0f4f05feb6f2d0c2902e
---

# Integrationen mit externen Systemen

Der Swiss AI Hub verbindet sich mit externen Systemen über vier Integrationsmuster.

## Integrationsansätze

### 1. Direkte Agenten-API-Aufrufe

Agents können externe APIs (REST, SOAP, GraphQL usw.) direkt aus ihren Workflow-Schritten mittels standardmäßiger Python
HTTP-Bibliotheken wie `httpx` oder `aiohttp` aufrufen. Während der Ausführung tätigen Agents API-Aufrufe als Teil ihrer
Logik, verarbeiten Antworten und integrieren die Ergebnisse in ihre Ausgaben.

Dies funktioniert gut für einfache API-Aufrufe mit Einzeloperationen innerhalb von Agenten-Workflows. Ein Agent könnte
während eines Gesprächs Kundendaten aus einem CRM abrufen, Formulardaten nach Benutzergenehmigung an ein externes Portal
übermitteln oder ein Ticketsystem abfragen, um Fragen zu beantworten. Das
[Agent Developer README](https://github.com/bbvch-ai/swiss-ai-hub/tree/main/aihub_agent) enthält Implementierungsmuster
und Beispiele.

### 2. Plattform-API-Integration (externe Systeme rufen auf)

Externe Systeme können Swiss AI Hub Agents über die
[Agent Interaction REST API](/de/docs/18_api/2_agent_interaction_api/) triggern. Die API authentifiziert eingehende
HTTP-Anfragen, übersetzt sie in interne Ereignisse und streamt Agent-Antworten als strukturierte Ergebnisse zurück.

Dieser Ansatz eignet sich für bidirektionale Integrationen, bei denen externe Systeme KI-Funktionen triggern müssen. Ein
Dokumentenportal könnte eine KI-Klassifizierung auslösen, wenn Dateien hochgeladen werden, eine Webanwendung könnte
KI-generierte Zusammenfassungen für ihr Dashboard anfordern, oder ein externes Workflow-System könnte Analyseaufgaben an
KI-Agents delegieren.

### 3. Datenpipeline-Integration (Batch-Synchronisation)

[Daten-Pipelines](/de/docs/6_pipelines/) synchronisieren kontinuierlich Daten von externen Systemen in Swiss AI Hub
Wissensbasen. Dagster-Pipelines verbinden sich mit externen Datenquellen, extrahieren und transformieren die Daten und
laden sie dann in den Swiss AI Hub, wo sie für RAG (Retrieval-Augmented Generation) indexiert werden. Pipelines können
nach Zeitplänen ausgeführt oder durch Ereignisse ausgelöst werden.

Dies deckt leselastige Integrationen ab, bei denen die KI hauptsächlich externe Daten analysiert, sowie groß angelegte
Dokumentenindizierung oder geplante Datensynchronisation von Unternehmenssystemen. Sie könnten SharePoint-Dokumente
nächtlich in eine Wissensbasis synchronisieren, Support-Tickets kontinuierlich zur Trendanalyse aufnehmen oder
Produktkataloge nach Zeitplan für Kundendienst-Agents importieren.

### 4. MCP-Integration (Entwicklungstools)

Das [Model Context Protocol (MCP)](/de/docs/19_mcp/) ermöglicht es KI-Coding-Assistenten wie Claude Code, Gemini CLI und
Cursor, während der Entwicklung mit dem Swiss AI Hub zu interagieren. Dies bietet eine schreibgeschützte Beobachtung des
Plattformzustands für Entwicklungs- und Debugging-Workflows.

## Die Wahl des richtigen Ansatzes

| Ansatz                      | Latenz   | Richtung      | Komplexität | Am besten geeignet für                            |
| :-------------------------- | :------- | :------------ | :---------- | :------------------------------------------------ |
| Direkte Agenten-API-Aufrufe | Echtzeit | Ausgehend     | Niedrig     | Einfache API-Aufrufe innerhalb der Agentenlogik   |
| Plattform-API-Integration   | Echtzeit | Eingehend     | Mittel      | Externe Systeme, die KI auslösen                  |
| Datenpipeline-Integration   | Batch    | Eingehend     | Mittel-Hoch | Groß angelegte Datensynchronisation, Wissensbasen |
| MCP-Integration             | Echtzeit | Bidirektional | Niedrig     | Nur Entwicklungstools                             |

## Netzwerk- und Sicherheitsaspekte

### Ausgehende Konnektivität (für direkte Agenten-API-Aufrufe und Pipelines)

Die Swiss AI Hub VM benötigt ausgehenden HTTPS (Port 443)-Zugriff auf externe Systeme. Konfigurieren Sie
Firewall-Regeln, um ausgehende Verbindungen zu bestimmten Endpunkten zuzulassen. Die Plattform unterstützt
API-Schlüssel, OAuth-Tokens und zertifikatbasierte Authentifizierung. Alle externen Verbindungen verwenden
verschlüsseltes HTTPS.

[Netzwerkanforderungen](/de/docs/3_deployment_guide/7_network_requirements/) enthält weitere Details.

### Eingehende Konnektivität (für Plattform-API-Integration)

Externe Systeme verbinden sich mit dem Swiss AI Hub über Standard-HTTPS (Port 443). Authentifizierungsoptionen umfassen
OAuth 2.0, API-Schlüssel oder Azure AD-Integration. Der Traefik Reverse Proxy bietet einen integrierten Schutz vor
Ratenbegrenzung, und Let's Encrypt übernimmt die automatische Zertifikatsverwaltung für die TLS-Terminierung.

[Netzwerksicherheit](/de/docs/20_security/4_network_security/) behandelt die Sicherheitsarchitektur.

## Allgemeine Integrationsprinzipien

Passen Sie Ihren Integrationsansatz an die Anforderungen bezüglich Latenz, Volumen und Richtung an. Deployen Sie den
Swiss AI Hub in der Schweiz, wenn Sie Schweizer Datenresidenz benötigen. Verwenden Sie TLS-Verschlüsselung, RBAC und
eine umfassende Audit-Protokollierung. Nutzen Sie Enterprise SSO über OAuth 2.0, SAML oder Azure AD. Konfigurieren Sie
die entsprechenden Firewall-Regeln für eingehende und ausgehende Konnektivität. Befolgen Sie die
[Schweizer Datenschutzrichtlinien](/de/docs/21_compliance/3_dsg/).

## Verwandte Dokumentation

- Agents: [Agent Developer Guide](https://github.com/bbvch-ai/swiss-ai-hub/tree/main/aihub_agent) – Implementierung
  direkter API-Aufrufe
- API: [Agent Interaction REST API](/de/docs/18_api/2_agent_interaction_api/) – HTTP-Schnittstelle der Plattform
- Pipelines: [Daten-Pipelines](/de/docs/6_pipelines/) – Automatisierte Datensynchronisation
- MCP: [Model Context Protocol](/de/docs/19_mcp/) – KI-Assistent-Integration
- Netzwerk: [Netzwerkanforderungen](/de/docs/3_deployment_guide/7_network_requirements/) – Firewall und Konnektivität
- Sicherheit: [Netzwerksicherheit](/de/docs/20_security/4_network_security/) – Sicherheitsarchitektur
- Authentifizierung: [Authentifizierungseinrichtung](/de/docs/11_access_management/1_authentication_setup/) – SSO
  konfigurieren
