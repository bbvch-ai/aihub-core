---
title: API
index: 16
source_sha: "b3d2f6aecb7aff694848c5600025130f6c8f50ea63053754a38a43da7cd72c9b"
---

# OpenAI-kompatible REST API

## Konzept und Zweck

Die OpenAI-kompatible REST API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Unternehmen, bestehende KI-gestützte Anwendungen auf die Swiss AI-Hub Plattform zu migrieren, ohne den Anwendungscode ändern zu müssen – lediglich die API-Endpunkt-URL und der Authentifizierungstoken müssen angepasst werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshemmnissen und dem Schutz bestehender Technologieinvestitionen. Unternehmen können die Swiss AI-Hub Infrastruktur aus Gründen der Datenhoheit, Kostenkontrolle oder Compliance nutzen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes Anwendungsökosystem bewahren.

## Kernprinzipien des Designs

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen Funktionen, einschließlich Konversations-KI (Chat-Vervollständigungen), semantischer Suche (Embeddings), Bildgenerierung und Audioverarbeitung (Sprach-zu-Text und Text-zu-Sprache). Anwendungen, die mit den Python- oder JavaScript-SDKs von OpenAI entwickelt wurden, funktionieren ohne Modifikation, was eine schnelle Plattformadoption ermöglicht und das Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Anfrage- und Antwortformate, Streaming-Verhalten und Fehlerbehandlungsmuster. Unternehmen können die Plattform mithilfe bestehender Testsuiten und Migrationsskripte validieren, was die Evaluierungs- und Bereitstellungszeiten beschleunigt.

### Anbieterneutraler Modellzugriff

Die API abstrahiert zugrunde liegende Modellprovider und unterstützt mehrere LLM-Quellen, einschließlich Azure OpenAI, selbst gehosteter Modelle und anderer OpenAI-kompatibler Dienste. Diese Anbieterneutralität bietet mehrere Geschäftsvorteile: Unternehmen können transparent und ohne Anwendungsänderungen zwischen Modellprovidern wechseln, Kostenoptimierungsstrategien implementieren, indem sie Anfragen basierend auf Workload-Eigenschaften an verschiedene Anbieter weiterleiten, Datenhoheit durch selbst gehostete Modelloptionen aufrechterhalten und hybride Bereitstellungsmodelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Die Modellauswahl und -weiterleitung erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und Optimierung ermöglicht, ohne dass eine Koordination zwischen den Anwendungsteams erforderlich ist.

### Erweitertes Modellkonzept: AI-Hub Assistenten

Über Standard-Sprachmodelle hinaus erweitert der Swiss AI-Hub das OpenAI-Modellkonzept um plattformnative KI-Assistenten (Agenten). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen es Anwendungen, mit komplexen, zustandsbehafteten Agenten-Workflows über dieselbe vertraute Chat-Schnittstelle zu interagieren.

Diese Erweiterung bietet einen Migrationspfad für Unternehmen, die sich von einfachen LLM-Interaktionen zu orchestrierten Agenten-Workflows entwickeln möchten. Anwendungen können zunächst grundlegende Sprachmodelle aufrufen und schrittweise anspruchsvollere Agenten ohne architektonische Änderungen adaptieren – dieselbe API-Schnittstelle dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet ein vollständiges Spektrum an KI-Funktionen, die mit modernen LLM-Anwendungen kompatibel sind:

**Konversations-KI**: Vollständige Unterstützung für Chat-Vervollständigungen mit synchronen und Streaming-Antwortmodi, die interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Konversationen über mehrere Runden, Funktionsaufrufe und multimodale Eingaben (Text und Bilder) für visuell fähige Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektordarstellungen für semantische Suche, Ähnlichkeitsabgleich und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt Batch-Verarbeitung und mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bildgenerierung aus Text-Prompts und Audioverarbeitungsfunktionen, einschließlich Sprach-zu-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-zu-Sprache-Synthese mit konfigurierbaren Stimmen und Streaming-Ausgabe.

**Model Discovery**: Die dynamische Modellauflistung ermöglicht es Anwendungen, verfügbare LLM-Modelle und AI-Hub Assistenten zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modellgovernance unterstützt.

## Geschäftswert

### Reduziertes Migrationsrisiko und -kosten

Unternehmen können die Swiss AI-Hub Plattform ohne Neuschreiben von Anwendungen übernehmen, wodurch Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams verwenden weiterhin vertraute OpenAI SDKs und Muster, wodurch Schulungsaufwand vermieden wird. Diese Kompatibilität bewahrt Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen einzigen Kontrollpunkt für den Modellzugriff im gesamten Unternehmen. Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt transparent, was Kostenoptimierung ermöglicht und eine Anbieterbindung vermeidet.

### Pfad zur schrittweisen Verbesserung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es Unternehmen, ihre KI-Fähigkeiten schrittweise weiterzuentwickeln. Anwendungen, die für den einfachen Modellzugriff entwickelt wurden, können mit zunehmender organisatorischer Reife schrittweise fortschrittlichere agentenbasierte Workflows übernehmen, ohne ein architektonisches Redesign zu erfordern.

## Implementierungsansatz

Basierend auf FastAPI, fungiert die API als Teil des Hauptplattformdienstes mit zustandsloser Anfragenverarbeitung, die eine horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit den Identitätsprovidern der Organisation, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und AI-Assistenten. Die Anfragen-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während Assistenten-Interaktionen in Plattform-Events für die Agentenverarbeitung umgewandelt werden, wodurch eine klare Trennung zwischen externem Modellzugriff und interner Agenten-Orchestrierung aufrechterhalten wird.

---
title: APIs
index: 1
source_sha: "b3d2f6aecb7aff694848c5600025130f6c8f50ea63053754a38a43da7cd72c9b"
---

# APIs

Die API-Schicht dient als zentrales Gateway für alle externen Interaktionen mit der Swiss AI-Hub Plattform. Sie bietet sichere, standardbasierte Schnittstellen für Benutzeranwendungen, administrative Tools und Integrationsendpunkte.

## Zweck und Geltungsbereich

Die API-Komponente umfasst alle programmatischen Schnittstellen, die es externen Systemen und Benutzern ermöglichen, mit der Plattform zu interagieren. Dazu gehören REST APIs für synchrone Operationen, WebSocket-Verbindungen für Echtzeitkommunikation und spezialisierte Endpunkte für Authentifizierung, Autorisierung und Ressourcenverwaltung.

## Hauptverantwortlichkeiten

**Authentifizierung und Autorisierung**: Die API-Schicht setzt Sicherheitsgrenzen durch, validiert Benutzeridentitäten durch Integration mit organisationalen Identitätsprovidern (OAuth2, OIDC) und erzwingt rollenbasierte Zugriffssteuerungsrichtlinien.

**Anfragen-Routing**: Eingehende Anfragen werden validiert, authentifiziert und an die entsprechenden Backend-Dienste weitergeleitet. Die API fungiert als Fassade, die die Komplexität der verteilten Dienstarchitektur vor den Clients abstrahiert.

**Protokollübersetzung**: Die API übersetzt zwischen externen Protokollen (HTTP/REST, WebSocket) und internen ereignisgesteuerten Kommunikationsmustern und überbrückt so synchrone Client-Erwartungen mit asynchroner Backend-Verarbeitung.

**Sitzungsverwaltung**: Für konversationelle Schnittstellen verwaltet die API den Sitzungskontext, indem sie langlebige Verbindungen verwaltet und die Zustands konsistenz über mehrere Interaktionen hinweg sicherstellt.

## API-Typen und Schnittstellen

Die Swiss AI-Hub Plattform stellt mehrere API-Typen bereit, die jeweils für spezifische Interaktionsmuster und Anwendungsfälle optimiert sind:

### 1. OpenAI-kompatible REST API

Eine standardbasierte HTTP API, die vollständige Kompatibilität mit der OpenAI API-Spezifikation bietet und eine nahtlose Migration für Anwendungen ermöglicht, die auf OpenAI SDKs basieren. Die API unterstützt Chat-Vervollständigungen, Embeddings, Bildgenerierung und Audioverarbeitung (Sprach-zu-Text und Text-zu-Sprache) mit identischen Endpunktstrukturen und Anfragen-/Antwortformaten. Dies dient als direkter Ersatz für OpenAI-Endpunkte, sodass bestehende Anwendungen die Swiss AI-Hub Infrastruktur ohne Codeänderungen nutzen können. Die API unterstützt sowohl den direkten LLM-Modellzugriff als auch AI-Hub Assistenten (Agenten) mit Streaming- und Nicht-Streaming-Modi für alle Funktionen.

### 2. Agenten-Interaktions-REST-API

Eine native HTTP API, die speziell für die Verwaltung und Interaktion mit KI-Agenten, Threads (Konversationen), Prozessen und Plattformressourcen entwickelt wurde. Diese API bietet umfassenden Zugriff auf die vollständigen Funktionen der Plattform, einschließlich Agenten-Discovery und -Konfiguration, Konversations-Lebenszyklusmanagement, Prozessausführung und -überwachung, Zugriff auf den Ereignisverlauf sowie Benutzer-/Rollenadministration. Sie ist optimiert für die Entwicklung nativer AI-Hub Anwendungen, die die vollständigen Agenten-Orchestrierungs- und Prozessautomatisierungsfunktionen der Plattform nutzen.

### 3. WebSocket API

Ein bidirektionaler Echtzeit-Kommunikationskanal, der Live-Event-Streaming und kontinuierliche Updates für interaktive Anwendungen ermöglicht. Die WebSocket API liefert Agentenereignisse, Statusaktualisierungen und Streaming-Antworten in Echtzeit mit geringer Latenz und unterstützt die progressive Anzeige von Agentenantworten in Benutzeroberflächen. Sie bietet verbindungsbasierte Sitzungsverwaltung mit tokenbasierter Authentifizierung und automatischer Trennung bei Autorisierungsfehlern. Diese API ist optimiert für Echtzeit-Benutzeroberflächen, die sofortiges Feedback und Live-Updates während der Agentenausführung erfordern.

### 4. Model Context Protocol (MCP) Server

Ein HTTP-basierter MCP-Server, der AI-Hub API-Endpunkte als Ressourcen und Tools für KI-Entwicklungsassistenten und Automatisierungstools verfügbar macht. Dies ermöglicht es KI-Codierungsassistenten wie Claude Code und Gemini CLI, den Plattformzustand abzufragen, Agenten zu inspizieren und während Entwicklungssitzungen mit der AI-Hub API zu interagieren. Der Server bietet automatische Ressourcen- und Tool-Discovery aus API-Endpunkten, schreibgeschützten Zugriff auf GET-Endpunkte als MCP-Ressourcen und dynamische Schema-Generierung aus OpenAPI-Spezifikationen.
