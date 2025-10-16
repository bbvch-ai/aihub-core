---
title: API
index: 16
source_sha: "0978b32cafaa78012e6c6ef4fe79c68f9696625e50421310e774ad49e3231ef6"
---

# OpenAI-kompatible REST-API

## Konzept und Zweck

Die OpenAI-kompatible REST-API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI-API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen ohne Änderung des Anwendungscodes auf die Swiss AI-Hub Plattform zu migrieren – lediglich die API-Endpunkt-URL und der Authentifizierungstoken müssen geändert werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshemmnissen und dem Schutz bestehender Technologieinvestitionen. Organisationen können die Swiss AI-Hub Infrastruktur für Datenhoheit, Kostenkontrolle oder Compliance-Gründe nutzen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes Anwendungsökosystem bewahren.

## Zentrale Designprinzipien

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen Funktionen, einschließlich Konversations-KI (Chat-Completions), semantischer Suche (Embeddings), Bildgenerierung und Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache). Anwendungen, die mit den Python- oder JavaScript-SDKs von OpenAI entwickelt wurden, funktionieren ohne Änderungen, was eine schnelle Plattformakzeptanz ermöglicht und das Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Anfrage- und Antwortformate, Streaming-Verhalten und Fehlerbehandlungsmuster. Organisationen können die Plattform mithilfe bestehender Testsuiten und Migrationsskripte validieren, wodurch Bewertungs- und Bereitstellungszeiten beschleunigt werden.

### Anbieterneutraler Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, darunter Azure OpenAI, selbst gehostete Modelle und andere OpenAI-kompatible Dienste. Diese Anbieterneutralität bietet mehrere Geschäftsvorteile: Organisationen können transparent zwischen Modellprovidern wechseln, ohne Anwendungsänderungen vornehmen zu müssen, Kostenoptimierungsstrategien implementieren, indem sie Anfragen basierend auf Workload-Eigenschaften an verschiedene Anbieter weiterleiten, Datenhoheit durch selbst gehostete Modelloptionen aufrechterhalten und hybride Bereitstellungsmodelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Die Modellauswahl und das Routing erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und Optimierung ohne Abstimmungsbedarf zwischen den Anwendungsteams ermöglicht.

### Erweitertes Modellkonzept: AI-Hub Assistenten

Über Standard-Sprachmodelle hinaus erweitert der Swiss AI-Hub das OpenAI-Modellkonzept um plattformnative KI-Assistenten (Agenten). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen Anwendungen die Interaktion mit komplexen, zustandsbehafteten Agenten-Workflows über dieselbe vertraute Chat-Schnittstelle.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die sich von einfachen LLM-Interaktionen hin zu orchestrierten Agenten-Workflows entwickeln möchten. Anwendungen können mit dem Aufruf einfacher Sprachmodelle beginnen und schrittweise anspruchsvollere Agenten übernehmen, ohne architektonische Änderungen vornehmen zu müssen – dieselbe API-Schnittstelle dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet ein vollständiges Spektrum an KI-Funktionen, die mit modernen LLM-Anwendungen kompatibel sind:

**Konversations-KI**: Vollständige Unterstützung für Chat-Completions mit synchronen und Streaming-Antwortmodi, die interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Konversationen über mehrere Runden, Funktionsaufrufe und multimodale Eingaben (Text und Bilder) für sehfähige Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektordarstellungen für semantische Suche, Ähnlichkeitsabgleich und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt die Stapelverarbeitung und mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bildgenerierung aus Text-Prompts und Audioverarbeitungsfunktionen, einschließlich Sprache-zu-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-zu-Sprache-Synthese mit konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modellentdeckung**: Dynamische Modellauflistung ermöglicht Anwendungen, verfügbare LLM-Modelle und AI-Hub Assistenten zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modell-Governance unterstützt.

## Geschäftswert

### Reduziertes Migrationsrisiko und -kosten

Organisationen können die Swiss AI-Hub Plattform übernehmen, ohne Anwendungen neu schreiben zu müssen, wodurch Migrationsprojektkosten entfallen und das Akzeptanzrisiko reduziert wird. Bestehende Entwicklungsteams verwenden weiterhin vertraute OpenAI SDKs und Muster, wodurch Umschulungsaufwand vermieden wird. Diese Kompatibilität schützt Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen zentralen Kontrollpunkt für den Modellzugriff innerhalb der gesamten Organisation. Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt transparent, was Kostenoptimierung ermöglicht und Vendor Lock-in vermeidet.

### Pfad der progressiven Verbesserung

Die vereinheitlichte Schnittstelle zwischen einfachen LLM-Modellen und anspruchsvollen KI-Assistenten ermöglicht es Organisationen, ihre KI-Fähigkeiten schrittweise weiterzuentwickeln. Anwendungen, die für den einfachen Modellzugriff entwickelt wurden, können mit zunehmender organisatorischer Reife schrittweise fortschrittlichere agentenbasierte Workflows übernehmen, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Die auf FastAPI basierende API ist Teil des Hauptplattformdienstes und verfügt über eine zustandslose Anfragenverarbeitung, die horizontales Skalieren ermöglicht. Die Authentifizierung integriert sich über OAuth2 in die Identitätsprovider der Organisation, und hierarchische Berechtigungen steuern den Zugriff sowohl auf LLM-Modelle als auch auf KI-Assistenten. Die Anfragen-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während Assistenten-Interaktionen in Plattformereignisse für die Agentenverarbeitung umgewandelt werden, wodurch eine klare Trennung zwischen externem Modellzugriff und interner Agenten-Orchestrierung aufrechterhalten wird.

---
title: APIs
index: 1
source_sha: "0978b32cafaa78012e6c6ef4fe79c68f9696625e50421310e774ad49e3231ef6"
---

# APIs

![System Overview - APIs](../../../../../../media/architecture/system_overview/system-overview-highlight-api.png)

Die API-Schicht dient als zentrales Gateway für alle externen Interaktionen mit der Swiss AI-Hub Plattform. Sie bietet sichere, standardbasierte Schnittstellen für Benutzeranwendungen, administrative Tools und Integrationsendpunkte.

## Zweck und Geltungsbereich

Die API-Komponente umfasst alle programmatischen Schnittstellen, die es externen Systemen und Benutzern ermöglichen, mit der Plattform zu interagieren. Dies beinhaltet REST-APIs für synchrone Operationen, WebSocket-Verbindungen für Echtzeitkommunikation und spezialisierte Endpunkte für Authentifizierung, Autorisierung und Ressourcenmanagement.

## Hauptaufgaben

**Authentifizierung und Autorisierung**: Die API-Schicht setzt Sicherheitsgrenzen durch, validiert Benutzeridentitäten durch Integration mit den Identitätsprovidern der Organisation (OAuth2, OIDC) und erzwingt rollenbasierte Zugriffssteuerungsrichtlinien.

**Anfragen-Routing**: Eingehende Anfragen werden validiert, authentifiziert und an die entsprechenden Backend-Dienste weitergeleitet. Die API fungiert als Fassade, die die Komplexität der verteilten Dienstarchitektur vor den Clients abstrahiert.

**Protokollübersetzung**: Die API übersetzt zwischen externen Protokollen (HTTP/REST, WebSocket) und internen ereignisgesteuerten Kommunikationsmustern und überbrückt so synchrone Client-Erwartungen mit asynchroner Backend-Verarbeitung.

**Sitzungsmanagement**: Für Konversationsschnittstellen pflegt die API den Sitzungskontext, verwaltet langlebige Verbindungen und gewährleistet die Zustandskonsistenz über mehrere Interaktionen hinweg.

## API-Typen und Schnittstellen

Die Swiss AI-Hub Plattform exponiert mehrere API-Typen, die jeweils für spezifische Interaktionsmuster und Anwendungsfälle optimiert sind:

### 1. OpenAI-kompatible REST-API

Eine standardbasierte HTTP-API, die vollständige Kompatibilität mit der OpenAI-API-Spezifikation bietet und eine nahtlose Migration für Anwendungen ermöglicht, die auf OpenAI SDKs basieren. Die API unterstützt Chat-Completions, Embeddings, Bildgenerierung und Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache) mit identischen Endpunktstrukturen und Anfrage-/Antwortformaten. Dies dient als Drop-in-Ersatz für OpenAI-Endpunkte, sodass bestehende Anwendungen die Swiss AI-Hub Infrastruktur ohne Codeänderungen nutzen können. Die API unterstützt sowohl den direkten LLM-Modellzugriff als auch AI-Hub Assistenten (Agenten), mit Streaming- und Nicht-Streaming-Modi für alle Funktionen.

### 2. REST-API für Agenteninteraktionen

Eine native HTTP-API, die speziell für die Verwaltung und Interaktion mit KI-Agenten, Threads (Konversationen), Prozessen und Plattformressourcen entwickelt wurde. Diese API bietet umfassenden Zugriff auf die vollständigen Funktionen der Plattform, einschließlich Agenten-Entdeckung und -Konfiguration, Lebenszyklusmanagement von Konversationen, Prozessausführung und -überwachung, Zugriff auf den Ereignisverlauf sowie Benutzer-/Rollenadministration. Sie ist für die Entwicklung nativer AI-Hub Anwendungen optimiert, die die vollständigen Agenten-Orchestrierungs- und Prozessautomatisierungsfunktionen der Plattform nutzen.

### 3. WebSocket-API

Ein bidirektionaler Echtzeit-Kommunikationskanal, der Live-Event-Streaming und kontinuierliche Updates für interaktive Anwendungen ermöglicht. Die WebSocket-API liefert Agentenereignisse, Statusaktualisierungen und Streaming-Antworten in Echtzeit mit geringer Latenz und unterstützt die progressive Anzeige von Agentenantworten in Benutzeroberflächen. Sie bietet verbindungsbasiertes Sitzungsmanagement mit tokenbasierter Authentifizierung und automatischer Trennung bei Autorisierungsfehlern. Diese API ist für Echtzeit-Benutzeroberflächen optimiert, die sofortiges Feedback und Live-Updates während der Agentenausführung erfordern.

### 4. Model Context Protocol (MCP) Server

Ein HTTP-basierter MCP-Server, der AI-Hub API-Endpunkte als Ressourcen und Tools für KI-Entwicklungsassistenten und Automatisierungstools bereitstellt. Dies ermöglicht es KI-Codierungsassistenten wie Claude Code und Gemini CLI, den Plattformstatus abzufragen, Agenten zu inspizieren und während der Entwicklungssitzungen mit der AI-Hub API zu interagieren. Der Server bietet automatische Ressourcen- und Tool-Erkennung von API-Endpunkten, schreibgeschützten Zugriff auf GET-Endpunkte als MCP-Ressourcen und dynamische Schema-Generierung aus OpenAPI-Spezifikationen.
