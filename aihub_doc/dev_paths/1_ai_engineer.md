# KI-Engineer

## Einleitung

Dieses Dokument beschreibt die einzelnen Stufen der Kompetenz KI-Engineering. Sie beschreibt nicht die Rolle KI-Engineer, denn diese besteht aus diversen Kompetenzen. Die Aufzählungen beschreiben kurz und prägnant, was eine Person auf der Stufe "X" beherrschen soll. Sie stellt keine Checkliste dar, sondern eine Hilfestellung für diejenigen, die in der Kompetenz KI-Engineering weiterkommen wollen. Es bestehen etliche Überschneidungen zu anderen Kompetenzen wie Software Engineering, Testing, Software Architektur, etc.

## Basic

Gut ausgebildet. Eine solide Grundlage. Die Routine fehlt.

### Methodik
- **KI-Agenten-Workflows**: Versteht und implementiert vorgegebene Agenten-Workflows. Kann die Konzepte von Event-basierten Agentensystemen nachvollziehen und anwenden.
- **Event-Driven Development**: Erkennt und handhabt verschiedene Event-Typen (Control Events, Semantic Events) und versteht deren Rolle im KI-System.
- **Testing**: Entwickelt Unit-Tests für KI-Komponenten. Kann einfache Testszenarien für Agenten implementieren.
- **Debugging**: Fehlersuche in eigenem Code und einfachen Agentenprozessen. Kann Logs und Traces nachvollziehen.
- **Pair Programming**: Arbeitet effektiv in Pair-Programming-Sessions, besonders für KI-spezifische Aufgaben.
- **Review**: Bereitet eigenen Code für Reviews vor und setzt Feedback um.

### Technologie
- **Entwicklungssprachen**: Gute Python-Kenntnisse für Backend und Agenten-Entwicklung. Grundkenntnisse in JavaScript/TypeScript für Frontend-Interaktionen.
- **LLM-Grundlagen**: Versteht grundlegende Konzepte von Large Language Models und deren Anwendungsmöglichkeiten. Kennt die Unterschiede zwischen gängigen Modellen (OpenAI, Anthropic, OSS-Modelle).
- **AI-Hub Stack**: Kennt die Grundkomponenten des AI-Hubs (NATS, FastAPI, Agenten-Framework) und kann damit arbeiten.
- **KI-Pipelines**: Versteht grundlegende Datenpipelines für KI-Anwendungen. Kann existierende Dagster-Pipelines bedienen und einfache Änderungen vornehmen.
- **Retrieval-Augmented Generation**: Grundlegendes Verständnis von RAG, kann vorgegebene RAG-Pipelines implementieren und einfache Anpassungen vornehmen.
- **Vector Embeddings**: Kennt das Konzept von Embeddings und deren Anwendung für semantische Suche und RAG.

### Tools
- **Entwicklungsumgebung**: Beherrscht die vollständige Setup-Prozedur (Docker, Poetry, PNPM) für KI-Entwicklung.
- **Versionsverwaltung**: Verwendet Git effektiv in KI-Projekten. Versteht Branching-Strategien im Kontext agiler KI-Entwicklung.
- **CI/CD**: Versteht GitHub Actions und deren Anwendung in KI-Projekten.
- **Prompt Engineering**: Kann einfache Prompts für LLMs entwickeln und iterativ verbessern.
- **Azure**: Kann mit Azure Cognitive Services und anderen KI-relevanten Azure-Diensten umgehen.

## Proficient

Bewandt und erfahren. Ein Performer.

### Methodik
- **Agenten-Design**: Entwickelt eigenständig Agenten mit komplexen Step-Flows und Events. Kann intelligente Entscheidungswege in Workflows abbilden.
- **Multi-Agent-Interaktion**: Implementiert Kommunikation zwischen mehreren Agenten. Gestaltet koordinierte Agentengruppen für komplexe Aufgaben.
- **Context-Handling**: Nutzt ThreadContext und RunContext effektiv für zustandsbehaftete Szenarien. Implementiert persistentes Wissen zwischen Sessions.
- **Testing-Strategien**: Entwickelt umfassende Test-Strategien für KI-Systeme, einschließlich Mocking von LLM-Antworten und Simulation von Nutzerinteraktionen.
- **Debugging**: Führt Verhaltensanalysen in komplexen Agentenabläufen durch. Kann Probleme in verteilten KI-Systemen identifizieren und beheben.
- **Refactoring**: Erkennt Verbesserungspotenziale in KI-Workflows und implementiert Optimierungen.
- **Pair Programming**: Bietet aktive Unterstützung in Pair-Programming-Sessions und kann bei KI-spezifischen Herausforderungen anleiten.
- **Review**: Führt effektive Code-Reviews für KI-Komponenten durch, mit Fokus auf Robustheit, Sicherheit und Wartbarkeit.

### Technologie
- **LLM-Integration**: Implementiert und optimiert Anbindungen an verschiedene LLM-Provider und -Modelle. Wählt geeignete Modelle basierend auf Anforderungen aus.
- **Retrieval-Augmented Generation**: Entwickelt fortgeschrittene RAG-Lösungen mit optimierten Chunking-Strategien, Reranking und Metadaten-Nutzung.
- **Embeddings**: Versteht verschiedene Embedding-Modelle und deren Anwendungsszenarien. Implementiert domänenspezifische Embedding-Strategien.
- **Event-Driven Architecture**: Tiefes Verständnis der Event-basierten Kommunikation in KI-Systemen. Gestaltet robuste Event-Flows für komplexe Use Cases.
- **Python-Ecosystem für KI**: Fortgeschrittene Kenntnisse relevanter Python-Frameworks (LangChain, OpenTelemetry, FastAPI, Pydantic, AsyncIO).
- **KI-Sicherheit**: Implementiert robuste Sicherheitskonzepte gegen Prompt-Injection, Halluzinationen und andere KI-spezifische Risiken.
- **Frontend für KI-Anwendungen**: Erstellt intuitive UIs für KI-Anwendungen mit Nuxt 3, Vue.js und TailwindCSS. Implementiert Echtzeit-Feedback für Agenten-Interaktionen.

### Tools
- **Infrastruktur als Code**: Setzt Pulumi für KI-spezifische Infrastruktur ein. Automatisiert Cloud-Ressourcen für KI-Workloads.
- **Observability**: Implementiert umfassende Tracing- und Logging-Lösungen für KI-Systeme. Nutzt OpenTelemetry für Transparenz bei KI-Entscheidungen.
- **Performance-Tuning**: Optimiert Agenten und Pipelines für niedrige Latenz und hohen Durchsatz. Verbessert Antwortzeiten von KI-Systemen.
- **DevOps für KI**: Erstellt und pflegt CI/CD-Pipelines für KI-Anwendungen. Integriert Tests und Deployment für kontinuierliche Verbesserung.
- **Vector-Datenbanken**: Konfiguriert und optimiert verschiedene Vector-Datenbanken für unterschiedliche Anwendungsfälle.

## Advanced

Lead und bildet aus. Ein Meister.

### Methodik
- **KI-System-Design**: Entwirft komplexe KI-Systeme mit multiplen, spezialisierten Agenten. Gestaltet Systeme, die über den aktuellen AI-Hub-Standard hinausgehen.
- **Workflow-Innovation**: Entwickelt neue Konzepte für Agenten-Workflows, die erweiterte Autonomie und Adaptivität bieten. Führt neue Workflow-Patterns ein.
- **Human-in-the-Loop**: Entwirft fortschrittliche HITL-Patterns, die die Zusammenarbeit von Menschen und KI optimieren und Vertrauen fördern.
- **Test-Driven KI-Entwicklung**: Leitet Test-Strategien, die KI-spezifische Herausforderungen addressieren. Definiert Qualitätsstandards für KI-Systeme.
- **Team-Leadership**: Leitet technische Teams, führt Code-Reviews durch, implementiert technische Standards für KI-Entwicklung.
- **Problem-Lösung**: Analysiert komplexe KI-Anforderungen und entwickelt neuartige Lösungsansätze. Überwindet Einschränkungen aktueller KI-Technologien.

### Technologie
- **LLM-Optimierung**: Führt fortgeschrittenes Fine-Tuning von LLMs durch. Entwickelt Domain-Adaptations und optimiert KI-Modelle für spezifische Anwendungen.
- **Multi-Modal KI**: Integriert Bild-, Audio- und andere Modalitäten in KI-Agenten. Entwickelt multimodale Workflows für komplexe Informationsverarbeitung.
- **Advanced Retrieval-Systeme**: Implementiert Cutting-Edge Retrieval-Techniken wie hierarchische RAG, rekursive Verfeinerung, hypothetische Dokumentengenerierung.
- **Kognitive Architekturen**: Entwickelt KI-Systeme mit fortschrittlichen kognitiven Fähigkeiten wie Planen, Gedächtnis und Selbstreflexion.
- **Custom Models**: Integriert und passt spezialisierte ML-Modelle (nicht nur LLMs) für domänenspezifische Anforderungen an.
- **Framework-Erweiterung**: Erweitert den AI-Hub um neue Funktionalitäten oder optimiert bestehende Komponenten für bessere Performance oder neue Anwendungsfälle.
- **Verteilte KI-Systeme**: Entwirft und implementiert KI-Systeme, die über mehrere Dienste und Geräte verteilt arbeiten können.

### Tools
- **Kostenoptimierung**: Entwickelt Strategien zur Optimierung von Betriebskosten für KI-Systeme ohne Kompromisse bei der Qualität.
- **Edge-Deployment**: Implementiert KI-Lösungen für Edge- und Hybrid-Cloud-Szenarien mit eingeschränkten Ressourcen.
- **KI-spezifische DevSecOps**: Entwickelt Sicherheits- und Compliance-Pipelines für KI-Anwendungen unter Berücksichtigung spezieller Anforderungen.
- **Forschungs-Integration**: Evaluiert und integriert neue Techniken aus der KI-Forschung in praktische Anwendungen.

## Expert

Kaum einer kann das Wasser reichen. Ein Guru.

### Methodik
- **Architektur-Innovation**: Konzipiert bahnbrechende Agentenarchitekturen jenseits aktueller Paradigmen. Entwickelt neue KI-Interaktionsmuster.
- **Schulung und Mentoring**: Bildet Teams in fortgeschrittenen KI-Engineering-Praktiken aus. Entwickelt Curricula und Best Practices.
- **Publikationen**: Verfasst technische Publikationen zu KI-Engineering-Themen. Präsentiert Innovationen auf Konferenzen.
- **Open-Source-Beiträge**: Trägt substantiell zu relevanten Open-Source-Projekten im KI-Bereich bei. Leitet Community-Entwicklungen.
- **KI-Entwicklungsmethodik**: Entwickelt und verfeinert Methodiken für KI-Engineering, die Robustheit, Erklärbarkeit und ethische Aspekte berücksichtigen.

### Technologie
- **Modell-Engineering**: Passt Modellarchitekturen für spezifische Anwendungsfälle an oder trainiert eigene Modelle von Grund auf.
- **Zukunftstechnologien**: Integriert aufkommende KI-Technologien wie Tool-Learning, Multi-Agent-Kooperation oder kognitive Architekturen in praktische Anwendungen.
- **Cross-Modal Intelligence**: Entwickelt komplexe multimodale Systeme mit hoher Fähigkeit zur Wissensintegration über verschiedene Datentypen hinweg.
- **Advanced Embedding und Retrieval**: Implementiert domänenspezifische Embedding- und Retrieval-Strategien jenseits von Standardmodellen, für maximale Präzision und Relevanz.
- **Autonome KI-Systeme**: Entwickelt selbstverbessernde KI-Systeme, die aus Interaktionen lernen und ihre eigenen Fähigkeiten erweitern.

### Tools
- **KI-Infrastruktur-Innovation**: Entwickelt innovative Ansätze für KI-Infrastrukturen, die neue Hardwaregenerationen oder verteilte Architekturen nutzen.
- **Hardwareoptimierung**: Nutzt spezielle Hardware (GPUs, TPUs, etc.) optimal für KI-Workloads. Implementiert hardwarespezifische Optimierungen.
- **Verteilte und Föderierte KI**: Konzipiert föderierte oder Edge-basierte verteilte KI-Architekturen für datenschutzsensitive oder bandbreiteneffiziente Anwendungen.
- **Self-Healing KI-Systeme**: Entwickelt selbstoptimierende und selbstreparierende KI-Infrastrukturen für maximale Verfügbarkeit und Adaptivität.
- **Experimentelle Toolchains**: Erprobt und integriert experimentelle KI-Tools und -Frameworks weit vor deren Mainstream-Adoption.

------ Gehalt ------

Prompt: Gegeben ist das Anforderungsprofil für einen KI-Entwickler. Schlage mir realistische Lohnbänder (min, median, max) für dieses Anforderungsprofil auf den gegebenen Stufen vor für den Jobmarkt in Zürich, Schweiz.

# AI Developer Salary Comparison (CHF per year)

| Level | Model | Minimum | Median | Maximum |
|-------|-------|---------|--------|---------|
| **Basic** | Claude Sonnet 3.7 | 90,000 | 110,000 | 130,000 |
| | o3-mini | 90,000 | 110,000 | 130,000 |
| | Gemini 2.5 Pro | 90,000 | 105,000 | 120,000 |
| **Proficient** | Claude Sonnet 3.7 | 120,000 | 150,000 | 180,000 |
| | o3-mini | 120,000 | 150,000 | 180,000 |
| | Gemini 2.5 Pro | 120,000 | 140,000 | 160,000 |
| **Advanced** | Claude Sonnet 3.7 | 160,000 | 190,000 | 230,000 |
| | o3-mini | 150,000 | 190,000 | 230,000 |
| | Gemini 2.5 Pro | 155,000 | 175,000 | 200,000+ |
| **Expert** | Claude Sonnet 3.7 | 200,000 | 250,000 | 350,000+ |
| | o3-mini | 200,000 | 240,000 | 300,000+ |
| | Gemini 2.5 Pro | 190,000 | 220,000 | 250,000++ |