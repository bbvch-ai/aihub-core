---
title: Model Context Protocol (MCP)
source_sha: 37bd3ce8304048892e93769776ca31675c94815b1987a801213f2eb062db6e35
---

# Model Context Protocol (MCP) Server

## Konzept und Zweck

Der Model Context Protocol (MCP) Server stellt die Fähigkeiten des Swiss AI Hub KI-Entwicklungsassistenten und
Automatisierungstools über ein standardisiertes Protokoll zur Verfügung. Basierend auf FastAPI und direkt in den
Haupt-API-Dienst integriert, ermöglicht diese Schnittstelle KI-Assistenten die Interaktion mit der Plattform.

## Kern-Designprinzipien

### Standardbasierte Integration

MCP ist ein aufkommender Standard, um Anwendungsfunktionen auf strukturierte, auffindbare Weise für KI-Assistenten
bereitzustellen. Durch die Implementierung von MCP anstelle proprietärer Schnittstellen stellt der Swiss AI Hub die
Kompatibilität mit jedem MCP-kompatiblen Tool sicher, ermöglicht eine automatische Integration, sobald neue
KI-Entwicklungstools das Protokoll übernehmen, und bietet Typsicherheit durch schema-basierte Interaktionen, die eine
falsche Tool-Nutzung verhindern.

Der standardbasierte Ansatz macht das Entwicklungs-Ökosystem der Plattform zukunftssicher: Wenn neue KI-Assistenten und
Automatisierungstools entstehen, erhalten sie sofortigen Zugriff auf die Funktionen des Swiss AI Hub, ohne dass eine
kundenspezifische Integrationsarbeit erforderlich ist.

### Automatische API-Übersetzung

Der MCP Server übersetzt die bestehende FastAPI REST-Schnittstelle automatisch in MCP-Ressourcen, wodurch doppelter
Implementierungs- und Wartungsaufwand entfällt. Aus Code-Annotationen generierte OpenAPI-Spezifikationen werden
automatisch in MCP-Schemata umgewandelt, was die Konsistenz zwischen menschenzentrierten REST APIs und KI-zentrierten
MCP-Ressourcen gewährleistet. Änderungen an den Plattformfähigkeiten spiegeln sich sofort in beiden Schnittstellen
wider, ohne separate Dokumentations- oder Übersetzungsschritte.

Diese Architektur pflegt eine einzige Quelle der Wahrheit: FastAPI-Routendefinitionen, Typannotationen und
Dokumentationsstrings dienen beiden Entwicklungsgemeinschaften gleichzeitig.

## Unterstützte Funktionen

Der MCP Server bietet KI-Assistenten Lesezugriff auf Plattforminformationen in vier Bereichen:

**Agenten-Erkennung und -Inspektion**: KI-Assistenten können verfügbare Agenten abfragen, detaillierte
Agentenkonfigurationen und -fähigkeiten abrufen, Agentenausführungsmuster und Leistungsmerkmale untersuchen und
verstehen, welche Agenten welche Aufgabentypen bearbeiten. Dies ermöglicht es Assistenten, geeignete Agenten für
spezifische Probleme zu empfehlen und korrekten Agenten-Aufrufcode zu generieren.

**Konversationsanalyse**: Der Zugriff auf Konversationsverläufe, Nachrichtenprotokolle und Teilnehmerinformationen hilft
KI-Assistenten, den Anwendungskontext zu verstehen. Assistenten können Konversationsflüsse verfolgen, Muster der
Multi-Agenten-Zusammenarbeit analysieren und Debugging-Anleitungen basierend auf tatsächlichen Konversationsstrukturen
statt auf Annahmen bereitstellen.

**Observability und Diagnostik**: Vollständiger Zugriff auf Event-Streams, Ausführungsprotokolle und Zeitreihenanalysen
ermöglicht KI-gestütztes Debugging. Assistenten können Events über Komponenten hinweg korrelieren, Performance-Engpässe
identifizieren, Fehler auf ihre Grundursachen zurückführen und Optimierungen basierend auf tatsächlichen Betriebsdaten
vorschlagen.

**Prozessüberwachung**: Die Einsicht in Geschäfts-Prozessdefinitionen, Ausführungszustände und Abschlussverläufe
ermöglicht es KI-Assistenten, Anwendungs-Workflows zu verstehen. Dies unterstützt die Prozessoptimierung, Fehleranalyse
und Anleitung bei der Implementierung neuer Prozessvarianten.

## Geschäftlicher Nutzen

### KI-gestützte Operationen und Überwachung

KI-Assistenten können den Live-Plattformstatus für operative Einblicke und Fehlerbehebung abfragen. Operationsteams
erhalten sofortige Antworten zum Status der Prozessausführung, zu Agenten-Leistungskennzahlen, Ereignisverläufen und zur
Systemintegrität, ohne manuell Schnittstellen navigieren oder Protokolle parsen zu müssen. Dies reduziert die
durchschnittliche Lösungszeit für Vorfälle und ermöglicht die proaktive Problemerkennung durch KI-gestützte
Anomalieerkennung über Konversationsmuster, Agentenverhalten und die Ausführung von Geschäftsprozessen hinweg.

### Intelligentes Wissensmanagement

Die MCP-Schnittstelle bietet KI-Assistenten Zugang zu Wissensdatenbanken, Dokumenten-Repositories und RAG-Indizes, was
eine ausgefeilte Wissensentdeckung und -analyse ermöglicht. Benutzer können natürliche Sprachfragen stellen, die
Informationen aus verteilten Dokumentsammlungen abrufen und synthetisieren, Wissenslücken identifizieren und
Empfehlungen für Inhaltsverbesserungen erhalten. Diese Funktion ist wertvoll für Compliance-Teams, die spezifische
regulatorische Referenzen finden müssen, und für Forscher, die große technische Dokumentsammlungen erkunden.

### Verbesserte Entwicklerproduktivität

Entwickler profitieren von KI-Assistenten mit direktem Plattformzugriff für Code-Generierung und Debugging.
Code-Vorschläge werden anhand aktueller API-Schemata und nicht anhand generischer Muster validiert,
Debugging-Konversationen umfassen den tatsächlichen Plattformstatus, und die Testgenerierung verwendet reale
Agentenkonfigurationen. Organisationen berichten von einer Steigerung der Entwicklerproduktivität um 30-50 %, wenn
KI-Assistenten strukturierten Systemzugriff haben. Neue Teammitglieder werden schneller produktiv durch sofortige,
kontextbezogene Anleitung, die die Einarbeitungszeit reduziert und die Abhängigkeit von Dokumentationssuchen eliminiert.

### Prozessanalyse und -optimierung

KI-Assistenten können Geschäfts-Prozessdefinitionen, Ausführungsverläufe und Leistungsmuster analysieren, um
Optimierungsmöglichkeiten zu identifizieren. Durch die Abfrage von Prozessinstanzen, Agenten-Interaktionen und
Abschlussmetriken liefern Assistenten umsetzbare Erkenntnisse für Workflow-Verbesserungen, die Identifizierung von
Engpässen und die Ressourcenallokation. Diese Fähigkeit unterstützt kontinuierliche Prozessverbesserungsinitiativen und
hilft Organisationen, den Return on Investment in KI-Automatisierung zu maximieren.

## Implementierungsansatz

Der MCP-Server, der mithilfe der FastMCP-Bibliothek erstellt wurde, generiert Ressourcen automatisch aus
FastAPI-Routendefinitionen und OpenAPI-Spezifikationen. Der Server wird unter `/mcp` auf dem Haupt-API-Dienst
eingebunden und teilt sich die Authentifizierungsinfrastruktur, Datenbankverbindungen und den Zugriff auf das
Event-System mit REST-Endpunkten. Es werden nur lesende Operationen (GET-Endpunkte) offengelegt, wodurch eine sichere
Entwicklungsschnittstelle gewährleistet wird, die eine Plattformbeobachtung ohne Zustandsmodifikation ermöglicht. Die
Authentifizierung verwendet dieselben OAuth2-/SAML-/LDAP-Identitätsanbieter wie REST APIs, mit hierarchischen
Berechtigungsprüfungen, die Ressourcen basierend auf Benutzerzugriffsrechten filtern. KI-Entwicklungstools konfigurieren
MCP-Verbindungen über `.mcp.json`-Dateien in Projekt-Repositories, was einen automatischen Plattformzugriff während der
Entwicklungssitzungen ermöglicht. Die Architektur skaliert horizontal mit API-Instanzen, erfordert keine separate
Bereitstellung und fügt dem bestehenden Dienst nur minimale Ressourcen-Overheads hinzu.
