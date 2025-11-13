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

## Textfluss und Whitepaper-Charakteristik

### Vollständige Sätze bevorzugen
**WICHTIG**: Ein Whitepaper ist ein Fließtext-Dokument, kein Präsentations-Foliensatz. Schreiben Sie in vollständigen, zusammenhängenden Sätzen statt Stichpunkten.

**❌ Vermeiden Sie inflationäre Bulletpoints**:
```
Die Plattform bietet:
- Moderne Benutzeroberfläche
- Multi-Kanal-Zugang
- Kontext-Erhaltung
- Intuitive Bedienung
```

**✅ Schreiben Sie stattdessen in Fließtext**:
```
Die Plattform bietet Mitarbeitern eine moderne, ChatGPT-ähnliche Benutzeroberfläche, die über verschiedene Kanäle zugänglich ist – sei es über Webbrowser, Microsoft Teams, Slack oder E-Mail. Das System erhält dabei den Kontext über mehrere Gesprächsrunden hinweg und ermöglicht eine intuitive Bedienung ohne umfangreiche Schulungen.
```

### Wann Bulletpoints verwenden
Setzen Sie Aufzählungen **nur gezielt** ein für:
- **Technische Spezifikationen**: Unterstützte Formate, Protokolle, Standards
- **Feature-Listen**: Wenn 5+ ähnliche Punkte aufgelistet werden müssen
- **Checklisten**: RFP-Anforderungen, Compliance-Kriterien
- **Vergleichstabellen**: Deployment-Optionen, Lizenzmodelle

**Faustregel**: Maximum 1-2 Bulletpoint-Listen pro Unterabschnitt. Alles andere in Fließtext.

### Natürlicher Textfluss
**Verbinden Sie Gedanken durch Übergänge**:

❌ **Abgehackt (wie AI-Text)**:
```
Die Plattform unterstützt mehrere Authentifizierungsmethoden. OIDC wird unterstützt.
SAML ist verfügbar. OAuth2 kann genutzt werden. On-Premise Kerberos ist möglich.
```

✅ **Fließend (wie menschlicher Text)**:
```
Für die Authentifizierung bietet die Plattform umfassende Flexibilität. Cloud-basierte
Organisationen können moderne Standards wie OIDC, SAML oder OAuth2 nutzen, während
On-Premise-Installationen auch Kerberos und mTLS unterstützen. Diese Vielfalt ermöglicht
die nahtlose Integration in bestehende Unternehmens-Infrastrukturen.
```

### Absatzstruktur für Lesbarkeit
Jeder Absatz sollte:
1. **Eine Hauptaussage haben** (im ersten oder zweiten Satz)
2. **Diese ausführen** (durch Beispiele, Details, Nutzen)
3. **Zum nächsten Gedanken überleiten** (letzter Satz als Brücke)

**Beispiel für guten Absatzfluss**:
```
Die Multi-Tenant-Architektur der Plattform gewährleistet strikte Datenisolation zwischen
verschiedenen Abteilungen. Jede Organisationseinheit erhält einen eigenen, abgeschotteten
Bereich für ihre Dokumente und Konversationen. Diese Trennung erfolgt auf mehreren Ebenen:
in der Datenbank durch separate Collections, in der Vektordatenbank durch Namespaces und
auf Container-Ebene durch dedizierte Ressourcen. Damit bleiben sensible HR-Dokumente für
die Finanzabteilung ebenso unerreichbar wie Vertragsdaten für das Marketing – ohne dass
Administratoren jeden Zugriff manuell konfigurieren müssen.

Diese automatisierte Isolation reduziert nicht nur Sicherheitsrisiken, sondern vereinfacht
auch die Verwaltung erheblich. [Übergang zum nächsten Thema...]
```

### Kompakter aber lesbarer Stil
**Balance zwischen Prägnanz und Verständlichkeit**:

❌ **Zu telegrafisch**:
```
Deployment: 30 Min. Kubernetes. Docker Compose verfügbar. GPU optional.
```

❌ **Zu ausschweifend**:
```
Die Plattform kann in einer sehr kurzen Zeitspanne in Betrieb genommen werden, was
insbesondere für Organisationen von Vorteil ist, die schnell produktiv werden möchten.
Die Deployment-Zeit liegt bei etwa 30 Minuten, sofern Kubernetes als Container-
Orchestrierungsplattform verwendet wird. Alternativ steht auch Docker Compose zur
Verfügung. Bei Bedarf können auch GPU-Ressourcen eingebunden werden.
```

✅ **Kompakt und lesbar**:
```
Die Plattform ist in 30 Minuten einsatzbereit – ob mit Kubernetes für produktive
Umgebungen oder Docker Compose für Entwicklung und Tests. Bei Bedarf können GPU-
Ressourcen für lokale Modelle eingebunden werden.
```

### Variation für natürlichen Rhythmus
**Vermeiden Sie monotone Satzmuster**:

❌ **Monoton (typisch AI)**:
```
Die Plattform bietet Verschlüsselung. Die Plattform bietet Zugriffskontrolle.
Die Plattform bietet Audit-Logging. Die Plattform bietet Backup-Funktionen.
```

✅ **Variiert (natürlich)**:
```
Sicherheit ist in die Plattform integriert: TLS 1.3 verschlüsselt alle Datenübertragungen,
während granulare Zugriffskontroollen jeden API-Aufruf autorisieren. Jede Aktion wird im
Audit-Log festgehalten, und automatische Backups schützen vor Datenverlust.
```

### Konkrete Beispiele statt Abstraktionen
**Zeigen Sie, beschreiben Sie nicht nur**:

❌ **Abstrakt**:
```
Die Plattform ermöglicht verschiedene Anwendungsfälle in unterschiedlichen Branchen.
```

✅ **Konkret**:
```
Ein Versicherungsunternehmen nutzt die Plattform, um Schadensmeldungen automatisch zu
kategorisieren und Bearbeitern relevante Policen-Klauseln anzuzeigen. Eine Behörde
beantwortet damit Bürgeranfragen auf Basis aktueller Gesetzestexte und Verordnungen.
```

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

### Kapitelaufbau für Standalone-Lesbarkeit

**KRITISCH**: Jedes Kapitel muss **eigenständig lesbar** sein, aber auch im Gesamtkontext funktionieren.

**Kapitelstruktur:**

1. **Einleitung** (1 Absatz, max. 150 Wörter):
   - Was behandelt dieses Kapitel?
   - Warum ist es wichtig? (Business-Relevanz)
   - Für wen ist es relevant? (Zielgruppe signalisieren)
   - **Keine Verweise auf andere Kapitel** - Kapitel muss standalone verständlich sein

2. **Hauptinhalt** (strukturiert in klar getrennte Subsektionen):
   - Verwenden Sie die 3-Typ-Struktur (siehe unten)
   - Jede Subsektion beginnt mit Zweck-Statement
   - Klare Überschriften die Inhalt signalisieren

3. **Zusammenfassung** (optional, 1 Absatz, max. 100 Wörter):
   - Nur wenn Kapitel besonders komplex oder lang
   - Wiederhole nur die 3-5 wichtigsten Punkte
   - Keine neuen Informationen

### Subsektion-Typen: Konzept, Prozess, Technik

**WICHTIG**: Strukturieren Sie Hauptinhalt nach **Informationstypen**, damit Leser erkennen können, was sie überspringen können.

**Typ 1: KONZEPT (Business-orientiert)**
- Überschriften wie: "Was ist...", "Überblick", "Grundprinzipien", "Architektur-Konzept"
- **Zielgruppe**: C-Level, Beschaffung, Compliance Officers
- **Inhalt**: Geschäftlicher Nutzen, Problemlösung, strategischer Wert
- **Stil**: Nicht-technisch, Analogien verwenden
- **Beispiel-Überschrift**: "4.1 Konzept: Wie AI auf Unternehmenswissen zugreift"

**Typ 2: PROZESS (Anwender-orientiert)**
- Überschriften wie: "Wie funktioniert...", "Workflow", "Ablauf", "In der Praxis"
- **Zielgruppe**: Projektleiter, Fachabteilungen, End-User
- **Inhalt**: Benutzererfahrung, Schritt-für-Schritt, Use Cases
- **Stil**: Praktisch, nachvollziehbar, mit Beispielen
- **Beispiel-Überschrift**: "4.2 Prozess: Von Upload bis zur KI-Antwort"

**Typ 3: TECHNIK (IT-orientiert)**
- Überschriften wie: "Technische Umsetzung", "Architektur", "Integration", "Spezifikationen"
- **Zielgruppe**: IT-Architekten, CTO, Sicherheitsteams
- **Inhalt**: Komponenten, Protokolle, Standards, Skalierung
- **Stil**: Technisch präzise, konkrete Werte
- **Beispiel-Überschrift**: "4.3 Technik: Milvus, Docling und RAG-Pipeline"

**Format-Beispiel:**
```markdown
## 4. Wissensmanagement und RAG

[Einleitung: 1 Absatz standalone]

### 4.1 Konzept: Organisationswissen als KI-Grundlage
[Business-orientiert, nicht-technisch]

### 4.2 Prozess: Dokumenten-Upload bis intelligente Antwort
[Anwender-orientiert, praktisch]

### 4.3 Technik: RAG-Architektur und Komponenten
[IT-orientiert, technisch]
```

### Signalisierung für selektives Lesen

**Leser sollen erkennen können, was sie brauchen und was sie überspringen können.**

**Methoden:**

1. **Überschriften explizit machen:**
   - ✅ "5.3 Technik: LlamaIndex Workflows und Event-Architektur"
   - ❌ "5.3 Agent-Architektur" (unklar ob Konzept oder Technik)

2. **Einleitungssatz pro Subsektion:**
   - "Dieser Abschnitt erklärt das Konzept der Workflow-basierten Agents aus Business-Perspektive."
   - "Dieser Abschnitt beschreibt den technischen Aufbau mit konkreten Komponenten."

3. **Zielgruppen-Hinweise (bei Bedarf):**
   - *Für IT-Architekten*: Details zu Kubernetes HPA, Pod-Limits...
   - *Für Compliance Officers*: Retention Policies, GDPR-Workflows...

4. **Visuelle Trennung:**
   - Verwenden Sie `###` Überschriften konsequent für Subsektionen
   - Mindestens 1 Leerzeile vor neuer Subsektion

### Prägnanz und Kompaktheit

**Das Whitepaper ist zu lang geworden. Seien Sie kompakter:**

❌ **Vermeiden Sie Redundanz:**
- Wiederholen Sie nicht, was in anderen Subsektionen steht
- Keine mehrfache Erklärung desselben Konzepts
- Nicht jeden Satz mit "Die Plattform..." beginnen

❌ **Vermeiden Sie Füllwörter:**
- "Es ist wichtig zu betonen, dass..."
- "In diesem Zusammenhang sollte erwähnt werden..."
- "Wie bereits erwähnt..."

✅ **Direkter Stil:**
- Gehen Sie direkt zum Punkt
- Ein Konzept = Ein Absatz (wenn möglich)
- Fassen Sie sich kurz, aber bleiben Sie präzise

**Beispiel Vorher (zu ausschweifend, 120 Wörter):**
```
Die Plattform bietet umfassende Authentifizierungsmöglichkeiten, die es Organisationen
ermöglichen, ihre bestehenden Identity-Management-Systeme nahtlos zu integrieren. Für
Cloud-basierte Organisationen stehen moderne Standards wie OIDC und SAML zur Verfügung.
Diese ermöglichen Single Sign-On und zentralisierte Benutzerverwaltung. Für On-Premise-
Installationen unterstützt die Plattform auch Kerberos sowie mTLS-basierte Authentifizierung.
Dies gewährleistet, dass auch Organisationen mit Legacy-Systemen die Plattform nutzen können.
Die Vielfalt dieser Authentifizierungsoptionen ermöglicht es jeder Organisation, unabhängig
von ihrer bestehenden Infrastruktur, die Plattform sicher zu nutzen.
```

**Beispiel Nachher (kompakt, 65 Wörter):**
```
Für die Authentifizierung unterstützt die Plattform moderne Standards (OIDC, SAML, OAuth2)
für Cloud-Umgebungen sowie Kerberos und mTLS für On-Premise-Installationen. Single Sign-On
ermöglicht nahtlose Integration in bestehende Identity-Management-Systeme – ohne dass
Benutzer separate Credentials verwalten müssen. Diese Flexibilität deckt sowohl moderne
als auch Legacy-Infrastrukturen ab.
```

### Absätze als Fließtext
- **Länge**: 3-6 Sätze pro Absatz (80-150 Wörter)
- **Struktur**: Hauptaussage → Erläuterung → Beispiel/Nutzen → Überleitung
- **Verbindung**: Jeder Absatz baut auf dem vorherigen auf
- **Rhythmus**: Wechseln Sie zwischen kurzen (3 Sätze) und längeren (5-6 Sätze) Absätzen

### Wann Formatierung verwenden
- **Fettschrift**: Sparsam nur für kritische Konzepte beim ersten Auftreten
- **Bulletpoints**: Nur für technische Specs, Feature-Listen (5+ Punkte), Compliance-Checklisten
- **Nummerierung**: Nur für sequenzielle Prozesse oder Schritte
- **Code/Konfiguration**: Nur wenn technische Details explizit verlangt sind

**Grundregel**: Wenn es in einem Satz oder kurzen Absatz ausgedrückt werden kann, schreiben Sie keinen Bulletpoint!

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

### Typische AI-Schreibmuster vermeiden
**Diese Muster lassen Text künstlich wirken**:

❌ **Inflationäre Bulletpoints statt Fließtext**
- Jeder Punkt eine Zeile
- Keine Satzverbindungen
- Listencharakter dominiert

❌ **Repetitive Satzstrukturen**
- "Die Plattform bietet X. Die Plattform bietet Y. Die Plattform bietet Z."
- Immer gleicher Satzbau
- Mechanisch und monoton

❌ **Übertriebene Strukturierung**
- Zu viele Unterüberschriften
- Jeder Absatz mit Fettschrift-Header
- Mehr Formatierung als Inhalt

❌ **Generische Übergangssätze**
- "Darüber hinaus...", "Des Weiteren...", "Zusätzlich..." (übermäßig häufig)
- "Es ist wichtig zu beachten, dass..."
- "In diesem Zusammenhang ist anzumerken..."

❌ **Redundante Zusammenfassungen**
- "Zusammenfassend lässt sich sagen..."
- Wiederholung des gerade Gesagten
- Unnatürliche "Meta-Kommentare"

✅ **Schreiben Sie stattdessen wie ein Mensch**:
- Variieren Sie Satzstrukturen und -längen
- Verwenden Sie Fließtext mit gezielten Aufzählungen
- Verbinden Sie Gedanken natürlich (durch Kontext, nicht durch "Des Weiteren")
- Vermeiden Sie übermäßige Strukturierung
- Gehen Sie direkt zum Punkt ohne Meta-Kommentare

## Qualitätskriterien

Ein gutes Kapitel erfüllt diese Kriterien:
- ✅ Für Nicht-Techniker verständlich
- ✅ Geschäftlicher Nutzen immer klar
- ✅ Konkrete Beispiele und Szenarien
- ✅ RFP-Anforderungen natürlich integriert
- ✅ Schweizer Kontext angemessen berücksichtigt
- ✅ **Primär Fließtext** mit gezielten Bulletpoints (max. 1-2 Listen pro Unterabschnitt)
- ✅ **Natürlicher Schreibstil** ohne typische AI-Muster (keine Repetition, keine generischen Übergänge)
- ✅ **Variierter Satzbau** (kurze, mittlere und lange Sätze gemischt)
- ✅ Flüssig lesbar, logischer Aufbau
- ✅ Professioneller, vertrauenswürdiger Ton
- ✅ Nachvollziehbare Argumentation
- ✅ Angemessene Länge (nicht zu knapp, nicht aufgebläht)
- ✅ Sinnvolle Übergänge zu anderen Kapiteln

### Selbst-Check: "Klingt das wie von einem Menschen geschrieben?"
- Würde ein Geschäftsführer so schreiben? (nicht wie ein Chatbot)
- Sind Absätze verbunden oder aneinandergereiht?
- Gibt es inflationäre Bulletpoints wo Fließtext besser wäre?
- Variieren Satzlänge und -struktur oder ist es monoton?

## Längen-Richtlinien

**WICHTIG**: Das Whitepaper ist zu lang geworden. Seien Sie **prägnant und kompakt**.

**Neue, reduzierte Ziel-Längen:**
- **Kurze Kapitel** (2-3 Seiten): ~**600-900 Wörter** (nicht mehr als 1000)
- **Mittlere Kapitel** (3-5 Seiten): ~**900-1500 Wörter** (nicht mehr als 1600)
- **Lange Kapitel** (5-7 Seiten): ~**1500-2100 Wörter** (nicht mehr als 2200)

Eine Seite entspricht etwa 300 Wörtern im fertigen Layout.

**Faustregel**:
- Wenn Kapitelprompt "3-5 Seiten" sagt → Ziele auf **1200 Wörter**
- Wenn Kapitelprompt "5-7 Seiten" sagt → Ziele auf **1800 Wörter**
- **Nie mehr als 2200 Wörter** pro Kapitel

**Wie kürzen:**
- Redundanz eliminieren
- Ein Konzept = Ein Absatz
- Füllwörter streichen
- Direkt zum Punkt kommen
- Beispiele kompakt halten (max. 2-3 Sätze)

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
- **Selektiv lesen** (nur relevante Subsektionen)

### Ihr Schreibauftrag

Erstellen Sie ein **professionelles Whitepaper-Kapitel** mit folgenden Eigenschaften:

**Struktur:**
- ✅ **Standalone lesbar** - Kapitel funktioniert ohne andere Kapitel
- ✅ **Klar strukturiert** - Konzept/Prozess/Technik-Subsektionen mit expliziten Überschriften
- ✅ **Signalisierend** - Leser erkennen sofort, was für sie relevant ist
- ✅ **Kompakt** - Ziel-Wortanzahl einhalten (siehe Längen-Richtlinien)

**Stil:**
- ✅ **Primär Fließtext** (nicht Bulletpoint-Folie)
- ✅ **Kompakt und prägnant** (keine Redundanz, keine Füllwörter)
- ✅ **Natürlicher Rhythmus** (variieren Sie Satzlänge und -struktur)
- ✅ **Menschlich wirkend** (vermeiden Sie typische AI-Schreibmuster)
- ✅ **Konkret und belegt** (Fakten, nicht Versprechungen)

**Inhalte:**
- ✅ **Business-Nutzen klar** (immer verbinden mit geschäftlichem Wert)
- ✅ **Technisch wenn nötig** (Details nur für IT-Zielgruppe)
- ✅ **Schweizer Kontext** (Datensouveränität, revDSG, Mehrsprachigkeit)

**KRITISCH**:
- Jedes Wort muss einen Zweck erfüllen
- Kapitel muss eigenständig lesbar sein
- Leser müssen erkennen können, welche Subsektionen sie überspringen können
- Bleiben Sie innerhalb der Ziel-Wortanzahl

**Denken Sie daran**: Dies ist kein Marketing-Material und keine Präsentation, sondern ein sachliches Whitepaper-Dokument für fundierte Geschäftsentscheidungen.
