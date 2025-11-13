# Kapitel 03: Datensouveränität und vollständige Kundenkontrolle

## Kapitelziel
Erklären Sie, wie die Plattform vollständige Kontrolle über Daten und AI-Systeme gewährleistet und Datensouveränitäts-Anforderungen erfüllt (1200 Wörter, 4 Seiten).

**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **lang** (1200 Wörter).

## Business-Dimensionen (Priorität für dieses Kapitel)
1. **DATENSCHUTZ** - SEHR WICHTIG: Datensouveränität, Schweizer Hosting, Data Residency
2. **ZUKUNFTSSICHERHEIT** - Sehr wichtig: Vendor-Unabhängigkeit, modulare Architektur, Komponentenaustauschbarkeit
3. **MANAGEMENT** - Wichtig: Governance-Mechanismen, RBAC-Kontrolle, Administrative Autonomie
4. **SICHERHEIT** - Wichtig: Isolation, Air-Gap-Betrieb, Zugriffskontrolle

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

## Themen und Inhalte

Beschreiben Sie folgende Themen und deren geschäftlichen Nutzen:

- **Deployment-Optionen für vollständige Datensouveränität**: Schweizer Hosting (dedizierte Cloud-Infrastruktur in ISO-zertifizierten Schweizer Rechenzentren), On-Premise-Deployment (Integration mit bestehenden Datenbanken MSSQL/Oracle/PostgreSQL), Isolierte Infrastruktur (keine Shared-Tenancy, vollständige Netzwerk-Isolation), Air-Gap-Betrieb (ohne Internetverbindung für höchste Sicherheit), Hybrid-Szenarien (Kombination verschiedener Deployment-Modelle je nach Datensensitivität); Geschäftlicher Nutzen: Vollständige Compliance mit revDSG und Data-Residency-Anforderungen, keine Abhängigkeit von externen Cloud-Providern, Anpassung an organisatorische Sicherheitsrichtlinien, Vertrauensbildung bei regulierten Branchen und öffentlicher Verwaltung

- **Kundenkontrolle über Administration und Konfiguration**: RBAC-basierte Administration (kundenseitige Administrationsrollen mit granularen Berechtigungen), Datenquellen-Kontrolle (volle Steuerung über Datenfluss und -nutzung), RAG-Konfiguration (Kontrolle über Vector-Stores, Chunking-Strategien, Retrieval-Parameter), AI-Modell-Kontrolle (Entscheidung über eingesetzte Modelle, Training, Fine-Tuning, Versionierung), Governance-Mechanismen (Feedback-Systeme, Bias-Monitoring, Human-in-the-Loop-Prozesse); Geschäftlicher Nutzen: Keine Black-Box mit voller Transparenz und Steuerung, Anpassung an interne Governance-Anforderungen, Risikominimierung durch menschliche Aufsicht über kritische AI-Entscheidungen, kontinuierliche Qualitätssicherung

- **Compliance-Funktionen und Datenschutz-Mechanismen**: Anonymisierung (automatische PII-Erkennung und Pseudonymisierung vor AI-Verarbeitung), Consent-Management (granulare Einwilligungsverwaltung), Lösch-Workflows (vollständige Datenentfernung/Right to be Forgotten über alle Systemkomponenten), Audit-Trails (unveränderliche zeitgestempelte Logs aller Datenverarbeitungsaktivitäten), Data Lineage (Nachverfolgung von Daten vom Ursprung bis zur Nutzung), eGov-Integration (Anbindung an staatliche Identitätssysteme und Compliance-Plattformen); Geschäftlicher Nutzen: Erfüllung von revDSG/GDPR/AI Act Anforderungen, Reduzierung von Compliance-Risiken und rechtlicher Exposition, Erleichterung von Audits, Vertrauen von Bürgern und Kunden

- **Vendor-Unabhängigkeit durch modulare Architektur**: Open-Source-Basis (Apache 2.0 Lizenzierung, transparenter Code), Standardbasierte Schnittstellen (REST APIs, OpenTelemetry, OAuth/OIDC), Komponentenaustauschbarkeit (Datenbanken, Vector-Stores, LLM-Provider, Authentifizierungssysteme austauschbar), Multi-Provider-Support (gleichzeitige Nutzung verschiedener LLM-Anbieter), keine proprietären Formate (Daten jederzeit exportierbar); Geschäftlicher Nutzen: Langfristige Investitionssicherheit ohne Abhängigkeit von einzelnen Anbietern, Flexibilität bei Technologiewechsel ohne System-Neubau, Verhandlungsstärke gegenüber Lieferanten, Anpassung an sich ändernde regulatorische/technische Anforderungen

## Business-Fragen, die das Kapitel beantwortet

### Deployment und Datensouveränität
1. Welche Deployment-Optionen bietet die Plattform zur Sicherstellung der Datensouveränität?
2. Kann die Plattform vollständig in der Schweiz betrieben werden, ohne dass Daten ins Ausland übertragen werden?
3. Unterstützt die Plattform On-Premise-Deployment mit unseren bestehenden Datenbanken (MSSQL, Oracle, PostgreSQL)?
4. Was ist Air-Gap-Betrieb und wann ist er erforderlich?
5. Wie stellt die Plattform sicher, dass keine Daten unkontrolliert die Schweiz verlassen?
6. Können wir verschiedene Deployment-Modelle für unterschiedliche Datensensitivitäten kombinieren?

### Kontrolle und Governance
7. Wer kontrolliert die Administration der Plattform – wir oder der Anbieter?
8. Wie funktioniert die rollenbasierte Zugriffskontrolle (RBAC) und welche Rollen sind verfügbar?
9. Welche Kontrolle habe ich über Datenquellen und RAG-Konfigurationen?
10. Kann ich kontrollieren, welche AI-Modelle verwendet werden und wie sie trainiert werden?
11. Wie stelle ich sicher, dass AI-Entscheidungen von Menschen überprüft werden können (Human-in-the-Loop)?
12. Welche Governance-Mechanismen sind eingebaut (Feedback, Bias-Monitoring)?

### Compliance und Datenschutz
13. Wie erfüllt die Plattform revDSG-Anforderungen?
14. Unterstützt die Plattform Anonymisierung sensibler Daten (PII-Erkennung)?
15. Wie wird Consent-Management gehandhabt?
16. Können Daten vollständig gelöscht werden (Right to be Forgotten / Art. 17 DSGVO)?
17. Wie werden Audit-Trails für Compliance-Nachweise bereitgestellt?
18. Unterstützt die Plattform Data Lineage für regulatorische Audits?
19. Wie integriert sich die Plattform mit eGov-Portalen und staatlichen Identitätssystemen?

### Vendor Lock-in und Erweiterbarkeit
20. Verhindert die Architektur Vendor Lock-in?
21. Können einzelne Komponenten (Datenbank, Vector-Store, LLM-Provider) ausgetauscht werden?
22. Basiert die Plattform auf offenen Standards oder proprietären Technologien?
23. Sind unsere Daten jederzeit exportierbar und in anderen Systemen nutzbar?
24. Kann ich mehrere LLM-Anbieter gleichzeitig nutzen?

## Relevante RFP-Anforderungen

Während des natürlichen Schreibens sicherstellen, dass das Kapitel diese Anforderungen addressiert:

- **"Swiss Hosting / Swiss cloud"** ✓
- **"Hosting in der Schweiz, Datenresidenz Schweiz"** ✓
- **"On-Premise-Deployment, Installation auf unseren Servern"** ✓
- **"Air-Gap-Betrieb ohne Internetverbindung"** ✓
- **"Datenschutzkonformer Betrieb nach revDSG"** ✓
- **"RBAC-basierte Zugriffskontrolle und Administration"** ✓
- **"Kontrolle über Datenquellen und Konfiguration"** ✓
- **"Human-in-the-Loop-Mechanismen"** ✓
- **"Bias-Monitoring und Feedback-Systeme"** ✓
- **"Anonymisierung sensibler Daten"** ✓
- **"Consent-Management für Datennutzung"** ✓
- **"Right to be Forgotten / Vollständige Lösch-Workflows"** ✓
- **"Audit-Trails und Data Lineage"** ✓
- **"Nicht rein proprietäre Lösung, offene Standards"** ✓
- **"Austausch einzelner Systembausteine ohne Herstellerbindung"** ✓
- **"Integration von Open-Source-Modulen"** ✓
- **"Integration mit eGov-Portalen"** ✓
