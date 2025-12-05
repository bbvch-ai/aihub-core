# Plattform-Überblick - Die Swiss AI-Hub-Lösung

## Enterprise-KI-Infrastruktur als Produkt

Die Fragmentierung der IT-Landschaft stellt IT-Entscheidungsträger heute vor enorme Herausforderungen. Oft müssen
Komponenten wie Vektordatenbanken, API-Gateways, Ingestion-Pipelines und Benutzeroberflächen separat evaluiert,
lizensiert und mühsam integriert werden. Dies bindet Ressourcen und verzögert die Wertschöpfung. Unternehmen benötigen
eine Lösung, welche die Lücke zwischen reinen Software-Frameworks – die Entwickler erst zusammensetzen müssen – und
externen SaaS-Diensten, die keine Datenkontrolle bieten, schliesst.

Der Swiss AI Hub beantwortet diese Anforderung als vollständige, produktionsreife KI-Infrastruktur, die Organisationen
als Produkt erwerben. Anstatt Basisinfrastruktur neu zu erfinden, liefert die Plattform ein harmonisiertes Gesamtsystem.
Technisch wird dies durch eine containerisierte Architektur realisiert, die mittels Docker Compose oder Kubernetes
bereitgestellt wird. Sie transformiert KI-Modelle in sichere, nutzbare Unternehmensanwendungen und übergibt die volle
Kontrolle über Deployment und Betrieb an den Kunden.

## Der «Batteries Included»-Ansatz: Sofortige Betriebsbereitschaft

Ein Sprachmodell allein bildet noch keine Geschäftsanwendung; oft fehlen essentielle Hilfssysteme wie Authentifizierung
oder Dokumentenverarbeitung. Dies führt dazu, dass Unternehmen Monate in Beschaffungsprozessen und Integrationsarbeit
verlieren. Um die Implementierungszeit drastisch zu verkürzen, verfolgt der Swiss AI Hub einen konsequenten «Batteries
Included»-Ansatz: Die Plattform integriert Best-in-Class Open-Source-Komponenten, die vorkonfiguriert und aufeinander
abgestimmt sind.

In der technischen Umsetzung im Swiss AI Hub bedeutet dies, dass komplexe Integrationsarbeit bereits geleistet wurde:

- **LiteLLM** fungiert als vereinheitlichtes LLM-Gateway zur Anbindung beliebiger Modelle mit integriertem Failover und
  Kosten-Tracking.
- **Milvus** steht als leistungsfähige Vektordatenbank für die semantische Suche bereit.
- **Dagster** orchestriert robuste Datenpipelines, während **Docling** die Dokumentenverarbeitung (Parsing von PDFs und
  Office-Dateien) übernimmt.
- **NATS** sorgt als Messaging-System für eine skalierbare, ereignisgesteuerte Architektur.
- **Phoenix** gewährleistet vollständige Observability und Tracing bis in die tiefsten Agenten-Entscheidungen.
- **Presidio** übernimmt die automatische Erkennung und Maskierung von PII (Personenidentifizierbare Informationen).

## Skalierbare Fähigkeiten durch das Stufenmodell

Die Einführung von KI ist ein Reifeprozess, der eine Organisation nicht überfordern darf. Es gilt, KI-Kompetenzen
schrittweise aufzubauen und Medienbrüche zu vermeiden. Der Swiss AI Hub unterstützt diesen Pfad durch eine Architektur,
die in logischen Stufen (Tiers) mit den Anforderungen wächst:

- **Stufe 1 (Zugang & Kompetenz):** Die Plattform bietet über eine sichere Web-Oberfläche (Open-WebUI) Zugang zu
  Sprachmodellen. Alle Anfragen werden zentral authentifiziert und via LiteLLM geleitet, um Prompting-Kompetenzen sicher
  aufzubauen.
- **Stufe 1+ (Integration):** Um KI direkt in den Arbeitsfluss zu bringen, bindet das System über das **Azure Bot
  Framework** Kanäle wie Microsoft Teams, Slack oder Outlook an. Die KI agiert dort, wo die Mitarbeitenden arbeiten.
- **Stufe 2 (Kontext & Wissen):** Für unternehmensspezifisches Wissen aktiviert die Plattform RAG-Fähigkeiten. Agenten
  greifen auf die Wissensdatenbank zu, die durch die Daten-zu-Wissen-Pipeline gespeist wird. Über das **Model Context
  Protocol (MCP)** können sich Agenten zudem sicher und standardisiert mit externen Tools verbinden.
- **Stufe 3 (Prozess-Orchestrierung):** Die höchste Ausbaustufe automatisiert komplexe Geschäftsprozesse. Ein
  dedizierter Orchestrator koordiniert Workflows, in denen KI-Agenten, Menschen und externe Systeme interagieren.
  Integrationen zu Power Automate oder UiPath (via n8n) ermöglichen hierbei die Einbindung von Legacy-Systemen.

## Plattform und SDK: Das Komplettpaket für Entwickler

Um «Schatten-IT» und Sicherheitslücken zu vermeiden, ist eine strikte Trennung zwischen Infrastruktur und
Anwendungslogik notwendig. Entwickler sollten sich nicht mit Authentifizierungsprotokollen oder Datenbankverbindungen
aufhalten müssen. Die Plattform stellt daher die fundamentale Basis bereit (Authentifizierung via OAuth2, Monitoring,
Zugriffskontrollen), während das zugehörige Software Development Kit (SDK) die Entwicklung der Geschäftslogik
fokussiert.

Wer mit dem SDK des Swiss AI Hub entwickelt, erbt automatisch die Fähigkeiten der Plattform. Ein neuer Agent muss keine
eigene Benutzerverwaltung implementieren; er nutzt die bereitgestellten Ressourcen sicher und konform. Dies reduziert
die Komplexität massiv: Sie schreiben die Logik für den Agenten, die Plattform kümmert sich um Security, Skalierung und
Audit-Trails.

## Unabhängigkeit und Investitionsschutz durch Open Source

Aus kaufmännischer Sicht eliminieren Unternehmen mit dieser Lösung die Risiken klassischer Cloud-Modelle, wie laufende
Lizenzgebühren pro Benutzer (Per-User-Fees) oder undurchsichtige Kostenstrukturen. Investitionssicherheit entsteht durch
Unabhängigkeit. Da der Swiss AI Hub auf der Apache 2.0 Lizenz basiert, gehört der Quellcode Ihnen. Sie investieren in
Ihre eigene Infrastruktur, nicht in die Miete einer Software.

Dies verhindert einen Vendor-Lock-in effektiv. Sollte sich die Preisstrategie eines Modell-Anbieters ändern, erlaubt die
modulare Architektur den Austausch einzelner Komponenten – etwa den Wechsel von einem OpenAI-Modell zu einem lokalen
Mistral-Modell via vLLM – ohne Anpassung der Applikationslogik. Da die Plattform auf offenen Standards wie S3, OAuth2
und OpenTelemetry basiert, bleibt Ihre Organisation jederzeit kompatibel und handlungsfähig. Selbst wenn der
Plattform-Anbieter vom Markt verschwinden würde, besitzen Sie ein funktionierendes, wartbares System.
