---
title: Externe Systemintegrationen
source_sha: f51d589316228de5fdf74b0472f93e9b7181bf9d2ade86b0824a4330666eb1c6
---

# Externe Systemintegrationen

Der Swiss AI-Hub verbindet sich mit externen Systemen über vier Integrationsmuster.

## Integrationsansätze

### 1. Direkte Agenten-API-Aufrufe

Agenten können externe APIs (REST, SOAP, GraphQL usw.) direkt aus ihren Workflow-Schritten mithilfe von
Standard-Python-HTTP-Bibliotheken wie `httpx` oder `aiohttp` aufrufen. Während der Ausführung tätigen Agenten
API-Aufrufe als Teil ihrer Logik, verarbeiten Antworten und integrieren die Ergebnisse in ihre Ausgaben.

Dies funktioniert gut für einfache API-Aufrufe mit einer einzigen Operation innerhalb von Agenten-Workflows. Ein Agent
könnte während einer Konversation Kundendaten aus einem CRM abrufen, Formulardaten nach Benutzergenehmigung an ein
externes Portal übermitteln oder ein Ticketing-System abfragen, um Fragen zu beantworten. Das
[Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) enthält Implementierungsmuster
und Beispiele.

### 2. Plattform-API-Integration (externe Systeme rufen auf)

Externe Systeme können AI-Hub-Agenten über die [Agent Interaction REST API](../16_api/2_agent_interaction_api/)
auslösen. Die API authentifiziert eingehende HTTP-Anfragen, übersetzt sie in interne Ereignisse und streamt
Agenten-Antworten als strukturierte Ergebnisse zurück.

Dieser Ansatz eignet sich für bidirektionale Integrationen, bei denen externe Systeme KI-Funktionen auslösen müssen. Ein
Dokumentenportal könnte eine KI-Klassifizierung auslösen, wenn Dateien hochgeladen werden, eine Webanwendung könnte
KI-generierte Zusammenfassungen für ihr Dashboard anfordern, oder ein externes Workflow-System könnte Analyseaufgaben an
KI-Agenten delegieren.

### 3. Datenpipeline-Integration (Batch-Synchronisation)

[Daten-Pipelines](../6_pipelines/) synchronisieren kontinuierlich Daten von externen Systemen in AI-Hub Wissensbasen.
Dagster-Pipelines verbinden sich mit externen Datenquellen, extrahieren und transformieren die Daten und laden sie dann
in den AI-Hub, wo sie für RAG (Retrieval-Augmented Generation) indiziert werden. Pipelines können nach Zeitplan oder
ereignisgesteuert ausgeführt werden.

Dies handhabt leseintensive Integrationen, bei denen die KI hauptsächlich externe Daten analysiert, grossformatige
Dokumentenindizierung oder die geplante Datensynchronisation von Unternehmenssystemen. Sie könnten SharePoint-Dokumente
nächtlich in eine Wissensbasis synchronisieren, Support-Tickets kontinuierlich für die Trendanalyse aufnehmen oder
Produktkataloge nach Zeitplan für Kundenservice-Agenten importieren.

### 4. MCP-Integration (Entwicklungstools)

Das [Model Context Protocol (MCP)](../17_mcp/) ermöglicht es KI-Codierungsassistenten wie Claude Code, Gemini CLI und
Cursor, während der Entwicklung mit dem AI-Hub zu interagieren. Dies bietet eine schreibgeschützte Beobachtung des
Plattformzustands für Entwicklungs- und Debugging-Workflows.

## Den richtigen Ansatz wählen

| Ansatz                      | Latenz   | Richtung      | Komplexität | Am besten geeignet für                           |
| :-------------------------- | :------- | :------------ | :---------- | :----------------------------------------------- |
| Direkte Agenten-API-Aufrufe | Echtzeit | Ausgehend     | Niedrig     | Einfache API-Aufrufe innerhalb der Agentenlogik  |
| Plattform-API-Integration   | Echtzeit | Eingehend     | Mittel      | Externe Systeme, die KI auslösen                 |
| Datenpipeline-Integration   | Batch    | Eingehend     | Mittel-Hoch | Grossflächige Datensynchronisation, Wissensbasen |
| MCP-Integration             | Echtzeit | Bidirektional | Niedrig     | Nur Entwicklungstools                            |

## Netzwerk- und Sicherheitsüberlegungen

### Ausgehende Konnektivität (für direkte Agenten-API-Aufrufe und Pipelines)

Die AI-Hub VM benötigt ausgehenden HTTPS-Zugriff (Port 443) auf externe Systeme. Konfigurieren Sie Firewall-Regeln, um
ausgehende Verbindungen zu bestimmten Endpunkten zu erlauben. Die Plattform unterstützt API-Schlüssel, OAuth-Tokens und
zertifikatbasierte Authentifizierung. Alle externen Verbindungen verwenden verschlüsseltes HTTPS.

[Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) enthält weitere Details.

### Eingehende Konnektivität (für Plattform-API-Integration)

Externe Systeme verbinden sich mit dem AI-Hub über Standard-HTTPS (Port 443). Authentifizierungsoptionen umfassen OAuth
2.0, API-Schlüssel oder Azure AD-Integration. Der Traefik Reverse Proxy bietet einen integrierten Schutz durch
Ratenbegrenzung, und Let's Encrypt übernimmt die automatische Zertifikatsverwaltung für die TLS-Terminierung.

[Netzwerksicherheit](../18_security/4_network_security/) behandelt die Sicherheitsarchitektur.

## Allgemeine Integrationsprinzipien

Passen Sie Ihren Integrationsansatz an die Anforderungen an Latenz, Volumen und Richtung an. Deployen Sie AI-Hub in der
Schweiz, wenn Sie eine Schweizer Datenresidenz benötigen. Verwenden Sie TLS-Verschlüsselung, RBAC und eine umfassende
Audit-Protokollierung. Nutzen Sie Enterprise-SSO über OAuth 2.0, SAML oder Azure AD. Konfigurieren Sie geeignete
Firewall-Regeln für eingehende und ausgehende Konnektivität. Befolgen Sie die Richtlinien des
[Schweizer Datenschutzes](../19_compliance/3_dsg/).

## Verwandte Dokumentation

- Agenten: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) – Direkte API-Aufrufe
  implementieren
- API: [Agent Interaction REST API](../16_api/2_agent_interaction_api/) – HTTP-Schnittstelle der Plattform
- Pipelines: [Daten-Pipelines](../6_pipelines/) – Automatisierte Datensynchronisation
- MCP: [Model Context Protocol](../17_mcp/) – KI-Assistenten-Integration
- Netzwerk: [Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) – Firewall und Konnektivität
- Sicherheit: [Netzwerksicherheit](../18_security/4_network_security/) – Sicherheitsarchitektur
- Authentifizierung: [Authentifizierungseinrichtung](../11_access_management/1_authentication_setup/) – SSO
  konfigurieren
