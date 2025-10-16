---
title: Modell-Kontext-Protokoll (MCP)
index: 17
source_sha: "146fdbe92459c783e30d3b60bcbbbeb12975a3a6f7d1719caf0f346a11c3b474"
---

# Modell-Kontext-Protokoll (MCP) Server

## Konzept und Zweck

Der Modell-Kontext-Protokoll (MCP) Server stellt Swiss AI-Hub-Funktionalitäten für KI-Entwicklungsassistenten und
Automatisierungstools über ein standardisiertes Protokoll bereit. Basierend auf FastAPI und direkt in den Haupt-API-Dienst integriert,
ermöglicht diese Schnittstelle KI-Assistenten die Interaktion mit der Plattform.

## Kernprinzipien des Designs

### Standardbasierte Integration

MCP ist ein aufkommender Standard zur Bereitstellung von Anwendungsfunktionalität für KI-Assistenten auf strukturierte,
auffindbare Weise. Durch die Implementierung von MCP anstelle proprietärer Schnittstellen gewährleistet der Swiss AI-Hub
die Kompatibilität mit jedem MCP-kompatiblen Tool, ermöglicht eine automatische Integration, wenn neue KI-Entwicklungstools
das Protokoll übernehmen, und bietet Typsicherheit durch schema-basierte Interaktionen, die eine falsche Tool-Nutzung verhindern.

Der standardbasierte Ansatz macht das Entwicklungsökosystem der Plattform zukunftssicher: Wenn neue KI-Assistenten
und Automatisierungstools entstehen, erhalten sie sofortigen Zugriff auf Swiss AI-Hub-Funktionalitäten,
ohne kundenspezifische Integrationsarbeiten zu erfordern.

### Automatische API-Übersetzung

Der MCP-Server übersetzt die bestehende FastAPI REST-Schnittstelle automatisch in MCP-Ressourcen,
wodurch doppelter Implementierungs- und Wartungsaufwand entfällt. Aus Code-Annotationen generierte
OpenAPI-Spezifikationen werden automatisch in MCP-Schemas umgewandelt, was die Konsistenz zwischen
menschenzentrierten REST-APIs und KI-zentrierten MCP-Ressourcen gewährleistet. Änderungen an den Plattformfunktionen
spiegeln sich sofort in beiden Schnittstellen wider, ohne separate Dokumentations- oder Übersetzungsschritte.

Diese Architektur pflegt eine einzige Quelle der Wahrheit: FastAPI-Routendefinitionen, Typannotationen und
Dokumentationsstrings dienen beiden Entwicklungsgemeinschaften gleichzeitig.

## Unterstützte Funktionen

Der MCP-Server bietet KI-Assistenten schreibgeschützten Zugriff auf Plattforminformationen in vier Bereichen:

**Agenten-Erkennung und -Inspektion**: KI-Assistenten können verfügbare Agenten abfragen, detaillierte Agentenkonfigurationen
und -fähigkeiten abrufen, Ausführungsmuster und Leistungsmerkmale von Agenten untersuchen und verstehen,
welche Agenten welche Aufgabentypen bearbeiten. Dies ermöglicht Assistenten, geeignete Agenten für spezifische Probleme
zu empfehlen und korrekten Code zur Agenten-Invokation zu generieren.

**Konversationsanalyse**: Zugriff auf Konversations-Threads, Nachrichtenverläufe und Teilnehmerinformationen hilft
KI-Assistenten, den Anwendungskontext zu verstehen. Assistenten können Konversationsflüsse verfolgen, Muster der
Multi-Agenten-Zusammenarbeit analysieren und Debugging-Anleitungen basierend auf tatsächlichen Konversationsstrukturen
anstatt auf Annahmen bereitstellen.

**Beobachtbarkeit und Diagnose**: Vollständiger Zugriff auf Ereignisströme, Ausführungsprotokolle und Zeitreihenanalysen
ermöglicht KI-gestütztes Debugging. Assistenten können Ereignisse über Komponenten hinweg korrelieren, Leistungsengpässe
identifizieren, Fehler auf Ursachen zurückführen und Optimierungen basierend auf tatsächlichen Betriebsdaten vorschlagen.

**Prozessüberwachung**: Transparenz über Geschäftsprozessdefinitionen, Ausführungszustände und Abschlussverläufe
ermöglicht KI-Assistenten, Anwendungs-Workflows zu verstehen. Dies unterstützt die Prozessoptimierung, Fehleranalyse
und Anleitung zur Implementierung neuer Prozessvarianten.

## Geschäftswert

### KI-gestützter Betrieb und Überwachung

KI-Assistenten können den Live-Plattformstatus für operative Einblicke und Fehlerbehebung abfragen.
Operationsteams erhalten sofortige Antworten über Prozessausführungsstatus, Agenten-Leistungsmetriken,
Ereignisverläufe und Systemzustand, ohne Schnittstellen manuell zu navigieren oder Protokolle zu parsen.
Dies reduziert die durchschnittliche Lösungszeit für Vorfälle (MTTR) und ermöglicht die proaktive Problemidentifizierung
durch KI-gestützte Anomalieerkennung über Konversationsmuster, Agentenverhalten und Geschäftsprozessausführung hinweg.

### Intelligentes Wissensmanagement

Die MCP-Schnittstelle bietet KI-Assistenten Zugriff auf Wissensbasen, Dokumenten-Repositories und RAG-Indizes,
was eine ausgeklügelte Wissensfindung und -analyse ermöglicht. Benutzer können natürlichsprachliche Fragen stellen,
die Informationen aus verteilten Dokumentensammlungen abrufen und synthetisieren, Wissenslücken identifizieren
und Empfehlungen für Inhaltsverbesserungen erhalten. Diese Funktion ist wertvoll für Compliance-Teams, die spezifische
regulatorische Referenzen finden müssen, und Forschende, die große technische Dokumentsammlungen untersuchen.

### Verbesserte Entwicklerproduktivität

Entwickler profitieren von KI-Assistenten mit direktem Plattformzugriff für Code-Generierung und Debugging.
Code-Vorschläge werden anhand aktueller API-Schemas validiert, anstatt generischer Muster, Debugging-Gespräche
beinhalten den tatsächlichen Plattformstatus, und die Testgenerierung verwendet reale Agentenkonfigurationen.
Organisationen berichten von Produktivitätssteigerungen in der Entwicklung von 30-50%, wenn KI-Assistenten
strukturierten Systemzugriff haben. Neue Teammitglieder werden schneller produktiv durch sofortige, kontextbezogene
Anleitung, die die Einarbeitungszeit reduziert und die Abhängigkeit von Dokumentationssuchen eliminiert.

### Prozessanalyse und -optimierung

KI-Assistenten können Geschäftsprozessdefinitionen, Ausführungsverläufe und Leistungsmuster analysieren,
um Optimierungsmöglichkeiten zu identifizieren. Durch Abfragen von Prozessinstanzen, Agenteninteraktionen
und Abschlussmetriken liefern Assistenten umsetzbare Erkenntnisse für Workflow-Verbesserungen, Engpasserkennung
und Ressourcenallokation. Dies unterstützt kontinuierliche Prozessverbesserungsinitiativen und hilft Organisationen,
den ROI von KI-Automatisierungsinvestitionen zu maximieren.

## Implementierungsansatz

Mit der FastMCP-Bibliothek erstellt, generiert der MCP-Server Ressourcen automatisch aus FastAPI-Routendefinitionen
und OpenAPI-Spezifikationen. Der Server wird unter `/mcp` im Haupt-API-Dienst eingebunden und teilt die
Authentifizierungsinfrastruktur, Datenbankverbindungen und den Zugriff auf das Ereignissystem mit REST-Endpunkten.
Nur schreibgeschützte Operationen (GET-Endpunkte) werden exponiert, wodurch eine sichere Entwicklungsschnittstelle
aufrechterhalten wird, die die Plattformbeobachtung ohne Zustandsänderung ermöglicht. Die Authentifizierung
verwendet dieselben OAuth2-/SAML-/LDAP-Identitätsprovider wie REST-APIs, mit hierarchischen Berechtigungsprüfungen,
die Ressourcen basierend auf Benutzerzugriffsrechten filtern. KI-Entwicklungstools konfigurieren MCP-Verbindungen
über `.mcp.json`-Dateien in Projekt-Repositories, wodurch ein automatischer Plattformzugriff während
Entwicklungssitzungen ermöglicht wird. Die Architektur skaliert horizontal mit API-Instanzen, erfordert keine
separate Bereitstellung und fügt dem bestehenden Dienst minimalen Ressourcen-Overhead hinzu.

---
title: MCP-Integration :tada: :100:
index: 1
source_sha: "146fdbe92459c783e30d3b60bcbbbeb12975a3a6f7d1719caf0f346a11c3b474"
---

# MCP-Integration :tada: :100:

::: info **Kurz gesagt – Was ist MCP-Integration?**
Der AI-Hub fungiert als **MCP (Modell-Kontext-Protokoll) Server**, der externen KI-Code-Assistenten und KI-gestützten
Tools ermöglicht, nahtlos mit Ihrer AI-Hub-Instanz über ein standardisiertes Protokoll zu interagieren. Das bedeutet,
dass Ihre bevorzugten KI-Tools direkt auf AI-Hub-APIs zugreifen, den Systemstatus beobachten und kontextbezogene
Unterstützung bieten können, ohne manuellen Datenexport oder komplexe Integrationen.
:::

## Was ist MCP und wie unterstützt der AI-Hub es? :brain:

Das **Modell-Kontext-Protokoll (MCP)** ist ein aufkommender Industriestandard, der es KI-Code-Assistenten und
KI-gestützten Tools ermöglicht, über eine einheitliche Schnittstelle mit externen Diensten und Datenbanken zu
kommunizieren. Stellen Sie es sich als einen universellen Übersetzer vor, der es Ihren KI-Tools ermöglicht,
mit Ihren Geschäftssystemen zu „sprechen“.

Der AI-Hub **stellt seine API-Funktionalität über MCP bereit**, wodurch Tools wie die folgenden in der Lage sind:

- **Claude Code** – Anthropic's KI-Code-Assistent
- **Gemini CLI** – Googles KI-Entwicklungstool
- **Cursor** – KI-gestützter Code-Editor
- **JetBrains AI** – InteliJ's KI-Assistent
- **Benutzerdefinierte KI-Tools** – Jedes Tool, das das MCP-Protokoll unterstützt

direkt mit Ihrer AI-Hub-Instanz zu interagieren, ohne manuelle API-Aufrufe oder komplexe Einrichtungsprozeduren zu erfordern.

## Warum dies ein Wendepunkt für Ihre KI-Strategie ist :trophy:

Diese Integration stellt einen **Paradigmenwechsel** in der Art und Weise dar, wie KI-Tools mit Ihren Unternehmenssystemen zusammenarbeiten können:

**🔗 Nahtlose Integration**: Ihre KI-Code-Assistenten können jetzt direkt auf Ihre AI-Hub-Daten, Agenten und Prozesse zugreifen.
Kein Kopieren und Einfügen von Daten zwischen Systemen oder manuelles Zuführen von Kontext an KI-Tools mehr.

**🧠 Verbesserte KI-Fähigkeiten**: KI-Tools können Vorschläge und Unterstützung basierend auf Echtzeitdaten aus Ihrem AI-Hub bereitstellen, einschließlich:

- Aktuelle Agentenkonfigurationen und Workflows
- Verlauf und Muster der Prozessausführung
- Systemzustand und Leistungsmetriken
- Inhalte der Wissensdatenbank und Abrufergebnisse

**🛡️ Kontrollierter Zugriff**: Die Implementierung des MCP-Servers bietet **schreibgeschützten Zugriff**, um die Sicherheit zu gewährleisten und gleichzeitig den Nutzen zu maximieren.
Ihre KI-Tools können beobachten und analysieren, ohne das Risiko unbeabsichtigter Änderungen.

**⚡ Entwicklerproduktivität**: Entwickler können KI-Assistenten nutzen, die den vollständigen Kontext Ihrer AI-Hub-Einrichtung verstehen,
was zu präziseren Code-Vorschlägen, besserer Debugging-Unterstützung und schnelleren Entwicklungszyklen führt.

**🌐 Ökosystem-Integration**: Dies öffnet die Tür für ein reichhaltiges Ökosystem von KI-gestützten Tools, die mit Ihrem AI-Hub zusammenarbeiten können,
und so eine wirklich integrierte KI-Entwicklungsumgebung schaffen.

::: details **Einrichtung des AI-Hubs als MCP-Server**
## Konfigurationsanforderungen

Um die MCP-Serverfunktionalität in Ihrem AI-Hub zu aktivieren:

1. **MCP-Endpunkt aktivieren**: Der AI-Hub stellt beim Start automatisch einen MCP-Endpunkt unter `/mcp` bereit.
2. **KI-Tools konfigurieren**: Richten Sie Ihre KI-Code-Assistenten so ein, dass sie sich mit Ihrer AI-Hub-Instanz verbinden.

## Beispielkonfiguration für Claude Code

Erstellen oder aktualisieren Sie Ihre `.mcp.json`-Konfigurationsdatei:

```json
{
  "mcpServers": {
    "aihub": {
      "type": "http",
      "url": "http://your-aihub-instance:8000/mcp",
      "description": "AI-Hub MCP Server Integration"
    }
  }
}
```

## Beispielkonfiguration für andere KI-Tools

Die meisten MCP-kompatiblen KI-Tools verwenden ähnliche Konfigurationsmuster:

```json
{
  "mcp_servers": {
    "aihub": {
      "endpoint": "http://your-aihub-instance:8000/mcp",
      "type": "http",
      "read_only": true
    }
  }
}
```

## Verfügbare MCP-Funktionen

Der AI-Hub MCP-Server bietet derzeit:

- **Agenteninformationen**: Zugriff auf Agentenkonfigurationen und -fähigkeiten
- **Prozessüberwachung**: Echtzeit-Status und -Verlauf der Prozessausführung
- **Systemzustand**: Leistungsmetriken und Systemstatus
- **Wissensdatenbank**: Schreibgeschützter Zugriff auf Wissensdatenbankinhalte
- **API-Dokumentation**: Interaktives API-Schema und Endpunktinformationen

## Sicherheitsaspekte

- **Schreibgeschützter Zugriff**: Die aktuelle Implementierung bietet nur Lesezugriff, um die Systemsicherheit zu gewährleisten.
- **Netzwerksicherheit**: Konfigurieren Sie entsprechende Firewall-Regeln und Netzwerkzugriffskontrollen.
- **Authentifizierung**: Stellen Sie sicher, dass für Ihre AI-Hub-Instanz eine ordnungsgemälsse Authentifizierung konfiguriert ist.
- **Überwachung**: Überwachen Sie die Nutzung des MCP-Endpunkts mithilfe der standardmäßigen AI-Hub-Protokollierungs- und Beobachtbarkeitstools.
:::

## Erste Schritte

Um mit der Nutzung der MCP-Integration mit Ihrem AI-Hub zu beginnen:

1. **Stellen Sie sicher, dass Ihr AI-Hub läuft**: Der MCP-Server ist automatisch am `/mcp`-Endpunkt verfügbar.
2. **Konfigurieren Sie Ihre KI-Tools**: Fügen Sie Ihre AI-Hub-Instanz zur MCP-Konfiguration Ihres KI-Tools hinzu.
3. **Beginnen Sie mit der Zusammenarbeit**: Ihre KI-Assistenten können auf den AI-Hub-Kontext zugreifen und erweiterte Unterstützung bieten.

Für erweiterte Konfigurationsoptionen und Fehlerbehebung konsultieren Sie die MCP-Dokumentation Ihres KI-Tools und die AI-Hub-API-Referenz.
