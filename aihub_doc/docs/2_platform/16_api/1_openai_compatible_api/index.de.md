---
title: OpenAI-kompatible REST API
index: 1
source_sha: "e9a7c928feeac89973b4f7863b3f3e3404f15d5c61c1187ed540cc45b4aa9ca6"
---

# OpenAI-kompatible REST API

## Konzept und Zweck

Die OpenAI-kompatible REST API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen auf die Swiss AI-Hub Plattform zu migrieren, ohne den Anwendungscode ändern zu müssen – lediglich die API-Endpunkt-URL und der Authentifizierungs-Token müssen angepasst werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshürden und dem Schutz bestehender Technologieinvestitionen. Organisationen können die Swiss AI-Hub Infrastruktur aus Gründen der Datensouveränität, Kostenkontrolle oder Compliance übernehmen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes Anwendungsökosystem beibehalten.

## Kern-Designprinzipien

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen Funktionen, einschließlich Konversations-KI (Chat Completions), semantischer Suche (Embeddings), Bildgenerierung und Audioverarbeitung (Speech-to-Text und Text-to-Speech). Anwendungen, die mithilfe der Python- oder JavaScript-SDKs von OpenAI entwickelt wurden, funktionieren ohne Modifikation, was eine schnelle Plattformadoption ermöglicht und das Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich sowohl auf Anfrage- und Antwortformate als auch auf Streaming-Verhalten und Fehlerbehandlungsmuster. Organisationen können die Plattform mithilfe bestehender Testsuiten und Migrationsskripte validieren, wodurch Bewertungs- und Bereitstellungszeiten beschleunigt werden.

### Anbieterneutraler Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, darunter Azure OpenAI, selbstgehostete Modelle und andere OpenAI-kompatible Dienste. Diese Anbieterneutralität bietet mehrere geschäftliche Vorteile: Organisationen können transparent zwischen Modellprovidern wechseln, ohne Anwendungsänderungen vornehmen zu müssen; sie können Kostenoptimierungsstrategien implementieren, indem sie Anfragen basierend auf Workload-Eigenschaften an verschiedene Anbieter weiterleiten; sie können Datensouveränität durch selbstgehostete Modelloptionen aufrechterhalten und hybride Bereitstellungsmodelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Die Modellauswahl und das Routing erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und Optimierung ermöglicht, ohne dass eine Koordination zwischen den Anwendungsteams erforderlich ist.

### Erweitertes Modellkonzept: AI-Hub Assistants

Über standardmäßige Sprachmodelle hinaus erweitert der Swiss AI-Hub das OpenAI-Modellkonzept um plattform-eigene KI-Assistenten (Agents). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen es Anwendungen, mit komplexen, zustandsbehafteten Agenten-Workflows über dieselbe vertraute Chat-Oberfläche zu interagieren.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die von einfachen LLM-Interaktionen zu orchestrierten Agenten-Workflows übergehen möchten. Anwendungen können mit dem Aufruf einfacher Sprachmodelle beginnen und schrittweise anspruchsvollere Agents übernehmen, ohne architektonische Änderungen vornehmen zu müssen – dieselbe API-Schnittstelle dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet ein vollständiges Spektrum an KI-Funktionen, das mit modernen LLM-Anwendungen kompatibel ist:

**Konversations-KI**: Vollständige Unterstützung für Chat Completions mit synchronen und Streaming-Antwortmodi, die interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Konversationen, Function Calling und multimodale Eingaben (Text und Bilder) für bildverarbeitungsfähige Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektorrepräsentationen für semantische Suche, Ähnlichkeitsabgleich und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt die Stapelverarbeitung und mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bildgenerierung aus Text-Prompts und Audioverarbeitungsfunktionen, einschließlich Speech-to-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-to-Speech-Synthese mit konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modellentdeckung**: Die dynamische Modellauflistung ermöglicht es Anwendungen, verfügbare LLM-Modelle und AI-Hub Assistants zur Laufzeit zu entdecken, wodurch adaptive Schnittstellen und eine zentralisierte Modell-Governance unterstützt werden.

## Geschäftswert

### Reduziertes Migrationsrisiko und Kosten

Organisationen können die Swiss AI-Hub Plattform übernehmen, ohne Anwendungen neu schreiben zu müssen, wodurch Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams verwenden weiterhin vertraute OpenAI SDKs und Muster, wodurch Umschulungsaufwand vermieden wird. Diese Kompatibilität schützt Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen einzigen Kontrollpunkt für den Modellzugriff innerhalb der Organisation. Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne Änderungen an einzelnen Anwendungen vornehmen zu müssen. Der Wechsel des Modellproviders erfolgt transparent, was Kostenoptimierung ermöglicht und Vendor Lock-in vermeidet.

### Pfad zur schrittweisen Erweiterung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es Organisationen, ihre KI-Fähigkeiten schrittweise weiterzuentwickeln. Anwendungen, die für den einfachen Modellzugriff entwickelt wurden, können mit zunehmender organisatorischer Reife schrittweise fortschrittlichere agentenbasierte Workflows übernehmen, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Basierend auf FastAPI fungiert die API als Teil des Hauptplattformdienstes mit zustandsloser Anfragenbehandlung, die eine horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich mit organisatorischen Identitätsprovidern über OAuth2, und hierarchische Berechtigungen steuern den Zugriff auf sowohl LLM-Modelle als auch AI-Assistenten. Die Anfragen-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während Assistenten-Interaktionen in Plattformereignisse für die Agentenverarbeitung umgewandelt werden, wodurch eine klare Trennung zwischen externem Modellzugriff und interner Agenten-Orchestrierung aufrechterhalten wird.
