---
title: 'Integrationen mit externen Systemen'
source_sha: "86ac2ecb5fe12a87506f68614a53978a071edef6aa0186ae45508b4373c74cd3"
---

# Integrationen mit externen Systemen

Der Swiss AI-Hub verbindet sich über vier Integrationsmuster mit externen Systemen.

## Integrationsansätze

### 1. Direkte Agenten-API-Aufrufe

Agenten können externe APIs (REST, SOAP, GraphQL usw.) direkt aus ihren Workflow-Schritten heraus aufrufen, indem sie Standard-Python-HTTP-Bibliotheken wie `httpx` oder `aiohttp` verwenden. Während der Ausführung tätigen Agenten API-Aufrufe als Teil ihrer Logik, verarbeiten Antworten und integrieren die Ergebnisse in ihre Ausgaben.

Dies funktioniert gut für einfache API-Aufrufe mit Einzeloperationen innerhalb von Agenten-Workflows. Ein Agent könnte während eines Gesprächs Kundendaten aus einem CRM abrufen, Formulardaten nach Benutzergenehmigung an ein externes Portal übermitteln oder ein Ticketsystem abfragen, um Fragen zu beantworten. Das [Agent Developer README](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) enthält Implementierungsmuster und Beispiele.

### 2. Plattform-API-Integration (externe Systeme rufen auf)

Externe Systeme können AI-Hub-Agenten über die [Agent Interaction REST API](../16_api/2_agent_interaction_api/) auslösen. Die API authentifiziert eingehende HTTP-Anfragen, übersetzt sie in interne Ereignisse und streamt Agentenantworten als strukturierte Ergebnisse zurück.

Dieser Ansatz eignet sich für bidirektionale Integrationen, bei denen externe Systeme KI-Funktionen auslösen müssen. Ein Dokumentenportal könnte eine KI-Klassifizierung auslösen, wenn Dateien hochgeladen werden, eine Webanwendung könnte KI-generierte Zusammenfassungen für ihr Dashboard anfordern, oder ein externes Workflow-System könnte Analyseaufgaben an KI-Agenten delegieren.

### 3. Datenpipeline-Integration (Stapel-Synchronisierung)

[Datenpipelines](../6_pipelines/) synchronisieren kontinuierlich Daten von externen Systemen in AI-Hub-Wissensdatenbanken. Dagster-Pipelines verbinden sich mit externen Datenquellen, extrahieren und transformieren die Daten und laden sie dann in AI-Hub, wo sie für RAG (Retrieval-Augmented Generation) indiziert werden. Pipelines können nach Zeitplänen ausgeführt oder durch Ereignisse ausgelöst werden.

Dies deckt leselastige Integrationen ab, bei denen KI hauptsächlich externe Daten analysiert, großflächige Dokumentenindizierung oder geplante Datensynchronisation aus Unternehmenssystemen. Sie könnten SharePoint-Dokumente nächtlich in eine Wissensdatenbank synchronisieren, Support-Tickets kontinuierlich für Trendanalysen erfassen oder Produktkataloge nach einem Zeitplan für Kundendienst-Agenten importieren.

### 4. MCP-Integration (Entwicklungstools)

Das [Model Context Protocol (MCP)](../17_mcp/) ermöglicht es KI-Codierungsassistenten wie Claude Code, Gemini CLI und Cursor, während der Entwicklung mit AI-Hub zu interagieren. Dies bietet eine schreibgeschützte Beobachtung des Plattformzustands für Entwicklungs- und Debugging-Workflows.

## Den richtigen Ansatz wählen

| Ansatz | Latenz | Richtung | Komplexität | Am besten geeignet für |
|----------|---------|-----------|------------|----------|
| Direkte Agenten-API-Aufrufe | Echtzeit | Ausgehend | Niedrig | Einfache API-Aufrufe innerhalb der Agentenlogik |
| Plattform-API-Integration | Echtzeit | Eingehend | Mittel | Externe Systeme, die KI auslösen |
| Datenpipeline-Integration | Stapel | Eingehend | Mittel-Hoch | Großflächige Datensynchronisation, Wissensdatenbanken |
| MCP-Integration | Echtzeit | Bidirektional | Niedrig | Nur Entwicklungstools |

## Netzwerk- und Sicherheitsüberlegungen

### Ausgehende Konnektivität (für direkte Agenten-API-Aufrufe und Pipelines)

Die AI-Hub VM benötigt ausgehenden HTTPS-Zugriff (Port 443) auf externe Systeme. Konfigurieren Sie Firewall-Regeln, um ausgehende Verbindungen zu bestimmten Endpunkten zu ermöglichen. Die Plattform unterstützt API-Schlüssel, OAuth-Tokens und zertifikatbasierte Authentifizierung. Alle externen Verbindungen verwenden verschlüsseltes HTTPS.

[Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) enthält weitere Details.

### Eingehende Konnektivität (für Plattform-API-Integration)

Externe Systeme verbinden sich mit AI-Hub über Standard-HTTPS (Port 443). Authentifizierungsoptionen umfassen OAuth 2.0, API-Schlüssel oder Azure AD-Integration. Der Traefik Reverse Proxy bietet einen integrierten Schutz vor Rate Limiting, und Let's Encrypt verwaltet die automatische Zertifikatsverwaltung für die TLS-Terminierung.

[Netzwerksicherheit](../18_security/4_network_security/) behandelt die Sicherheitsarchitektur.

## Allgemeine Integrationsprinzipien

Passen Sie Ihren Integrationsansatz an die Anforderungen an Latenz, Volumen und Richtung an. Stellen Sie AI-Hub in der Schweiz bereit, wenn Sie eine Schweizer Datenresidenz benötigen. Verwenden Sie TLS-Verschlüsselung, RBAC und eine umfassende Audit-Protokollierung. Nutzen Sie Enterprise-SSO über OAuth 2.0, SAML oder Azure AD. Konfigurieren Sie geeignete Firewall-Regeln für die eingehende und ausgehende Konnektivität. Befolgen Sie die [Schweizer Datenschutzrichtlinien](../19_compliance/3_dsg/).

## Verwandte Dokumentation

- Agenten: [Agent Developer Guide](https://github.com/bbvch-ai/aihub-core/tree/main/aihub_agent) - Implementierung direkter API-Aufrufe
- API: [Agent Interaction REST API](../16_api/2_agent_interaction_api/) - Plattform-HTTP-Schnittstelle
- Pipelines: [Datenpipelines](../6_pipelines/) - Automatisierte Datensynchronisation
- MCP: [Model Context Protocol](../17_mcp/) - KI-Assistenten-Integration
- Netzwerk: [Netzwerkanforderungen](../3_deployment_guide/7_network_requirements/) - Firewall und Konnektivität
- Sicherheit: [Netzwerksicherheit](../18_security/4_network_security/) - Sicherheitsarchitektur
- Authentifizierung: [Authentifizierungseinrichtung](../11_access_management/1_authentication_setup/) - SSO konfigurieren
