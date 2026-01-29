---
title: API
source_sha: bed624a9f3afac4a0e5c68b13007d642db7210da367d07e8efe95289bbcb4f8f
---

# OpenAI-kompatible REST-API

## Konzept und Zweck

Die OpenAI-kompatible REST-API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI aufbaut und der OpenAI
API-Spezifikation exakt entspricht. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen auf
die Swiss AI-Hub Plattform zu migrieren, ohne den Anwendungscode ändern zu müssen – lediglich die API-Endpunkt-URL und
das Authentifizierungstoken müssen geändert werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt darin, Migrationshürden zu reduzieren und bestehende
Technologieinvestitionen zu schützen. Organisationen können die Swiss AI-Hub Infrastruktur aus Gründen der Datenhoheit,
Kostenkontrolle oder Compliance übernehmen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes
Anwendungsökosystem bewahren.

## Wesentliche Designprinzipien

### Nahtlose Migration und Integration

Die API bietet vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen Funktionen,
einschließlich konversationaler KI (Chat Completions), semantischer Suche (Embeddings), Bilderzeugung und
Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache). Anwendungen, die mit den Python- oder JavaScript-SDKs von
OpenAI entwickelt wurden, funktionieren ohne Änderungen, was eine schnelle Plattformakzeptanz ermöglicht und das
Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Anfrage- und Antwortformate, Streaming-Verhalten und Fehlerbehandlungsmuster.
Organisationen können die Plattform mithilfe bestehender Testsuiten und Migrationsskripte validieren, wodurch
Evaluierungs- und Bereitstellungszeiten beschleunigt werden.

### Anbieterunabhängiger Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, darunter Azure OpenAI,
selbst gehostete Modelle und andere OpenAI-kompatible Dienste. Diese Anbieterneutralität bietet mehrere
Geschäftsvorteile: Organisationen können transparent und ohne Anwendungsänderungen zwischen Modellprovidern wechseln,
Kostenoptimierungsstrategien implementieren, indem Anfragen basierend auf Workload-Charakteristiken an verschiedene
Anbieter weitergeleitet werden, Datenhoheit durch selbst gehostete Modelloptionen aufrechterhalten und hybride
Bereitstellungsmodelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Modellauswahl und -routing erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und Optimierung
ermöglicht, ohne eine Koordination zwischen den Anwendungsteams zu erfordern.

### Erweitertes Modellkonzept: AI-Hub Assistenten

Über die Standard-Sprachmodelle hinaus erweitert der Swiss AI-Hub das OpenAI-Modellkonzept um plattform-eigene
KI-Assistenten (Agents). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs, wodurch
Anwendungen mit komplexen, zustandsbehafteten Agenten-Workflows über dieselbe vertraute Chat-Schnittstelle interagieren
können.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die sich von einfachen LLM-Interaktionen hin zu
orchestrierten Agenten-Workflows entwickeln möchten. Anwendungen können mit dem Aufruf grundlegender Sprachmodelle
beginnen und schrittweise komplexere Agenten übernehmen, ohne architektonische Änderungen vornehmen zu müssen – dieselbe
API-Schnittstelle dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet ein umfassendes Spektrum an KI-Funktionalitäten, die mit modernen LLM-Anwendungen kompatibel sind:

**Konversations-KI**: Vollständige Unterstützung für Chat Completions mit synchronen und Streaming-Antwortmodi, die
interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Gespräche,
Funktionsaufrufe und multimodale Eingaben (Text und Bilder) für sehfähige Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektorrepräsentationen für semantische Suche,
Ähnlichkeitsabgleich und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt Batch-Verarbeitung und
mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bilderzeugung aus Text-Prompts und Audioverarbeitungsfunktionen, einschließlich
Sprache-zu-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-zu-Sprache-Synthese mit
konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modell-Entdeckung**: Die dynamische Modellauflistung ermöglicht Anwendungen, verfügbare LLM-Modelle und AI-Hub
Assistenten zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modell-Governance
unterstützt.

## Geschäftlicher Nutzen

### Reduziertes Migrationsrisiko und Kosten

Organisationen können die Swiss AI-Hub Plattform übernehmen, ohne Anwendungen neu schreiben zu müssen, wodurch
Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams nutzen weiterhin
vertraute OpenAI SDKs und Muster, wodurch Umschulungsaufwand vermieden wird. Diese Kompatibilität schützt Investitionen
in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen zentralen Kontrollpunkt für den Modellzugriff innerhalb der Organisation.
Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne
Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt transparent, was
Kostenoptimierung ermöglicht und Anbieterbindung (Vendor Lock-in) vermeidet.

### Pfad zur progressiven Verbesserung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es
Organisationen, ihre KI-Fähigkeiten schrittweise zu entwickeln. Anwendungen, die für den einfachen Modellzugriff
entwickelt wurden, können mit zunehmender organisatorischer Reife schrittweise fortschrittlichere agentenbasierte
Workflows übernehmen, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Auf FastAPI aufgebaut, fungiert die API als Teil des Hauptplattformdienstes mit zustandsloser Anfragenverarbeitung, die
horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit organisationalen
Identitätsprovidern, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und KI-Assistenten. Die
Anfragen-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während
Assistenten-Interaktionen in Plattformereignisse für die Agentenverarbeitung umgewandelt werden, wobei eine klare
Trennung zwischen externem Modellzugriff und interner Agenten-Orchestrierung aufrechterhalten wird.

## Schlüsselaufgaben

**Authentifizierung und Autorisierung**: Die API-Schicht setzt Sicherheitsgrenzen durch, indem sie Benutzeridentitäten
durch Integration mit organisationalen Identitätsprovidern (OAuth2, OIDC) validiert und rollenbasierte
Zugriffssteuerungsrichtlinien durchsetzt.

**Anfragen-Routing**: Eingehende Anfragen werden validiert, authentifiziert und an die entsprechenden Backend-Dienste
weitergeleitet. Die API fungiert als Fassade, die die Komplexität der verteilten Dienstarchitektur vor den Clients
abstrahiert.

**Protokollübersetzung**: Die API übersetzt zwischen externen Protokollen (HTTP/REST, WebSocket) und internen
ereignisgesteuerten Kommunikationsmustern, wodurch synchrone Client-Erwartungen mit asynchroner Backend-Verarbeitung
überbrückt werden.

**Sitzungsverwaltung**: Für konversationsbasierte Schnittstellen verwaltet die API den Sitzungskontext, indem sie
langlebige Verbindungen verwaltet und die Zustands konsistenz über mehrere Interaktionen hinweg sicherstellt.

## API-Typen und Schnittstellen

Die Swiss AI-Hub Plattform stellt mehrere API-Typen bereit, die jeweils für spezifische Interaktionsmuster und
Anwendungsfälle optimiert sind:

### 1. OpenAI-kompatible REST-API

Eine standardbasierte HTTP-API, die vollständige Kompatibilität mit der OpenAI API-Spezifikation bietet und eine
nahtlose Migration für Anwendungen ermöglicht, die auf OpenAI SDKs basieren. Die API unterstützt Chat Completions,
Embeddings, Bilderzeugung und Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache) mit identischen Endpunktstrukturen
und Anfrage-/Antwortformaten. Dies dient als direkter Ersatz für OpenAI-Endpunkte, sodass bestehende Anwendungen die
Swiss AI-Hub Infrastruktur ohne Code-Änderungen nutzen können. Die API unterstützt sowohl den direkten LLM-Modellzugriff
als auch AI-Hub Assistenten (Agents) mit Streaming- und Nicht-Streaming-Modi für alle Funktionen.

### 2. Agenten-Interaktions-REST-API

Eine native HTTP-API, die speziell für die Verwaltung und Interaktion mit KI-Agenten, Threads (Konversationen),
Prozessen und Plattformressourcen entwickelt wurde. Diese API bietet umfassenden Zugriff auf die vollständigen
Funktionen der Plattform, einschließlich Agenten-Entdeckung und -Konfiguration, Konversations-Lebenszyklusmanagement,
Prozessausführung und -überwachung, Zugriff auf den Ereignisverlauf sowie Benutzer-/Rollenverwaltung. Sie ist optimiert
für die Entwicklung nativer AI-Hub Anwendungen, die die vollständigen Agenten-Orchestrierungs- und
Prozessautomatisierungsfunktionen der Plattform nutzen.

### 3. WebSocket-API

Ein bidirektionaler, Echtzeit-Kommunikationskanal, der Live-Ereignis-Streaming und kontinuierliche Updates für
interaktive Anwendungen ermöglicht. Die WebSocket-API liefert Agenten-Ereignisse, Statusaktualisierungen und
Streaming-Antworten in Echtzeit mit geringer Latenz, wodurch die progressive Anzeige von Agenten-Antworten in
Benutzeroberflächen unterstützt wird. Sie bietet verbindungsbasierte Sitzungsverwaltung mit tokenbasierter
Authentifizierung und automatischer Trennung bei Autorisierungsfehlern. Diese API ist optimiert für
Echtzeit-Benutzeroberflächen, die sofortiges Feedback und Live-Updates während der Agentenausführung erfordern.

### 4. Model Context Protocol (MCP) Server

Ein HTTP-basierter MCP-Server, der AI-Hub API-Endpunkte als Ressourcen und Tools für KI-Entwicklungsassistenten und
Automatisierungstools zugänglich macht. Dies ermöglicht es KI-Codierungsassistenten wie Claude Code und Gemini CLI, den
Plattformstatus abzufragen, Agenten zu inspizieren und während Entwicklungssitzungen mit der AI-Hub API zu interagieren.
Der Server bietet automatische Ressourcen- und Tool-Erkennung von API-Endpunkten, schreibgeschützten Zugriff auf
GET-Endpunkte als MCP-Ressourcen und dynamische Schema-Generierung aus OpenAPI-Spezifikationen.
