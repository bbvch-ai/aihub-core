---
title: API
source_sha: 30be89c27c1a7ba5aeebca467ca64423148175ef99cfe067bff92d5e78c072b0
---

# OpenAI-kompatible REST-API

## Konzept und Zweck

Die OpenAI-kompatible REST-API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI
API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen
ohne Änderung des Anwendungscodes auf die Swiss AI Hub-Plattform zu migrieren – lediglich die API-Endpunkt-URL und der
Authentifizierungstoken müssen geändert werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshürden und dem Schutz
bestehender Technologieinvestitionen. Organisationen können die Swiss AI Hub-Infrastruktur aus Gründen der Datenhoheit,
Kostenkontrolle oder Compliance übernehmen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes
Anwendungsökosystem beibehalten.

## Zentrale Designprinzipien

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen
Funktionen, einschließlich konversationeller KI (Chat Completions), semantischer Suche (Embeddings), Bilderzeugung und
Audioverarbeitung (Speech-to-Text und Text-to-Speech). Anwendungen, die mit OpenAI's Python- oder JavaScript-SDKs
entwickelt wurden, funktionieren ohne Änderungen, was eine schnelle Plattformakzeptanz ermöglicht und das
Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Anfrage- und Antwortformate, Streaming-Verhalten und Fehlerbehandlungsmuster.
Organisationen können die Plattform mit bestehenden Test-Suites und Migrationsskripten validieren, was die Evaluierungs-
und Deployment-Zeiten beschleunigt.

### Anbieterneutraler Modellzugriff

Die API abstrahiert zugrunde liegende Modellprovider und unterstützt mehrere LLM-Quellen, darunter Swiss LLM Cloud,
selbst gehostete vLLM-Modelle und andere OpenAI-kompatible Services. Diese Anbieterneutralität bietet mehrere
Geschäftsvorteile: Organisationen können transparent zwischen Modellprovidern wechseln, ohne Anwendungsänderungen
vornehmen zu müssen; Kostenoptimierungsstrategien implementieren, indem Anfragen basierend auf Workload-Charakteristiken
an verschiedene Anbieter weitergeleitet werden; Datenhoheit durch selbst gehostete Modelloptionen aufrechterhalten und
hybride Deployment-Modelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Die Modellauswahl und das Routing erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und
Optimierung ermöglicht, ohne eine Koordination zwischen den Anwendungsteams zu erfordern.

### Erweitertes Modellkonzept: Swiss AI Hub Assistants

Über Standard-Sprachmodelle hinaus erweitert der Swiss AI Hub das OpenAI-Modellkonzept um plattformeigene KI-Assistenten
(Agents). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen es
Anwendungen, mit komplexen, zustandsbehafteten Agent-Workflows über dieselbe vertraute Chat-Schnittstelle zu
interagieren.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die von einfachen LLM-Interaktionen zu orchestrierten
Agent-Workflows übergehen möchten. Anwendungen können mit dem Aufruf grundlegender Sprachmodelle beginnen und
schrittweise anspruchsvollere Agents ohne architektonische Änderungen einführen – dieselbe API-Schnittstelle dient
beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet eine umfassende KI-Funktionalität, die mit modernen LLM-Anwendungen kompatibel ist:

**Konversationelle KI**: Volle Unterstützung für Chat Completions mit synchronen und Streaming-Antwortmodi, die
interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Konversationen,
Function Calling und multimodale Eingaben (Text und Bilder) für visuell-fähige Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektorrepräsentationen für die semantische Suche,
Ähnlichkeitsabgleiche und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt Batch-Verarbeitung und
mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bilderzeugung aus Textprompts und Audioverarbeitungsfunktionen, einschließlich
Speech-to-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-to-Speech-Synthese mit
konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modell-Discovery**: Dynamische Modellauflistung ermöglicht es Anwendungen, verfügbare LLM-Modelle und Swiss AI Hub
Assistants zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modell-Governance unterstützt.

## Geschäftlicher Nutzen

### Reduziertes Migrationsrisiko und -kosten

Organisationen können die Swiss AI Hub-Plattform übernehmen, ohne Anwendungen neu schreiben zu müssen, wodurch
Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams verwenden
weiterhin vertraute OpenAI-SDKs und -Muster, wodurch Umschulungsaufwand vermieden wird. Diese Kompatibilität bewahrt
Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen einzigen Kontrollpunkt für den Modellzugriff innerhalb der gesamten
Organisation. Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien
implementieren, ohne Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt
transparent, was Kostenoptimierung ermöglicht und Vendor Lock-in vermeidet.

### Pfad zur progressiven Erweiterung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es
Organisationen, ihre KI-Fähigkeiten inkrementell weiterzuentwickeln. Anwendungen, die für den einfachen Modellzugriff
entwickelt wurden, können schrittweise fortschrittlichere agentenbasierte Workflows einführen, wenn die organisationale
Reife zunimmt, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Die auf FastAPI basierende API operiert als Teil des Hauptplattformdienstes mit zustandsloser Anfragenverarbeitung, die
eine horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit organisationalen
Identitätsprovidern, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und Swiss AI Hub Assistants.
Die Anfragen-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während sie
Assistant-Interaktionen in Plattformereignisse für die Agent-Verarbeitung umwandelt, wodurch eine klare Trennung
zwischen externem Modellzugriff und interner Agent-Orchestrierung aufrechterhalten wird.

## Hauptaufgaben

**Authentifizierung und Autorisierung**: Die API-Schicht setzt Sicherheitsgrenzen durch, validiert Benutzeridentitäten
durch Integration mit organisationalen Identitätsprovidern (OAuth2, OIDC) und erzwingt rollenbasierte
Zugriffssteuerungsrichtlinien.

**Anfrage-Routing**: Eingehende Anfragen werden validiert, authentifiziert und an die entsprechenden Backend-Services
weitergeleitet. Die API fungiert als Fassade, die die Komplexität der verteilten Service-Architektur vor Clients
abstrahiert.

**Protokollübersetzung**: Die API übersetzt zwischen externen Protokollen (HTTP/REST, WebSocket) und internen
ereignisgesteuerten Kommunikationsmustern und überbrückt so synchrone Client-Erwartungen mit asynchroner
Backend-Verarbeitung.

**Sitzungsverwaltung**: Für konversationelle Schnittstellen verwaltet die API den Sitzungskontext, indem sie langlebige
Verbindungen verwaltet und die Zustandskonsistenz über mehrere Interaktionen hinweg sicherstellt.

## API-Typen und -Schnittstellen

Die Swiss AI Hub-Plattform stellt mehrere API-Typen bereit, die jeweils für spezifische Interaktionsmuster und
Anwendungsfälle optimiert sind:

### 1. OpenAI-kompatible REST-API

Eine standardbasierte HTTP-API, die volle Kompatibilität mit der OpenAI-API-Spezifikation bietet und eine nahtlose
Migration für auf OpenAI SDKs basierende Anwendungen ermöglicht. Die API unterstützt Chat Completions, Embeddings,
Bilderzeugung und Audioverarbeitung (Speech-to-Text und Text-to-Speech) mit identischen Endpunktstrukturen und
Anfrage-/Antwortformaten. Dies dient als Drop-in-Ersatz für OpenAI-Endpunkte, sodass bestehende Anwendungen die Swiss
Swiss AI Hub-Infrastruktur ohne Codeänderungen nutzen können. Die API unterstützt sowohl den direkten LLM-Modellzugriff
als auch Swiss AI Hub Assistants (Agents), mit Streaming- und Nicht-Streaming-Modi für alle Funktionen.

### 2. Agenten-Interaktions-REST-API

Eine native HTTP-API, die speziell für die Verwaltung und Interaktion mit KI-Agenten, Threads (Konversationen),
Prozessen und Plattformressourcen entwickelt wurde. Diese API bietet umfassenden Zugriff auf die vollen Fähigkeiten der
Plattform, einschließlich Agent-Discovery und -Konfiguration, Konversations-Lebenszyklusmanagement, Prozessausführung
und -überwachung, Zugriff auf den Ereignisverlauf sowie Benutzer-/Rollenadministration. Sie ist optimiert für die
Entwicklung nativer Swiss AI Hub-Anwendungen, die die vollständigen Agent-Orchestrierungs- und
Prozessautomatisierungsfunktionen der Plattform nutzen.

### 3. WebSocket-API

Ein bidirektionaler Echtzeit-Kommunikationskanal, der Live-Event-Streaming und kontinuierliche Updates für interaktive
Anwendungen ermöglicht. Die WebSocket-API liefert Agent-Ereignisse, Statusaktualisierungen und Streaming-Antworten in
Echtzeit mit geringer Latenz, was die progressive Anzeige von Agent-Antworten in Benutzeroberflächen unterstützt. Sie
bietet verbindungsbasierte Sitzungsverwaltung mit tokenbasierter Authentifizierung und automatischer Trennung bei
Autorisierungsfehlern. Diese API ist optimiert für Echtzeit-Benutzeroberflächen, die sofortiges Feedback und
Live-Updates während der Agent-Ausführung erfordern.

### 4. Model Context Protocol (MCP) Server

Ein HTTP-basierter MCP-Server, der Swiss AI Hub-API-Endpunkte als Ressourcen und Tools für KI-Entwicklungsassistenten
und Automatisierungstools bereitstellt. Dies ermöglicht es KI-Codierungsassistenten wie Claude Code und Gemini CLI, den
Plattformstatus abzufragen, Agents zu inspizieren und während Entwicklungssitzungen mit der Swiss AI Hub-API zu
interagieren. Der Server bietet automatische Ressourcen- und Tool-Discovery von API-Endpunkten, schreibgeschützten
Zugriff auf GET-Endpunkte als MCP-Ressourcen und dynamische Schema-Generierung aus OpenAPI-Spezifikationen.
