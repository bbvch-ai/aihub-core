# Terminologie-Glossar für Swiss AI Hub Whitepaper

Dieses Glossar definiert die konsistente Verwendung von Fachbegriffen im Whitepaper. Verwenden Sie diese Begriffe
konsequent, um eine einheitliche Terminologie sicherzustellen.

## Agenten-Architektur

### Agenten-Bauplan

**Verwendung:** Agenten-Bauplan **Definition:** Der Code, der den Agenten-Workflow beschreibt. Ein Agenten-Bauplan
besitzt inhärent noch nicht eine komplette Fähigkeit, da diese erst über die Konfiguration gegeben wird – unter anderem
durch die Definition der Daten, welche vom Agenten verarbeitet werden. **Kontext:** Ein Agenten-Bauplan ist eine
technische Vorlage oder ein Template, das die grundlegende Struktur und Logik eines Agenten definiert.

### Agenten-Profil

**Verwendung:** Agenten-Profil **Definition:** Die Konfiguration eines Agenten, die schlussendlich einen individuellen
Agenten mit seinen individuellen Fähigkeiten darstellt. Ein Agenten-Profil basiert auf einem Agenten-Bauplan und wird
durch spezifische Konfigurationen erweitert (z.B. Zugriff auf bestimmte Datenquellen, spezifische Prompts,
Modellauswahl). **Kontext:** Mehrere Agenten-Profile können auf dem gleichen Agenten-Bauplan basieren, haben aber
unterschiedliche Konfigurationen und damit unterschiedliche Fähigkeiten.

## Daten und Wissen

### Unternehmensdaten

**Verwendung:** Unternehmensdaten **Definition:** Strukturierte und unstrukturierte Daten aus Unternehmenssystemen wie
SharePoint, OneDrive, Datenbanken, CRM-Systemen, etc. **Beispiele:** Dokumente, E-Mails, Kundenakten, Projektunterlagen,
interne Wikis

### Daten-zu-Wissen-Pipeline

**Verwendung:** Daten-zu-Wissen-Pipeline **Definition:** Automatisierte Prozesse, die Unternehmensdaten aufbereiten,
transformieren und in eine für KI-Agenten nutzbare Form (Vektorembeddings) überführen. **Technische Komponenten:**
Document Parsing (Docling), Chunking, Embedding-Generierung, Vektorspeicherung (Milvus)

### Wissensdatenbank

**Verwendung:** Wissensdatenbank **Definition:** Zentrale Speicherstruktur für aufbereitete Unternehmensdaten in
vektorisierter Form. Ermöglicht semantische Suche und Retrieval-Augmented Generation (RAG). **Kontext:** Eine
Wissensdatenbank kann mehrere Sammlungen enthalten.

### Sammlung

**Verwendung:** Sammlung **Definition:** Ein logisch abgegrenzter Teil einer Wissensdatenbank. Sammlungen gruppieren
thematisch oder organisatorisch zusammenhängende Dokumente. **Beispiel:** Eine Sammlung für HR-Dokumente, eine für
technische Spezifikationen, eine für Kundenverträge.

## Sicherheit und Zugriffskontrolle

### Rolle

**Verwendung:** Rolle **Definition:** Eine definierte Menge von Berechtigungen, die Benutzern zugewiesen werden können.
**Kontext:** Rollen definieren, welche Aktionen ein Benutzer durchführen und auf welche Ressourcen er zugreifen darf.

### RollenManager-Rolle

**Verwendung:** RollenManager-Rolle **Definition:** Eine privilegierte Rolle, die Berechtigungen zur Verwaltung von
Benutzerrollen und Zugriffsrechten besitzt.

### WissensVerwalter-Rolle

**Verwendung:** WissensVerwalter-Rolle **Definition:** Eine Rolle mit Berechtigungen zur Verwaltung von
Wissensdatenbanken, Sammlungen und Daten-zu-Wissen-Pipelines.

### AgentVerwender-Rolle

**Verwendung:** AgentVerwender-Rolle **Definition:** Eine Standard-Benutzerrolle, die die Verwendung von konfigurierten
Agenten-Profilen erlaubt, aber keine administrativen Berechtigungen besitzt.

### Zugriffsrechte

**Verwendung:** Zugriffsrechte **Definition:** Granulare Berechtigungen, die definieren, welche Benutzer oder Rollen auf
welche Ressourcen (Agenten-Profile, Wissensdatenbanken, Sammlungen) zugreifen dürfen.

## Benutzer und Administration

### Superuser

**Verwendung:** Superuser (Plural: Superusers) **Definition:** Administratorrolle mit uneingeschränkten Systemrechten.
Wird typischerweise für die initiale Plattform-Einrichtung und Systemwartung verwendet. **Hinweis:** Im Whitepaper
konsistent als "Superuser" (nicht "Swiss AI Hub Superuser") bezeichnen.

### Administrator

**Verwendung:** Administrator (Plural: Administratoren) **English:** Administrator **Definition:** Benutzer mit
erweiterten Verwaltungsrechten innerhalb eines Mandanten oder der gesamten Plattform. **Hinweis:** Im Whitepaper
konsistent als "Administrator" (nicht "Swiss AI Hub Admin") bezeichnen.

### Mandant

**Verwendung:** Mandant (Plural: Mandanten) **English:** Tenant / Organization **Definition:** Eine logisch isolierte
Organisationseinheit innerhalb der Swiss AI Hub Plattform. Jeder Mandant besitzt eigene Benutzer, Wissensdatenbanken,
Agenten-Profile und Zugriffsrechte. **Kontext:** Multi-Tenancy ermöglicht die sichere Nutzung derselben
Plattform-Instanz durch mehrere unabhängige Organisationen.

### Benutzer

**Verwendung:** Benutzer (Plural: Benutzer) **English:** User **Definition:** Eine natürliche Person oder ein
technischer Account, der die Swiss AI Hub Plattform nutzt.

## Plattform-Komponenten

### Swiss AI Hub

**Verwendung:** Swiss AI Hub **English:** Swiss AI Hub **Definition:** Die vollständige Enterprise-KI-Plattform als
Gesamtsystem. **Hinweis:** Immer mit "Swiss" als Präfix verwenden (nicht nur "AI Hub").

### LLM-Gateway

**Verwendung:** LLM-Gateway **English:** LLM Gateway **Definition:** Zentrale Zugriffskontrolle und Routing-Komponente
für alle LLM-Anfragen (implementiert durch LiteLLM). **Funktion:** Abstrahiert verschiedene Modell-Provider,
implementiert Kostenmanagement, Logging und Rate-Limiting.

### Vektordatenbank

**Verwendung:** Vektordatenbank **English:** Vector Database **Definition:** Spezialisierte Datenbank für
hochdimensionale Vektorrepräsentationen (Embeddings), optimiert für semantische Ähnlichkeitssuche (implementiert durch
Milvus).

## Rechtliche und Compliance-Begriffe

### Datensouveränität

**Verwendung:** Datensouveränität **English:** Data Sovereignty **Definition:** Das Prinzip, dass Daten den Gesetzen und
Vorschriften des Landes unterliegen, in dem sie gespeichert werden. Im Schweizer Kontext: Daten verbleiben physisch in
der Schweiz und unterliegen Schweizer Recht.

### PII (Personenidentifizierbare Informationen)

**Verwendung:** Personenidentifizierbare Informationen (PII) **English:** Personally Identifiable Information (PII)
**Definition:** Daten, die zur Identifikation einer natürlichen Person verwendet werden können (z.B. Name, E-Mail,
AHV-Nummer). **Kontext:** Swiss AI Hub nutzt Presidio zur automatischen Erkennung und Anonymisierung von PII.

## Technische Konzepte

### Retrieval-Augmented Generation (RAG)

**Verwendung:** Retrieval-Augmented Generation (RAG) **English:** Retrieval-Augmented Generation (RAG) **Definition:**
KI-Architekturmuster, bei dem ein LLM mit relevantem Kontext aus einer Wissensdatenbank angereichert wird, bevor es eine
Antwort generiert. **Vorteil:** Reduziert Halluzinationen, ermöglicht Zugriff auf aktuelle Unternehmensdaten ohne
Model-Retraining.

### Workflow-basierter Agent

**Verwendung:** Workflow-basierter Agent **English:** Workflow-based Agent **Definition:** Ein KI-Agent, dessen
Entscheidungsprozess einem definierten, nachvollziehbaren Workflow folgt (im Gegensatz zu autonomen
"Black-Box"-Agenten). **Vorteil:** Transparenz, Auditierbarkeit, kontrolliertes Verhalten (keine unvorhersehbaren
Aktionen).

### Closed Workflow

**Verwendung:** Closed Workflow **English:** Closed Workflow **Definition:** Ein deterministischer Agenten-Workflow mit
definierten Schritten und Pfaden, ohne offene Entscheidungsschleifen. **Kontext:** Swiss AI Hub verwendet Closed
Workflows, um Vertrauen und Kontrollierbarkeit zu gewährleisten.

## Stilistische Hinweise

- **Konsistente Groß-/Kleinschreibung:** Achten Sie auf die im Glossar definierte Schreibweise (z.B. "Agenten-Profil"
  nicht "Agentenprofil").
- **Bindestriche:** Verwenden Sie Bindestriche bei zusammengesetzten Begriffen wie angegeben (z.B.
  "Daten-zu-Wissen-Pipeline").
- **Englische Begriffe:** Verwenden Sie bei etablierten technischen Begriffen die englische Bezeichnung in Klammern bei
  der ersten Nennung (z.B. "Wissensdatenbank (Knowledge Base)").
- **Plural-Formen:** Beachten Sie die korrekten Plural-Formen (Superusers, Administratoren, Mandanten).
