---
title: OpenAI-kompatible REST API
source_sha: 2f1a9ff59c46e6f1dfc64698d009e2d11062dea567710a39312b110e505de83a
---

# OpenAI-kompatible REST API

## Konzept und Zweck

Die OpenAI-kompatible REST API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI
API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen
auf die Swiss AI-Hub Plattform zu migrieren, ohne den Anwendungscode zu ändern – lediglich die API-Endpunkt-URL und der
Authentifizierungs-Token müssen angepasst werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshürden und dem Schutz
bestehender Technologieinvestitionen. Organisationen können die Swiss AI-Hub Infrastruktur aus Gründen der Datenhoheit,
Kostenkontrolle oder Compliance übernehmen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes
Anwendungsökosystem beibehalten.

## Kernprinzipien des Designs

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen
Funktionen, einschließlich Konversations-KI (Chat Completions), semantische Suche (Embeddings), Bildgenerierung und
Audioverarbeitung (Sprache-zu-Text und Text-zu-Sprache). Anwendungen, die mit den Python- oder JavaScript-SDKs von
OpenAI entwickelt wurden, funktionieren ohne Änderungen, was eine schnelle Plattformadoption ermöglicht und das
Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich sowohl auf Anfrage- und Antwortformate, Streaming-Verhalten als auch auf
Fehlerbehebungsmuster. Organisationen können die Plattform mit bestehenden Testsuiten und Migrationsskripten validieren,
wodurch Evaluierungs- und Bereitstellungszeiten beschleunigt werden.

### Anbieterneutraler Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, darunter Azure OpenAI,
selbst gehostete Modelle und andere OpenAI-kompatible Dienste. Diese Anbieterneutralität bietet mehrere
Geschäftsvorteile: Organisationen können transparent und ohne Anwendungsänderungen zwischen Modellprovidern wechseln,
Kostenoptimierungsstrategien implementieren, indem sie Anfragen basierend auf Workload-Eigenschaften an verschiedene
Anbieter weiterleiten, Datenhoheit durch selbst gehostete Modelloptionen aufrechterhalten und hybride
Bereitstellungsmodelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Die Modellauswahl und -weiterleitung erfolgen transparent auf Plattformebene, was eine zentralisierte Governance und
Optimierung ermöglicht, ohne eine Koordination zwischen den Anwendungsteams zu erfordern.

### Erweitertes Modellkonzept: AI-Hub Assistenten

Über Standard-Sprachmodelle hinaus erweitert der Swiss AI-Hub das OpenAI-Modellkonzept um plattform-native
KI-Assistenten (Agenten). Diese Assistenten erscheinen als spezialisierte Modelle neben traditionellen LLMs und
ermöglichen es Anwendungen, mit komplexen, zustandsbehafteten Agenten-Workflows über dieselbe vertraute
Chat-Schnittstelle zu interagieren.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die sich von einfachen LLM-Interaktionen zu
orchestrierten Agenten-Workflows entwickeln möchten. Anwendungen können zunächst grundlegende Sprachmodelle aufrufen und
schrittweise anspruchsvollere Agenten übernehmen, ohne architektonische Änderungen vornehmen zu müssen – dieselbe
API-Schnittstelle dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet eine vollständige Palette an KI-Funktionalität, die mit modernen LLM-Anwendungen kompatibel ist:

**Konversations-KI**: Vollständige Unterstützung für Chat Completions mit synchronen und Streaming-Antwortmodi, die
interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Konversationen,
Funktionsaufrufe und multimodale Eingaben (Text und Bilder) für visuell-fähige Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektorrepräsentationen für semantische Suche,
Ähnlichkeitsabgleich und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt Batch-Verarbeitung und
mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bildgenerierung aus Text-Prompts und Audioverarbeitungsfunktionen, einschließlich
Sprache-zu-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-zu-Sprache-Synthese mit
konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modell-Erkennung**: Die dynamische Modellauflistung ermöglicht Anwendungen, verfügbare LLM-Modelle und AI-Hub
Assistenten zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentralisierte Modellverwaltung unterstützt.

## Geschäftswert

### Reduziertes Migrationsrisiko und -kosten

Organisationen können die Swiss AI-Hub Plattform übernehmen, ohne Anwendungen neu schreiben zu müssen, wodurch
Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams nutzen weiterhin
vertraute OpenAI SDKs und Muster, wodurch Umschulungsaufwand vermieden wird. Diese Kompatibilität sichert Investitionen
in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen zentralen Kontrollpunkt für den Modellzugriff innerhalb der Organisation.
Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne
Änderungen an einzelnen Anwendungen zu erfordern. Der Wechsel des Modellproviders erfolgt transparent, was
Kostenoptimierung ermöglicht und die Anbieterbindung (Vendor Lock-in) vermeidet.

### Pfad zur progressiven Verbesserung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und hochentwickelten KI-Assistenten ermöglicht es
Organisationen, ihre KI-Fähigkeiten schrittweise weiterzuentwickeln. Anwendungen, die für den einfachen Modellzugriff
entwickelt wurden, können mit zunehmender organisatorischer Reife schrittweise fortschrittlichere agentenbasierte
Workflows übernehmen, ohne ein architektonisches Redesign zu erfordern.

## Implementierungsansatz

Die auf FastAPI basierende API ist als Teil des Hauptplattformdienstes implementiert und verfügt über eine zustandslose
Anfrageverarbeitung, die eine horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit
den Identitätsprovidern der Organisation, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und
KI-Assistenten. Die Anfrage-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während
Assistenten-Interaktionen in Plattformereignisse zur Agentenverarbeitung umgewandelt werden, wodurch eine klare Trennung
zwischen externem Modellzugriff und interner Agenten-Orchestrierung aufrechterhalten wird.
