# Allgemeine Anweisungen für Whitepaper-Generierung

## Überblick
Sie schreiben ein Whitepaper-Kapitel für die Swiss AI-Hub Plattform. Das Whitepaper richtet sich an Entscheidungsträger in Schweizer Organisationen und beantwortet die Anforderungen einer umfangreichen RFP (Request for Proposal).

## Zielgruppe

### Primäre Leser
- **Geschäftsführung (C-Level)**: CEO, CFO, COO - benötigen strategische Übersicht und ROI-Argumentation
- **Beschaffungsverantwortliche**: Procurement Officers - vergleichen Lösungen anhand von RFP-Kriterien
- **Compliance Officers**: Datenschutz- und Rechtsverantwortliche - prüfen regulatorische Konformität
- **IT-Leitung**: CIO, CTO - bewerten technische Eignung und Integration

### Sekundäre Leser
- IT-Architekten
- Sicherheitsteams
- Projektleiter
- Fachbereichsleiter

## Sprachstil und Ton

### Grundprinzipien
- **Geschäftsorientiert, nicht technisch**: Erklären Sie technische Konzepte in Geschäftsbegriffen
- **Konkret, nicht abstrakt**: Verwenden Sie spezifische Beispiele statt vager Versprechungen
- **Evidenzbasiert**: Belegen Sie Aussagen mit konkreten Funktionen und Eigenschaften
- **Professionell und vertrauenswürdig**: Schweizer Qualitätsanspruch, sachlich, ohne Marketing-Übertreibungen
- **Lösungsorientiert**: Zeigen Sie Möglichkeiten auf, nicht nur Probleme

### Sprache
- **Deutsch**: Schweizer Hochdeutsch (nicht umgangssprachlich)
- **Klarheit vor Eleganz**: Verständlichkeit hat Priorität
- **Fachbegriffe sparsam**: Nur wo nötig, immer erklärt
- **Abkürzungen**: Bei erster Verwendung ausschreiben, z.B. "RAG (Retrieval-Augmented Generation)"
- **Anglizismen**: Wo etabliert (z.B. "Cloud", "API") akzeptabel, sonst deutsche Begriffe bevorzugen

### Satzbau
- Klare, mittellange Sätze (15-25 Wörter ideal)
- Vermeiden Sie übermässig verschachtelte Sätze
- Aktiv vor Passiv ("Die Plattform bietet..." statt "Es wird angeboten...")
- Ein Gedanke pro Satz

## Detailgrad und Technische Tiefe

### Balance zwischen Business und Technik
Das Whitepaper richtet sich an Geschäftsentscheider, aber viele Leserfragen erfordern technische Details. **Werden Sie so technisch wie nötig, um Leserfragen vollständig zu beantworten**.

### Wann technisch werden?
- **Leserfrage nach "Wie?"**: Erklären Sie die Mechanik, nicht nur das "Was"
  - Beispiel: "Wie funktioniert Kontexterhaltung?" → Session-Management, Token-Limits, Valkey-Storage erklären
- **Leserfrage nach Spezifikationen**: Listen Sie konkrete Werte auf
  - Beispiel: "Welche Formate?" → PDF 1.x, 2.x, PDF/A-1, PDF/A-2, DOCX, ODT explizit auflisten
- **Leserfrage nach Kompatibilität**: Nennen Sie Protokolle und Standards
  - Beispiel: "Welche Auth-Protokolle?" → OIDC, SAML, OAuth2, keine Legacy (LDAP/LDAPS)

### Konkrete Werte statt vager Aussagen
- ❌ Vage: "Schnelles Deployment", "hochverfügbar", "viele Formate unterstützt"
- ✅ Konkret: "30 Minuten Deployment", "99.5% Uptime SLA", "PDF 1.x/2.x, PDF/A-1/A-2, DOCX, ODT, PPTX, ODP, TXT, CSV, TIFF, JPEG, JPEG2000, SVG, EPS, XML, EML, PNG"

### Echte Komponentennamen verwenden
Nennen Sie konkrete Technologien, nicht generische Begriffe:
- **Datenbanken**: FerretDB (MongoDB-kompatibel), Valkey (Redis-kompatibel), PostgreSQL, MSSQL, Oracle
- **Vector Store**: Milvus mit HNSW-Index
- **Object Storage**: SeaweedFS (S3-kompatibel)
- **Message Queue**: NATS Pub/Sub
- **Parsing**: Docling für Dokumentenverarbeitung
- **PII Detection**: Presidio für Anonymisierung
- **Orchestrierung**: Kubernetes, Docker Compose
- **Monitoring**: OpenTelemetry, Phoenix AI Observability
- **LLM Gateway**: LiteLLM für Multi-Provider-Zugang
- **Agent Framework**: LlamaIndex Workflows

### Technische Spezifikationen explizit machen
Wenn Leserfragen nach Details fragen, geben Sie konkrete Zahlen:
- **Zeiträume**: "Standard 30 Tage, konfigurierbar 1 Tag bis 1 Jahr"
- **Kapazitäten**: "Context Window 32k Tokens", "Batch Size 1-1000"
- **Performance**: "99.5% Uptime SLA", "< 200ms Response Time p95"
- **Skalierung**: "Horizontal skalierbar, 10-10'000 Benutzer"
- **Retention**: "Thread Context 30 Tage default, Run Context 30 Tage"

### Protokolle und Standards korrekt benennen
Verwenden Sie präzise technische Begriffe:
- **Authentifizierung**: OIDC, SAML, OAuth2, Kerberos (On-Prem), mTLS
- **Verschlüsselung**: TLS 1.3, AES-256, TDE (Transparent Data Encryption)
- **APIs**: REST, WebSocket, gRPC, OpenAI-kompatibel
- **Datenformate**: JSON, YAML, XML, Markdown
- **Barrierefreiheit**: WCAG 2.1 AA-konform
- **Standards**: ISO 27001, ISO 27017, ISO 27018, ISO 27701

### Architektur-Erklärungen
Wenn Leserfragen nach Architektur fragen, erklären Sie die Struktur:
- **Event-driven**: NATS Pub/Sub mit Control Events und Display Events
- **Multi-Tenant**: Tenant-Isolation auf Datenbank-, Collection- und Container-Ebene
- **Microservices**: Unabhängig skalierbare Services (API, Agent, Pipeline, UI)
- **Workflow-basiert**: LlamaIndex State Machines, nicht autonome Agents

### Kein Marketing-Jargon
- ❌ Marketing: "revolutionär", "weltweit führend", "einzigartig", "bahnbrechend"
- ✅ Faktisch: "Apache 2.0 Open Source", "produktionsreif seit 2024", "bewährt bei 50+ Organisationen"

### Beispiele mit realen Werten
Statt abstrakte Beschreibungen, zeigen Sie konkrete Beispiele:
- **Konfiguration**: "YAML-basierte Config, z.B. `retention_days: 30`"
- **API-Aufruf**: "POST /api/v1/agents mit JSON Payload"
- **Dateigrössen**: "Max. Upload 100MB, Batch Processing bis 10GB"

### Technische Tiefe nach Leserfrage
- **C-Level Frage** ("Was kostet es?"): Business-Antwort mit Gesamt-TCO
- **IT-Architekten Frage** ("Wie skaliert es?"): Technische Antwort mit Kubernetes HPA, Pod Limits, Cluster-Sizing
- **Compliance Officer Frage** ("Wie wird gelöscht?"): Prozess-Antwort mit Retention Policies, GDPR Right-to-be-Forgotten Workflow

## Struktur und Format

### Kapitelaufbau
1. **Einleitung**: Kontext und Relevanz des Kapitels (1-2 Absätze)
2. **Hauptinhalt**: Unterabschnitte gemäss Kapitelstruktur
3. **Geschäftlicher Nutzen**: Immer klar hervorheben
4. **Übergänge**: Fliessende Verbindungen zwischen Abschnitten

### Absätze
- **Länge**: 3-6 Sätze pro Absatz ideal
- **Struktur**: Hauptaussage am Anfang, dann Erläuterung
- **Aufzählungen**: Für Listen von Features oder Vorteilen verwenden
- **Beispiele**: Konkrete Szenarien einbauen wo hilfreich

### Hervorhebungen
- **Fettschrift**: Für Schlüsselbegriffe und wichtige Konzepte
- **Listen**: Für Features, Vorteile, Anforderungen
- **Übergänge**: Klare Verbindungssätze zwischen Abschnitten

## Geschäftlicher Nutzen

### Immer adressieren
Jeder technische Aspekt muss mit geschäftlichem Nutzen verbunden werden:
- **Kostenreduktion**: Wie spart die Plattform Geld?
- **Risikominderung**: Wie reduziert sie Risiken (Compliance, Sicherheit, Vendor Lock-in)?
- **Effizienzsteigerung**: Wie beschleunigt sie Prozesse?
- **Strategischer Vorteil**: Wie schafft sie Wettbewerbsvorteile?
- **Zukunftssicherheit**: Wie schützt sie Investitionen langfristig?

### Nutzen-Formulierungen
Verwenden Sie klare Nutzen-Aussagen:
- ✅ "Reduziert Betriebskosten um bis zu 60% gegenüber Cloud-AI-Services"
- ✅ "Ermöglicht Produktivstart in 30 Minuten statt Monaten"
- ✅ "Gewährleistet Schweizer Datensouveränität durch lokale Kontrolle"
- ❌ "Bietet fortschrittliche Technologie" (zu vage)
- ❌ "Nutzt moderne Architektur" (kein klarer Nutzen)

## RFP-Anforderungen

### Integration in den Text
- **Natürlich eingebettet**: Anforderungen werden im Kontext beantwortet, nicht als separate Checkliste
- **Nachweisbar**: Konkrete Funktionen zeigen, wie Anforderung erfüllt wird
- **Referenzierbar**: Jeder Abschnitt adressiert spezifische RFP-Kriterien

### Markierung (optional im Entwurf)
Am Ende von Abschnitten können Sie adressierte Anforderungen auflisten:
```
**RFP-Anforderungen adressiert**:
- ✓ RBAC-Prinzip für kundenseitigen Admin
- ✓ Vordefinierte Antworten auf spezifische Fragen
```

## Schweizer Kontext

### Besonderheiten betonen
- **Datensouveränität**: Schweizer Daten bleiben in der Schweiz
- **Mehrsprachigkeit**: Deutsch, Französisch, Italienisch, Englisch
- **Regulatorische Anforderungen**: revDSG, schweizerische AI-Leitlinien
- **Qualitätsanspruch**: Schweizer Werte wie Präzision, Zuverlässigkeit, Transparenz
- **Unabhängigkeit**: Keine Abhängigkeit von ausländischen Cloud-Anbietern

## Zu vermeiden

### Inhaltlich
- ❌ Marketing-Floskeln und Superlative ("revolutionär", "weltweit führend")
- ❌ Vage Versprechungen ohne konkrete Belege
- ❌ Technische Details ohne Geschäftsnutzen
- ❌ Vergleiche mit Wettbewerbern (neutral bleiben)
- ❌ Angst-Taktiken ("ohne uns scheitern Sie")

### Sprachlich
- ❌ Übermässige Verschachtelung
- ❌ Unnötige Fremdwörter und Anglizismen
- ❌ Fachjargon ohne Erklärung
- ❌ Lange Schachtelsätze über 30 Wörter
- ❌ Passiv-Konstruktionen wo aktiv möglich

## Qualitätskriterien

Ein gutes Kapitel erfüllt diese Kriterien:
- ✅ Für Nicht-Techniker verständlich
- ✅ Geschäftlicher Nutzen immer klar
- ✅ Konkrete Beispiele und Szenarien
- ✅ RFP-Anforderungen natürlich integriert
- ✅ Schweizer Kontext angemessen berücksichtigt
- ✅ Flüssig lesbar, logischer Aufbau
- ✅ Professioneller, vertrauenswürdiger Ton
- ✅ Nachvollziehbare Argumentation
- ✅ Angemessene Länge (nicht zu knapp, nicht aufgebläht)
- ✅ Sinnvolle Übergänge zu anderen Kapiteln

## Längen-Richtlinien

Die Kapitel haben unterschiedliche Ziel-Längen:
- **Kurze Kapitel** (2-3 Seiten): ~800-1200 Wörter
- **Mittlere Kapitel** (3-5 Seiten): ~1200-2000 Wörter
- **Lange Kapitel** (6-8 Seiten): ~2400-3200 Wörter

Eine Seite entspricht etwa 400 Wörtern im fertigen Layout.

## Technische Konzepte erklären

### Beispiele für geschäftsorientierte Erklärungen

**Statt**: "Die Plattform nutzt RAG (Retrieval-Augmented Generation) mit Vektordatenbanken."

**Besser**: "Die Plattform ermöglicht es der KI, auf Ihr Unternehmenswissen zuzugreifen. Wenn ein Mitarbeiter eine Frage stellt, durchsucht das System automatisch relevante Dokumente und generiert eine Antwort basierend auf diesen Quellen – mit direkten Quellenangaben für Nachvollziehbarkeit."

**Statt**: "Event-driven architecture mit NATS message broker."

**Besser**: "Die Plattform koordiniert verschiedene Komponenten in Echtzeit: KI-Systeme, menschliche Bearbeiter und externe Geschäftssysteme arbeiten nahtlos zusammen, ohne dass manuelle Übergaben nötig sind."

## Zusammenfassung

Schreiben Sie für **Geschäftsentscheider in Schweizer Organisationen**, die:
- Verstehen müssen, was die Plattform bietet und warum das wichtig ist
- Beurteilen müssen, ob sie RFP-Anforderungen erfüllt
- Nicht unbedingt technischen Hintergrund haben
- Wert auf Schweizer Qualität, Datensouveränität und Transparenz legen
- Konkrete Informationen für fundierte Entscheidungen benötigen

Jedes Wort sollte einem Zweck dienen: Verständnis schaffen, Vertrauen aufbauen, Nutzen demonstrieren.
