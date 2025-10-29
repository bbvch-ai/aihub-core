---
title: Modell-Kontext-Protokoll (MCP)
source_sha: "0d71a850aaa957ab1d84ce6b1bef09d64a22bab4ec23b9ebe863f4e72be45fc5"
---

# Modell-Kontext-Protokoll (MCP) Server

## Konzept und Zweck

Der Modell-Kontext-Protokoll (MCP) Server stellt die Fähigkeiten des Swiss AI-Hub für KI-Entwicklungsassistenten und Automatisierungstools über ein standardisiertes Protokoll bereit. Basierend auf FastAPI und direkt in den Haupt-API-Service integriert, ermöglicht diese Schnittstelle KI-Assistenten die Interaktion mit der Plattform.

## Zentrale Designprinzipien

### Standardbasierte Integration

MCP ist ein aufkommender Standard, um Anwendungsfunktionalitäten KI-Assistenten auf strukturierte, auffindbare Weise zugänglich zu machen. Durch die Implementierung von MCP anstelle proprietärer Schnittstellen gewährleistet der Swiss AI-Hub die Kompatibilität mit jedem MCP-kompatiblen Tool, ermöglicht die automatische Integration, wenn neue KI-Entwicklungstools das Protokoll übernehmen, und bietet Typsicherheit durch schemabasierte Interaktionen, die eine falsche Toolnutzung verhindern.

Der standardbasierte Ansatz macht das Entwicklungs-Ökosystem der Plattform zukunftssicher: Wenn neue KI-Assistenten und Automatisierungstools entstehen, erhalten sie sofortigen Zugriff auf die Swiss AI-Hub-Funktionen, ohne dass individuelle Integrationsarbeiten erforderlich sind.

### Automatische API-Übersetzung

Der MCP Server übersetzt die bestehende FastAPI REST-Schnittstelle automatisch in MCP-Ressourcen, wodurch doppelter Implementierungs- und Wartungsaufwand entfällt. Aus Code-Annotationen generierte OpenAPI-Spezifikationen werden automatisch in MCP-Schemata umgewandelt, was die Konsistenz zwischen menschenorientierten REST APIs und KI-orientierten MCP-Ressourcen sicherstellt. Änderungen an den Plattformfunktionen spiegeln sich sofort in beiden Schnittstellen wider, ohne separate Dokumentations- oder Übersetzungsschritte.

Diese Architektur pflegt eine einzige Quelle der Wahrheit: FastAPI-Routendefinitionen, Typ-Annotationen und Dokumentationsstrings dienen beiden Entwicklungsgemeinschaften gleichzeitig.

## Unterstützte Funktionen

Der MCP Server bietet KI-Assistenten Lesezugriff auf Plattforminformationen aus vier Bereichen:

**Agenten-Erkennung und -Inspektion**: KI-Assistenten können verfügbare Agenten abfragen, detaillierte Agentenkonfigurationen und -funktionen abrufen, Agenten-Ausführungsmuster und Leistungsmerkmale untersuchen und verstehen, welche Agenten welche Aufgabentypen bearbeiten. Dies ermöglicht Assistenten, geeignete Agenten für spezifische Probleme zu empfehlen und korrekten Agenten-Aufrufcode zu generieren.

**Konversationsanalyse**: Der Zugriff auf Konversationsverläufe, Nachrichtenprotokolle und Teilnehmerinformationen hilft KI-Assistenten, den Anwendungskontext zu verstehen. Assistenten können Konversationsflüsse nachverfolgen, Multi-Agenten-Kollaborationsmuster analysieren und Debugging-Anleitungen basierend auf tatsächlichen Konversationsstrukturen anstatt auf Annahmen bereitstellen.

**Beobachtbarkeit und Diagnose**: Voller Zugriff auf Ereignisströme, Ausführungsprotokolle und Zeitreihenanalysen ermöglicht KI-gestütztes Debugging. Assistenten können Ereignisse über Komponenten hinweg korrelieren, Leistungsengpässe identifizieren, Fehler auf ihre Ursachen zurückverfolgen und Optimierungen auf der Grundlage tatsächlicher Betriebsdaten vorschlagen.

**Prozessüberwachung**: Einblick in Geschäftsprozessdefinitionen, Ausführungszustände und Abschlussverläufe ermöglicht KI-Assistenten, Anwendungs-Workflows zu verstehen. Dies unterstützt die Prozessoptimierung, Fehleranalyse und Anleitung zur Implementierung neuer Prozessvarianten.

## Geschäftswert

### KI-gestützte Operationen und Überwachung

KI-Assistenten können den Live-Plattformstatus für operative Einblicke und Fehlerbehebung abfragen. Operationsteams erhalten sofortige Antworten zum Status der Prozessausführung, zu Agenten-Leistungsmetriken, Ereignisverläufen und zum Systemzustand, ohne Schnittstellen manuell navigieren oder Protokolle parsen zu müssen. Dies reduziert die durchschnittliche Lösungszeit für Vorfälle und ermöglicht die proaktive Problemidentifizierung durch KI-gestützte Anomalieerkennung über Konversationsmuster, Agentenverhaltensweisen und die Ausführung von Geschäftsprozessen.

### Intelligentes Wissensmanagement

Die MCP-Schnittstelle bietet KI-Assistenten Zugang zu Wissensdatenbanken, Dokumenten-Repositories und RAG-Indizes, was eine anspruchsvolle Wissensfindung und -analyse ermöglicht. Benutzer können Fragen in natürlicher Sprache stellen, die Informationen aus verteilten Dokumentensammlungen abrufen und synthetisieren, Wissenslücken identifizieren und Empfehlungen für Inhaltsverbesserungen erhalten. Diese Funktion ist wertvoll für Compliance-Teams, die spezifische regulatorische Referenzen finden müssen, und für Forscher, die große technische Dokumentensammlungen durchsuchen.

### Verbesserte Entwicklerproduktivität

Entwickler profitieren von KI-Assistenten mit direktem Plattformzugriff für Codegenerierung und Debugging. Codevorschläge werden anhand aktueller API-Schemata validiert anstatt anhand generischer Muster, Debugging-Konversationen umfassen den tatsächlichen Plattformstatus, und die Testgenerierung verwendet reale Agentenkonfigurationen. Organisationen berichten von Produktivitätsverbesserungen in der Entwicklung von 30-50%, wenn KI-Assistenten strukturierten Systemzugriff haben. Neue Teammitglieder werden schneller produktiv durch sofortige, kontextbezogene Anleitung, die die Einarbeitungszeit reduziert und die Abhängigkeit von Dokumentationssuchen eliminiert.

### Prozessanalyse und -optimierung

KI-Assistenten können Geschäftsprozessdefinitionen, Ausführungsverläufe und Leistungsmuster analysieren, um Optimierungsmöglichkeiten zu identifizieren. Durch das Abfragen von Prozessinstanzen, Agenteninteraktionen und Abschlussmetriken liefern Assistenten umsetzbare Erkenntnisse für Workflow-Verbesserungen, die Identifizierung von Engpässen und die Ressourcenallokation. Diese Funktion unterstützt kontinuierliche Prozessverbesserungsinitiativen und hilft Organisationen, den Return on Investment (ROI) von KI-Automatisierungsinvestitionen zu maximieren.

## Implementierungsansatz

Der MCP-Server wurde mit der FastMCP-Bibliothek erstellt und generiert Ressourcen automatisch aus FastAPI-Routendefinitionen und OpenAPI-Spezifikationen. Der Server wird unter `/mcp` auf dem Haupt-API-Service gemountet und teilt sich die Authentifizierungsinfrastruktur, Datenbankverbindungen und den Zugriff auf das Ereignissystem mit REST-Endpunkten. Es werden nur Leseoperationen (GET-Endpunkte) freigegeben, wodurch eine sichere Entwicklungsschnittstelle aufrechterhalten wird, die eine Plattformbeobachtung ohne Zustandsänderung ermöglicht. Die Authentifizierung verwendet dieselben OAuth2-/SAML-/LDAP-Identitätsprovider wie REST APIs, wobei hierarchische Berechtigungsprüfungen die Ressourcen basierend auf den Benutzerzugriffsrechten filtern. KI-Entwicklungstools konfigurieren MCP-Verbindungen über `.mcp.json`-Dateien in Projekt-Repositories, was einen automatischen Plattformzugriff während Entwicklungssitzungen ermöglicht. Die Architektur skaliert horizontal mit API-Instanzen, erfordert keine separate Bereitstellung und verursacht nur minimalen Ressourcen-Overhead für den bestehenden Dienst.
