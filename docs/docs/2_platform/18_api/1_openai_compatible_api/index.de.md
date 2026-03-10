---
title: OpenAI-kompatible REST API
source_sha: b690801a80c10550fd115cb9afd29d92093f8e869b436e810def4d032a8d36d9
---

# OpenAI-kompatible REST API

## Konzept und Zweck

Die OpenAI-kompatible REST API bietet eine standardbasierte HTTP-Schnittstelle, die auf FastAPI basiert und die OpenAI
API-Spezifikation exakt widerspiegelt. Dieses Design ermöglicht es Organisationen, bestehende KI-gestützte Anwendungen
auf die Swiss AI Hub-Plattform zu migrieren, ohne den Anwendungscode ändern zu müssen – lediglich die API-Endpunkt-URL
und der Authentifizierungstoken müssen angepasst werden.

Der strategische Wert dieser Kompatibilitätsschicht liegt in der Reduzierung von Migrationshürden und dem Schutz
bestehender Technologieinvestitionen. Organisationen können die Swiss AI Hub-Infrastruktur aus Gründen der Datenhoheit,
Kostenkontrolle oder Compliance übernehmen, während sie ihr auf OpenAI SDKs und Bibliotheken aufgebautes
Anwendungsökosystem beibehalten.

## Wesentliche Designprinzipien

### Nahtlose Migration und Integration

Die API implementiert vollständige Kompatibilität mit der OpenAI-Schnittstelle und unterstützt alle wichtigen
Funktionen, einschließlich Konversations-KI (Chat Completions), semantischer Suche (Embeddings), Bildgenerierung und
Audioverarbeitung (Speech-to-Text und Text-to-Speech). Anwendungen, die mit den Python- oder JavaScript-SDKs von OpenAI
entwickelt wurden, funktionieren ohne Änderungen, was eine schnelle Plattformadoption ermöglicht und das
Implementierungsrisiko reduziert.

Diese Kompatibilität erstreckt sich auf Anfrage- und Antwortformate, Streaming-Verhalten und Fehlerbehandlungsmuster.
Organisationen können die Plattform mit bestehenden Testsuiten und Migrationsskripten validieren, was die Evaluierungs-
und Deployment-Zeitpläne beschleunigt.

### Anbieterunabhängiger Modellzugriff

Die API abstrahiert die zugrunde liegenden Modellprovider und unterstützt mehrere LLM-Quellen, darunter die Swiss LLM
Cloud, selbstgehostete vLLM-Modelle und andere OpenAI-kompatible Services. Diese Anbieterneutralität bietet mehrere
Geschäftsvorteile: Organisationen können transparent zwischen Modellprovidern wechseln, ohne Anwendungsänderungen
vornehmen zu müssen, Kostenoptimierungsstrategien implementieren, indem Anfragen basierend auf Workload-Eigenschaften an
verschiedene Anbieter geleitet werden, Datenhoheit durch selbstgehostete Modelloptionen aufrechterhalten und hybride
Deployment-Modelle nutzen, die Cloud- und On-Premise-Ressourcen kombinieren.

Modellauswahl und Routing erfolgen transparent auf Plattformebene, was eine zentrale Governance und Optimierung
ermöglicht, ohne Koordination zwischen den Anwendungsteams zu erfordern.

### Erweitertes Modellkonzept: Swiss AI Hub Agents

Über Standard-Sprachmodelle hinaus erweitert der Swiss AI Hub das OpenAI-Modellkonzept um plattformeigene KI-Agents.
Diese Agents erscheinen als spezialisierte Modelle neben traditionellen LLMs und ermöglichen Anwendungen die Interaktion
mit komplexen, zustandsbehafteten Agent-Workflows über dieselbe vertraute Chat-Schnittstelle.

Diese Erweiterung bietet einen Migrationspfad für Organisationen, die von einfachen LLM-Interaktionen zu orchestrierten
Agent-Workflows übergehen möchten. Anwendungen können zunächst grundlegende Sprachmodelle aufrufen und schrittweise
anspruchsvollere Agents übernehmen, ohne architektonische Änderungen vornehmen zu müssen – dieselbe API-Schnittstelle
dient beiden Anwendungsfällen.

## Unterstützte Funktionen

Die API bietet eine Vollspektrum-KI-Funktionalität, die mit modernen LLM-Anwendungen kompatibel ist:

**Konversations-KI**: Vollständige Unterstützung für Chat Completions mit synchronen und Streaming-Antwortmodi, die
interaktive Anwendungen und progressive UI-Updates ermöglichen. Die Schnittstelle unterstützt Multi-Turn-Konversationen,
Funktionsaufrufe und multimodale Eingaben (Text und Bilder) für visuelle Modelle.

**Semantische Suche**: Die Embedding-Generierung wandelt Text in Vektorrepräsentationen für die semantische Suche,
Ähnlichkeitsabgleiche und Retrieval-Augmented Generation Workflows um. Diese Funktion unterstützt Batch-Verarbeitung und
mehrere Embedding-Modellkonfigurationen.

**Multimodale Generierung**: Bildgenerierung aus Text-Prompts und Audioverarbeitungsfunktionen, einschließlich
Speech-to-Text-Transkription (unterstützt mehrere Audioformate und Sprachen) und Text-to-Speech-Synthese mit
konfigurierbaren Stimmen und Streaming-Ausgabe.

**Modellentdeckung**: Die dynamische Modellauflistung ermöglicht Anwendungen, verfügbare LLM-Modelle und Swiss AI
Hub-Agents zur Laufzeit zu entdecken, was adaptive Schnittstellen und eine zentrale Modell-Governance unterstützt.

## Geschäftswert

### Reduziertes Migrationsrisiko und geringere Kosten

Organisationen können die Swiss AI Hub-Plattform übernehmen, ohne Anwendungen neu schreiben zu müssen, wodurch
Migrationsprojektkosten entfallen und das Adoptionsrisiko reduziert wird. Bestehende Entwicklungsteams verwenden
weiterhin vertraute OpenAI SDKs und Muster, wodurch Umschulungsaufwand vermieden wird. Diese Kompatibilität bewahrt
Investitionen in Anwendungscode, Testinfrastruktur und operative Runbooks.

### Zentralisierte Governance und Kostenkontrolle

Die Kompatibilitätsschicht bietet einen zentralen Kontrollpunkt für den Modellzugriff innerhalb der Organisation.
Plattformadministratoren können Kostenkontrollen, Nutzungskontingente und Routing-Richtlinien implementieren, ohne
Änderungen an einzelnen Anwendungen zu erfordern. Der Wechsel des Modellproviders erfolgt transparent, was
Kostenoptimierung ermöglicht und Anbieterbindung (Vendor Lock-in) vermeidet.

### Pfad der progressiven Weiterentwicklung

Die vereinheitlichte Schnittstelle zwischen grundlegenden LLM-Modellen und anspruchsvollen KI-Agents ermöglicht es
Organisationen, ihre KI-Fähigkeiten schrittweise weiterzuentwickeln. Anwendungen, die für den einfachen Modellzugriff
entwickelt wurden, können mit zunehmender organisatorischer Reife schrittweise fortschrittlichere agentenbasierte
Workflows übernehmen, ohne eine architektonische Neugestaltung zu erfordern.

## Implementierungsansatz

Auf FastAPI basierend, operiert die API als Teil des Hauptplattform-Services mit zustandsloser Anfragebearbeitung, die
horizontale Skalierung ermöglicht. Die Authentifizierung integriert sich über OAuth2 mit organisationsinternen
Identitätsprovidern, und hierarchische Berechtigungen steuern den Zugriff auf LLM-Modelle und KI-Agents. Die
Anfragen-Routing-Logik leitet Modell-Anfragen transparent an die LLM-Proxy-Schicht weiter, während Agent-Interaktionen
in Plattformereignisse zur Agent-Verarbeitung umgewandelt werden, wodurch eine klare Trennung zwischen externem
Modellzugriff und interner Agent-Orchestrierung aufrechterhalten wird.
