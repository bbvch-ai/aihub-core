---
title: Integrationen mit externen Systemen
source_sha: 445a5ecf1d5c6706aedef7ff49b91b131b564e0624acaf4a77956bf788a80170
---

# Integrationen mit externen Systemen

Der Swiss AI Hub verbindet sich über vier Integrationsmuster mit externen Systemen.

## Integrationsansätze

### 1. Direkte Agent-API-Aufrufe

Agents können externe APIs (REST, SOAP, GraphQL usw.) direkt aus ihren Workflow-Schritten mittels standardmäßiger
Python-HTTP-Bibliotheken wie `httpx` oder `aiohttp` aufrufen. Während der Ausführung tätigen Agents API-Aufrufe als Teil
ihrer Logik, verarbeiten Antworten und integrieren die Ergebnisse in ihre Ausgaben.

Dies eignet sich gut für einfache API-Aufrufe mit einer einzigen Operation innerhalb von Agent-Workflows. Ein Agent
könnte während eines Gesprächs Kundendaten aus einem CRM abrufen, Formulardaten nach Benutzerzustimmung an ein externes
Portal übermitteln oder ein Ticketsystem abfragen, um Fragen zu beantworten. Das
[Agent Developer README](https://github.com/bbvch-ai/swiss-ai-hub/tree/main/aihub_agent) enthält Implementierungsmuster
und Beispiele.

### 2. Plattform-API-Integration (externe Systeme rufen auf)

Externe Systeme können Swiss AI Hub Agents über die [Agent Interaction REST API](../18_api/2_agent_interaction_api/)
triggern. Die API authentifiziert eingehende HTTP-Anfragen, übersetzt sie in interne Events und streamt Agent-Antworten
als strukturierte Ergebnisse zurück.

Dieser Ansatz eignet sich für bidirektionale Integrationen, bei denen externe Systeme KI-Funktionen triggern müssen. Ein
Dokumentenportal könnte eine KI-Klassifizierung triggern, wenn Dateien hochgeladen werden, eine Webanwendung könnte
KI-generierte Zusammenfassungen für ihr Dashboard anfordern, oder ein externes Workflow-System könnte Analyseaufgaben an
KI-Agents delegieren.

### 3. Datenpipeline-Integration (Batch-Synchronisierung)

[Data Pipelines](../6_pipelines/) synchronisieren kontinuierlich Daten von externen Systemen in Swiss AI Hub
Wissensbasen. Dagster Pipelines verbinden sich mit externen Datenquellen, extrahieren und transformieren die Daten und
laden sie dann in den Swiss AI Hub, wo sie für RAG (Retrieval-Augmented Generation) indexiert werden. Pipelines können
nach Zeitplan ausgeführt oder durch Events getriggert werden.

Dies deckt leseintensive Integrationen ab, bei denen die KI hauptsächlich externe Daten analysiert, sowie groß angelegte
Dokumentenindizierung oder geplante Datensynchronisierung aus Unternehmenssystemen. Sie könnten SharePoint-Dokumente
nächtlich in eine Wissensbasis synchronisieren, Support-Tickets kontinuierlich für die Trendanalyse aufnehmen oder
Produktkataloge nach Zeitplan für Kundenservice-Agents importieren.

### 4. MCP-Integration (Entwicklungstools)

Das [Model Context Protocol (MCP)](../19_mcp/) ermöglicht es KI-Codierungsassistenten wie Claude Code, Gemini CLI und
Cursor, während der Entwicklung mit dem Swiss AI Hub zu interagieren. Dies bietet eine schreibgeschützte Beobachtung des
Plattformstatus für Entwicklungs- und Debugging-Workflows.

## Wahl des richtigen Ansatzes

| Ansatz                    | Latenz   | Richtung      | Komplexität | Am besten geeignet für                         |
| :------------------------ | :------- | :------------ | :---------- | :--------------------------------------------- |
| Direkte Agent-API-Aufrufe | Echtzeit | Ausgehend     | Gering      | Einfache API-Aufrufe innerhalb der Agent-Logik |
| Plattform-API-Integration | Echtzeit | Eingehend     | Mittel      | Externe Systeme, die KI triggern               |
| Datenpipeline-Integration | Batch    | Eingehend     | Mittel-Hoch | Große Datensynchronisierung, Wissensbasen      |
| MCP-Integration           | Echtzeit | Bidirektional | Gering      | Nur Entwicklungstools                          |

## Netzwerk- und Sicherheitsaspekte

### Ausgehende Konnektivität (für direkte Agent-API-Aufrufe und Pipelines)

Die Swiss AI Hub VM benötigt ausgehenden HTTPS-Zugriff (Port 443) auf externe Systeme. Konfigurieren Sie
Firewall-Regeln, um ausgehende Verbindungen zu bestimmten Endpunkten zu erlauben. Die Plattform unterstützt
API-Schlüssel, OAuth-Tokens und zertifikatbasierte Authentifizierung. Alle externen Verbindungen verwenden
verschlüsseltes HTTPS.

[Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) enthält weitere Details.

### Eingehende Konnektivität (für Plattform-API-Integration)

Externe Systeme verbinden sich mit dem Swiss AI Hub über standardmäßiges HTTPS (Port 443). Authentifizierungsoptionen
umfassen OAuth 2.0, API-Schlüssel oder Azure AD-Integration. Der Traefik Reverse Proxy bietet integrierten Schutz vor
Rate Limiting, und Let's Encrypt übernimmt die automatische Zertifikatsverwaltung für die TLS-Terminierung.

[Netzwerksicherheit](../20_security/4_network_security/) behandelt die Sicherheitsarchitektur.

## Allgemeine Integrationsprinzipien

Passen Sie Ihren Integrationsansatz an die Anforderungen bezüglich Latenz, Volumen und Richtung an. Deployen Sie Swiss
AI Hub in der Schweiz, wenn Sie eine Schweizer Datenresidenz benötigen. Verwenden Sie TLS-Verschlüsselung, RBAC und
umfassende Audit-Protokollierung. Nutzen Sie Enterprise SSO über OAuth 2.0, SAML oder Azure AD. Konfigurieren Sie
geeignete Firewall-Regeln für eingehende und ausgehende Konnektivität. Befolgen Sie die
[Schweizer Datenschutz](../21_compliance/3_dsg/)-Richtlinien.

## Verwandte Dokumentation

- Agents: [Agent Developer Guide](https://github.com/bbvch-ai/swiss-ai-hub/tree/main/aihub_agent) – Implementierung
  direkter API-Aufrufe
- API: [Agent Interaction REST API](../18_api/2_agent_interaction_api/) – HTTP-Schnittstelle der Plattform
- Pipelines: [Data Pipelines](../6_pipelines/) – Automatisierte Datensynchronisierung
- MCP: [Model Context Protocol](../19_mcp/) – KI-Assistenten-Integration
- Netzwerk: [Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) – Firewall und Konnektivität
- Sicherheit: [Netzwerksicherheit](../20_security/4_network_security/) – Sicherheitsarchitektur
- Authentifizierung: [Authentifizierungseinrichtung](../11_access_management/1_authentication_setup/) – SSO
  konfigurieren
