---
title: Model Context Protocol (MCP)
source_sha: d804511017c71b46b73b0a75c477d6be579a5f248cde303c29f7f1127e36c659
---

# Model Context Protocol (MCP) Server

## Konzept und Zweck

Der Model Context Protocol (MCP) Server stellt die Fähigkeiten des Swiss AI Hub für KI-Entwicklungsassistenten und
Automatisierungstools über ein standardisiertes Protokoll bereit. Dieses Interface, das auf FastAPI basiert und direkt
in den Haupt-API-Service integriert ist, ermöglicht KI-Assistenten die Interaktion mit der Plattform.

## Kernprinzipien des Designs

### Standardsbasierte Integration

MCP ist ein aufkommender Standard, um Anwendungsfunktionalitäten strukturiert und auffindbar für KI-Assistenten
bereitzustellen. Durch die Implementierung von MCP anstelle proprietärer Schnittstellen stellt der Swiss AI Hub die
Kompatibilität mit jedem MCP-kompatiblen Tool sicher, ermöglicht eine automatische Integration, sobald neue
KI-Entwicklungstools das Protokoll übernehmen, und bietet Typsicherheit durch schemabasierte Interaktionen, die eine
falsche Tool-Nutzung verhindern.

Der standardsbasierte Ansatz macht das Entwicklungs-Ökosystem der Plattform zukunftssicher: Wenn neue KI-Assistenten und
Automatisierungstools aufkommen, erhalten sie sofortigen Zugriff auf die Fähigkeiten des Swiss AI Hub, ohne dass
individuelle Integrationsarbeiten erforderlich sind.

### Automatische API-Übersetzung

Der MCP Server übersetzt die bestehende FastAPI REST-Schnittstelle automatisch in MCP-Ressourcen, wodurch doppelter
Implementierungs- und Wartungsaufwand entfällt. Aus Code-Annotationen generierte OpenAPI-Spezifikationen werden
automatisch in MCP-Schemata umgewandelt, was die Konsistenz zwischen menschenzentrierten REST APIs und KI-zentrierten
MCP-Ressourcen gewährleistet. Änderungen an den Plattformfähigkeiten spiegeln sich sofort in beiden Schnittstellen
wider, ohne separate Dokumentations- oder Übersetzungsschritte.

Diese Architektur behält eine einzige Quelle der Wahrheit bei: FastAPI-Routendefinitionen, Typ-Annotationen und
Dokumentations-Strings dienen gleichzeitig beiden Entwicklungsgemeinschaften.

## Unterstützte Funktionen

Der MCP Server bietet KI-Assistenten Lesezugriff auf Plattforminformationen in vier Bereichen:

**Agent Discovery und Inspection**: KI-Assistenten können verfügbare Agents abfragen, detaillierte Agent-Konfigurationen
und -Fähigkeiten abrufen, Agent-Ausführungsmuster und Leistungsmerkmale untersuchen und verstehen, welche Agents welche
Aufgabentypen bearbeiten. Dies ermöglicht Assistenten, geeignete Agents für spezifische Probleme zu empfehlen und
korrekten Agent-Aufrufcode zu generieren.

**Konversationsanalyse**: Der Zugriff auf Konversations-Threads, Nachrichtenverläufe und Teilnehmerinformationen hilft
KI-Assistenten, den Anwendungskontext zu verstehen. Assistenten können Konversationsflüsse nachverfolgen, Muster der
Multi-Agent-Kollaboration analysieren und Debugging-Anleitungen basierend auf tatsächlichen Konversationsstrukturen
anstatt auf Annahmen bereitstellen.

**Observability und Diagnostik**: Umfassender Zugriff auf Event-Streams, Ausführungsprotokolle und Zeitreihenanalysen
ermöglicht KI-gestütztes Debugging. Assistenten können Events über Komponenten hinweg korrelieren, Leistungsengpässe
identifizieren, Fehler auf Ursachen zurückführen und Optimierungen auf der Grundlage tatsächlicher Betriebsdaten
vorschlagen.

**Prozessüberwachung**: Einblick in Geschäftsprozessdefinitionen, Ausführungszustände und Abschlussverläufe ermöglicht
es KI-Assistenten, Anwendungs-Workflows zu verstehen. Dies unterstützt die Prozessoptimierung, Fehleranalyse und
Anleitung bei der Implementierung neuer Prozessvarianten.

## Geschäftswert

### KI-gestützte Operationen und Überwachung

KI-Assistenten können den Live-Plattformstatus für operative Einblicke und Fehlerbehebung abfragen. Operationsteams
erhalten sofortige Antworten zum Status der Prozessausführung, zu Agent-Leistungsmetriken, Event-Historien und zur
Systemgesundheit, ohne Schnittstellen manuell navigieren oder Protokolle parsen zu müssen. Dies reduziert die
durchschnittliche Problemlösungszeit (Mean Time To Resolution) bei Vorfällen und ermöglicht eine proaktive
Problemidentifikation durch KI-gestützte Anomalieerkennung über Konversationsmuster, Agent-Verhalten und die Ausführung
von Geschäftsprozessen hinweg.

### Intelligentes Wissensmanagement

Die MCP-Schnittstelle bietet KI-Assistenten Zugang zu Wissensdatenbanken, Dokumenten-Repositories und RAG-Indizes, was
eine anspruchsvolle Wissensentdeckung und -analyse ermöglicht. Benutzer können Fragen in natürlicher Sprache stellen,
die Informationen über verteilte Dokumentsammlungen hinweg abrufen und synthetisieren, Wissenslücken identifizieren und
Empfehlungen für Inhaltsverbesserungen erhalten. Diese Fähigkeit ist wertvoll für Compliance-Teams, die spezifische
regulatorische Referenzen finden müssen, und für Forscher, die grosse technische Dokumentsammlungen untersuchen.

### Erhöhte Entwicklerproduktivität

Entwickler profitieren von KI-Assistenten mit direktem Plattformzugriff für Codegenerierung und Debugging.
Codevorschläge werden anhand aktueller API-Schemata validiert anstatt gegen generische Muster, Debugging-Konversationen
umfassen den tatsächlichen Plattformzustand und die Testgenerierung verwendet reale Agent-Konfigurationen.
Organisationen berichten von Produktivitätssteigerungen bei der Entwicklung um 30-50%, wenn KI-Assistenten
strukturierten Systemzugriff haben. Neue Teammitglieder werden durch sofortige, kontextbezogene Anleitungen schneller
produktiv, was die Einarbeitungszeit verkürzt und die Abhängigkeit von Dokumentationssuchen eliminiert.

### Prozessanalyse und -optimierung

KI-Assistenten können Geschäftsprozessdefinitionen, Ausführungsverläufe und Leistungsmuster analysieren, um
Optimierungsmöglichkeiten zu identifizieren. Durch das Abfragen von Prozessinstanzen, Agent-Interaktionen und
Abschlussmetriken liefern Assistenten umsetzbare Erkenntnisse für Workflow-Verbesserungen, die Identifizierung von
Engpässen und die Ressourcenallokation. Diese Fähigkeit unterstützt Initiativen zur kontinuierlichen Prozessverbesserung
und hilft Organisationen, den Return on Investment (ROI) ihrer KI-Automatisierungsinvestitionen zu maximieren.

## Implementierungsansatz

Der MCP-Server, der mit der FastMCP-Bibliothek erstellt wurde, generiert Ressourcen automatisch aus
FastAPI-Routendefinitionen und OpenAPI-Spezifikationen. Der Server wird unter `/mcp` auf dem Haupt-API-Service gemountet
und teilt die Authentifizierungsinfrastruktur, Datenbankverbindungen und den Zugriff auf das Eventsystem mit
REST-Endpunkten. Es werden nur lesende Operationen (GET-Endpunkte) exponiert, wodurch eine sichere
Entwicklungsschnittstelle aufrechterhalten wird, die die Plattformbeobachtung ohne Zustandsänderung ermöglicht. Die
Authentifizierung verwendet dieselben OAuth2-/SAML-/LDAP-Identitätsprovider wie REST APIs, wobei hierarchische
Berechtigungsprüfungen Ressourcen basierend auf den Benutzerzugriffsrechten filtern. KI-Entwicklungstools konfigurieren
MCP-Verbindungen über `.mcp.json`-Dateien in Projekt-Repositories, was einen automatischen Plattformzugriff während
Entwicklungssitzungen ermöglicht. Die Architektur skaliert horizontal mit API-Instanzen, erfordert kein separates
Deployment und fügt dem bestehenden Service nur minimalen Ressourcen-Overhead hinzu.
