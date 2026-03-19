---
title: OpenAI-kompatible REST API
source_sha: 3c669efc69e6adb8850aba1a1c511eec4e316c709760742d54ac6130d8cfa3d5
---

# OpenAI-kompatible REST API

## Konzept und Zweck

Die OpenAI-kompatible REST API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI
API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen
auf die Swiss AI Hub-Plattform zu migrieren, ohne den Anwendungscode ändern zu müssen – lediglich die API-Endpunkt-URL
und der Authentifizierungs-Token müssen angepasst werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshemmnissen und dem Schutz
bestehender Technologieinvestitionen. Organisationen können die Swiss AI Hub-Infrastruktur aus Gründen der Datenhoheit,
Kostenkontrolle oder Compliance einführen und gleichzeitig ihr auf OpenAI SDKs und Bibliotheken aufgebautes
Anwendungs-Ökosystem bewahren.

## Kern-Designprinzipien

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen
Funktionen, einschliesslich konversationeller KI (Chat Completions), semantischer Suche (Embeddings), Bildgenerierung
und Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache). Anwendungen, die mit den Python- oder JavaScript-SDKs von
OpenAI entwickelt wurden, funktionieren ohne Modifikation, was eine schnelle Plattformakzeptanz ermöglicht und das
Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Request- und Response-Formate, Streaming-Verhalten und Fehlerbehandlungsmuster.
Organisationen können die Plattform mit bestehenden Testsuiten und Migrationsskripten validieren, was die Evaluierungs-
und Deployment-Zeiten beschleunigt.

### Anbieterneutraler Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, einschliesslich Swiss LLM
Cloud, selbst gehostete vLLM-Modelle und andere OpenAI-kompatible Services. Diese Anbieterneutralität bietet mehrere
Geschäftsvorteile: Organisationen können transparent zwischen Modellprovidern wechseln, ohne Anwendungsänderungen
vornehmen zu müssen, Kostenoptimierungsstrategien implementieren, indem sie Anfragen basierend auf
Workload-Eigenschaften an verschiedene Anbieter weiterleiten, Datenhoheit durch selbst gehostete Modelloptionen
aufrechterhalten und hybride Deployment-Modelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Die Modellauswahl und das Routing erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und
Optimierung ermöglicht, ohne dass eine Koordination zwischen den Anwendungsteams erforderlich ist.

### Erweitertes Modellkonzept: Swiss AI Hub Assistants

Über Standard-Sprachmodelle hinaus erweitert der Swiss AI Hub das OpenAI-Modellkonzept um plattformeigene KI-Assistenten
(Agents). Diese Assistants erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen es
Anwendungen, mit komplexen, zustandsbehafteten Agent-Workflows über dieselbe vertraute Chat-Schnittstelle zu
interagieren.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die von einfachen LLM-Interaktionen zu orchestrierten
Agent-Workflows übergehen möchten. Anwendungen können damit beginnen, grundlegende Sprachmodelle aufzurufen und
schrittweise anspruchsvollere Agents ohne architektonische Änderungen zu übernehmen – dieselbe API-Schnittstelle bedient
beide Anwendungsfälle.

## Unterstützte Funktionen

Die API bietet eine umfassende KI-Funktionalität, die mit modernen LLM-Anwendungen kompatibel ist:

**Konversationelle KI**: Vollständige Unterstützung für Chat Completions mit synchronen und Streaming-Response-Modi, die
interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Konversationen,
Function Calling und multimodale Eingaben (Text und Bilder) für visuell-fähige Modelle.

**Semantische Suche**: Embedding-Generierung wandelt Text in Vektordarstellungen für semantische Suche,
Ähnlichkeitsabgleich und Retrieval-Augmented Generation-Workflows um. Diese Funktion unterstützt Batch-Verarbeitung und
mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bildgenerierung aus Text-Prompts und Audioverarbeitungsfunktionen, einschliesslich
Sprache-zu-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-zu-Sprache-Synthese mit
konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modellentdeckung**: Dynamische Modellauflistung ermöglicht es Anwendungen, verfügbare LLM-Modelle und Swiss AI Hub
Assistants zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modellgovernance unterstützt.

## Geschäftswert

### Reduziertes Migrationsrisiko und -kosten

Organisationen können die Swiss AI Hub-Plattform ohne Umschreiben von Anwendungen einführen, wodurch
Migrationsprojektkosten eliminiert und das Adoptionsrisiko reduziert werden. Bestehende Entwicklungsteams verwenden
weiterhin vertraute OpenAI SDKs und Muster, wodurch Schulungsaufwand vermieden wird. Diese Kompatibilität bewahrt
Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen einzigen Kontrollpunkt für den Modellzugriff innerhalb der gesamten
Organisation. Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien
implementieren, ohne Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt
transparent, was Kostenoptimierung ermöglicht und Vendor Lock-in vermeidet.

### Progressiver Entwicklungspfad

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es
Organisationen, ihre KI-Fähigkeiten inkrementell zu entwickeln. Anwendungen, die für den einfachen Modellzugriff
entwickelt wurden, können schrittweise fortschrittlichere Agent-basierte Workflows übernehmen, wenn die organisatorische
Reife zunimmt, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Auf FastAPI basierend, agiert die API als Teil des Hauptplattform-Services mit zustandsloser Request-Verarbeitung, die
horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich mit organisatorischen Identitätsprovidern via
OAuth2, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und KI-Assistenten. Die
Request-Routing-Logik leitet Modell-Requests transparent an die LLM-Proxy-Schicht weiter, während
Assistant-Interaktionen in Plattformereignisse für die Agent-Verarbeitung umgewandelt werden, wodurch eine klare
Trennung zwischen externem Modellzugriff und interner Agent-Orchestrierung aufrechterhalten wird.
