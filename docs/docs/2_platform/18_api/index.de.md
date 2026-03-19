```
---
title: API
source_sha: "d6fd723f2687f584e2f9cc75575dc85a5fd51296aa07263e6b529b1bf2644ad3"
---

# OpenAI-kompatible REST API

## Konzept und Zweck

Die OpenAI-kompatible REST API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen auf die Swiss AI Hub Plattform zu migrieren, ohne den Anwendungscode zu ändern – lediglich die API-Endpunkt-URL und der Authentifizierungs-Token müssen angepasst werden.

Der strategische Wert dieser Kompatibilitätsebene liegt in der Reduzierung von Migrationshemmnissen und dem Schutz bestehender Technologieinvestitionen. Organisationen können die Swiss AI Hub-Infrastruktur aus Gründen der Datensouveränität, Kostenkontrolle oder Compliance nutzen und dabei ihr auf OpenAI SDKs und Bibliotheken aufgebautes Anwendungsökosystem bewahren.

## Grundlegende Designprinzipien

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen Funktionen, einschliesslich konversationeller KI (Chat-Vervollständigungen), semantischer Suche (Embeddings), Bilderzeugung und Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache). Anwendungen, die mit den Python- oder JavaScript-SDKs von OpenAI entwickelt wurden, funktionieren ohne Änderungen, was eine schnelle Plattformadoption ermöglicht und das Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Anfrage- und Antwortformate, Streaming-Verhalten und Fehlerbehandlungsmuster. Organisationen können die Plattform mit vorhandenen Test-Suites und Migrationsskripten validieren, was die Evaluierungs- und Deployment-Zeiten beschleunigt.

### Anbieterneutraler Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, einschliesslich Swiss LLM Cloud, selbst gehostete vLLM-Modelle und andere OpenAI-kompatible Services. Diese Anbieterneutralität bietet mehrere geschäftliche Vorteile: Organisationen können transparent und ohne Anwendungsänderungen zwischen Modellprovidern wechseln, Kostenoptimierungsstrategien implementieren, indem Anfragen basierend auf den Workload-Eigenschaften an verschiedene Anbieter geleitet werden, Datensouveränität durch selbst gehostete Modelloptionen wahren und hybride Deployment-Modelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Modellauswahl und -routing erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und Optimierung ermöglicht, ohne dass eine Koordination zwischen den Anwendungsteams erforderlich ist.

### Erweitertes Modellkonzept: Swiss AI Hub KI-Assistenten

Über standardmässige Sprachmodelle hinaus erweitert der Swiss AI Hub das OpenAI-Modellkonzept um plattformnative KI-Assistenten (Agents). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen es Anwendungen, mit komplexen, zustandsbehafteten Agent-Workflows über dieselbe vertraute Chat-Oberfläche zu interagieren.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die von einfachen LLM-Interaktionen zu orchestrierten Agent-Workflows übergehen möchten. Anwendungen können zunächst grundlegende Sprachmodelle aufrufen und schrittweise anspruchsvollere Agents adoptieren, ohne architektonische Änderungen vornehmen zu müssen – dieselbe API-Schnittstelle dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet eine vollständige Palette an KI-Funktionalität, die mit modernen LLM-Anwendungen kompatibel ist:

**Konversations-KI**: Vollständige Unterstützung für Chat-Vervollständigungen mit synchronen und Streaming-Antwortmodi, die interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Konversationen, Funktionsaufrufe und multimodale Eingaben (Text und Bilder) für visuell-fähige Modelle.

**Semantische Suche**: Die Einbettungsgenerierung wandelt Text in Vektorrepräsentationen für die semantische Suche, Ähnlichkeitsabgleiche und Retrieval-Augmented Generation (RAG)-Workflows um. Diese Funktion unterstützt die Stapelverarbeitung und mehrere Konfigurationen für Einbettungsmodelle.

**Multimodale Generierung**: Bilderzeugung aus Text-Prompts und Audioverarbeitungsfunktionen, einschliesslich Sprache-zu-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-zu-Sprache-Synthese mit konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modellentdeckung**: Die dynamische Modellauflistung ermöglicht es Anwendungen, verfügbare LLM-Modelle und Swiss AI Hub KI-Assistenten zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modell-Governance unterstützt.

## Geschäftlicher Nutzen

### Reduziertes Migrationsrisiko und Kosten

Organisationen können die Swiss AI Hub Plattform adoptieren, ohne Anwendungen neu schreiben zu müssen, wodurch Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams nutzen weiterhin vertraute OpenAI SDKs und Muster, wodurch Schulungsaufwand vermieden wird. Diese Kompatibilität schützt Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsebene bietet einen einzigen Kontrollpunkt für den Modellzugriff innerhalb der Organisation. Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt transparent, was Kostenoptimierung ermöglicht und die Anbieterbindung vermeidet.

### Pfad zur progressiven Weiterentwicklung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es Organisationen, ihre KI-Funktionen schrittweise zu erweitern. Anwendungen, die für den einfachen Modellzugriff konzipiert wurden, können bei zunehmender Reife der Organisation schrittweise fortgeschrittenere agentenbasierte Workflows adoptieren, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Die auf FastAPI basierende API ist Teil des Hauptplattformdienstes und ermöglicht mit ihrer zustandslosen Anfragenbearbeitung eine horizontale Skalierung. Die Authentifizierung integriert sich über OAuth2 in die Identitätsprovider der Organisation, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und KI-Assistenten. Die Anfragerouting-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während Interaktionen mit Assistenten in Plattform-Events für die Agent-Verarbeitung umgewandelt werden, wodurch eine klare Trennung zwischen externem Modellzugriff und interner Agent-Orchestrierung gewährleistet wird.

## Kernaufgaben

### Authentifizierung und Autorisierung

Die API-Schicht erzwingt Sicherheitsgrenzen, indem sie Benutzeridentitäten durch die Integration mit organisatorischen Identitätsprovidern (OAuth2, OIDC) validiert und rollenbasierte Zugriffsrichtlinien durchsetzt.

### Anfragerouting

Eingehende Anfragen werden validiert, authentifiziert und an die entsprechenden Backend-Services weitergeleitet. Die API fungiert als Fassade, die die Komplexität der verteilten Servicearchitektur vor Clients abstrahiert.

### Protokollübersetzung

Die API übersetzt zwischen externen Protokollen (HTTP/REST, WebSocket) und internen ereignisgesteuerten Kommunikationsmustern und überbrückt so synchrone Client-Erwartungen mit asynchroner Backend-Verarbeitung.

### Sitzungsverwaltung

Für konversationelle Schnittstellen verwaltet die API den Sitzungskontext, indem sie langlebige Verbindungen aufrechterhält und die Konsistenz des Zustands über mehrere Interaktionen hinweg sicherstellt.

## API-Typen und -Schnittstellen

Die Swiss AI Hub Plattform bietet mehrere API-Typen, die jeweils für spezifische Interaktionsmuster und Anwendungsfälle optimiert sind:

### 1. OpenAI-kompatible REST API

Eine standardbasierte HTTP-API, die vollständige Kompatibilität mit der OpenAI API-Spezifikation bietet und eine nahtlose Migration für Anwendungen ermöglicht, die auf OpenAI SDKs basieren. Die API unterstützt Chat-Vervollständigungen, Embeddings, Bilderzeugung und Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache) mit identischen Endpunktstrukturen und Anfrage-/Antwortformaten. Dies dient als Drop-in-Ersatz für OpenAI-Endpunkte, sodass bestehende Anwendungen die Swiss AI Hub-Infrastruktur ohne Codeänderungen nutzen können. Die API unterstützt sowohl den direkten LLM-Modellzugriff als auch Swiss AI Hub KI-Assistenten (Agents), mit Streaming- und Nicht-Streaming-Modi für alle Funktionen.

### 2. Agenten-Interaktions-REST-API

Eine native HTTP-API, die speziell für die Verwaltung und Interaktion mit KI-Agents, Threads (Konversationen), Prozessen und Plattformressourcen entwickelt wurde. Diese API bietet umfassenden Zugriff auf die vollständigen Funktionen der Plattform, einschliesslich Agent-Entdeckung und -Konfiguration, Lebenszyklusverwaltung von Konversationen, Prozessausführung und -überwachung, Zugriff auf den Ereignisverlauf sowie Benutzer-/Rollenverwaltung. Sie ist optimiert für die Entwicklung nativer Swiss AI Hub-Anwendungen, die die vollständigen Funktionen der Plattform für Agenten-Orchestrierung und Prozessautomatisierung nutzen.

### 3. WebSocket API

Ein bidirektionaler Echtzeit-Kommunikationskanal, der Live-Event-Streaming und kontinuierliche Updates für interaktive Anwendungen ermöglicht. Die WebSocket API liefert Agent-Ereignisse, Statusaktualisierungen und Streaming-Antworten in Echtzeit und mit geringer Latenz, was die progressive Anzeige von Agent-Antworten in Benutzeroberflächen unterstützt. Sie bietet eine verbindungsbasierte Sitzungsverwaltung mit Token-basierter Authentifizierung und automatischer Trennung bei Autorisierungsfehlern. Diese API ist optimiert für Echtzeit-Benutzeroberflächen, die sofortiges Feedback und Live-Updates während der Agent-Ausführung erfordern.

### 4. Model Context Protocol (MCP) Server

Ein HTTP-basierter MCP-Server, der Swiss AI Hub API-Endpunkte als Ressourcen und Tools für KI-Entwicklungsassistenten und Automatisierungstools zugänglich macht. Dies ermöglicht es KI-Codierungsassistenten wie Claude Code und Gemini CLI, den Plattformstatus abzufragen, Agents zu inspizieren und während Entwicklungssitzungen mit der Swiss AI Hub API zu interagieren. Der Server bietet eine automatische Ressourcen- und Tool-Entdeckung aus API-Endpunkten, schreibgeschützten Zugriff auf GET-Endpunkte als MCP-Ressourcen und dynamische Schema-Generierung aus OpenAPI-Spezifikationen.
```
