# Kapitel 04: Plattform-Transparenz und Prüfbarkeit

Die transformative Kraft der Künstlichen Intelligenz (KI) entfaltet sich am stärksten, wenn Vertrauen und Kontrolle
gegeben sind. Für Schweizer Organisationen, die in einem streng regulierten Umfeld agieren und höchste Anforderungen an
Datensouveränität stellen, ist es unerlässlich, dass KI-Systeme keine undurchsichtigen "Black Boxes" bleiben. Dieses
Kapitel beleuchtet, wie der Swiss AI Hub durchgängige Transparenz und lückenlose Überwachbarkeit über sämtliche
Systemgrenzen und KI-Interaktionen hinweg gewährleistet. Es wird dargelegt, wie Entscheidungsketten der KI bis auf den
einzelnen Verarbeitungsschritt und die genutzte Datenquelle nachvollziehbar gemacht werden, um regulatorische
Anforderungen, interne Compliance-Richtlinien und eine präzise Kostenkontrolle sicher zu erfüllen.

## 1. Transparenz der KI-Entscheidungsketten: Vom Black-Box zum White-Box-Modell

### Mehrwert und Nutzen: Nachvollziehbarkeit schafft Vertrauen

Die grösste Hürde beim Einsatz von KI in sensiblen Geschäftsbereichen ist oft die Intransparenz. Die Frage "Wie ist die
KI zu dieser Antwort gekommen?" bleibt bei vielen Systemen unbeantwortet. Der Swiss AI Hub überwindet diesen
"Black-Box"-Ansatz und schafft Vertrauen durch lückenlose Nachvollziehbarkeit. Für Entscheidungsträger bedeutet dies,
dass sie die Funktionsweise von KI-Agenten verstehen und somit die Akzeptanz und Einführung innovativer Lösungen im
Unternehmen fördern können. Compliance-Teams erhalten die notwendigen Werkzeuge, um sicherzustellen, dass
KI-Entscheidungen den internen und externen Richtlinien entsprechen und jederzeit auditierbar sind. Diese umfassende
Transparenz minimiert das Risiko von unvorhersehbaren oder unverständlichen KI-Outputs und stärkt das Vertrauen in die
eingesetzten Systeme.

### Konzepte & Prozesse: Strukturierte Workflows und hierarchisches Scoping

Die Architektur des Swiss AI Hub basiert auf einem konsequenten Workflow-Ansatz, der komplexe, mehrstufige und
asynchrone KI-Operationen handhabbar macht. Agenten folgen explizit definierten, schrittweisen Prozessen, anstatt
autonom und unkontrollierbar zu agieren. Jeder dieser Schritte kann die volle Leistung der KI nutzen, um zu
argumentieren und Entscheidungen zu treffen, doch der Gesamtpfad bleibt stets durch den vordefinierten Workflow
gesteuert. Dies ist entscheidend für autonome Agenten, die über Minuten, Stunden oder sogar Monate hinweg agieren können
und deren operative Lebensdauer nicht an eine einzelne Benutzeranfrage gebunden ist. Das zugrunde liegende Protokoll ist
ein granularer Vertrag, der jede bedeutsame Aktion als eigenständiges Ereignis definiert, was für detailliertes Tracing
und Debugging unerlässlich ist.

Ein zentrales Element ist die strikte Trennung von **Control Events** und **Display Events** im internen Swiss AI Agent
Protokoll (SAAP). `Control Events` steuern den Workflow und verursachen Zustandsänderungen, während `Display Events`
rein informativ sind und Status, Gedanken oder Zwischenergebnisse an die Benutzeroberfläche liefern, ohne den Logikfluss
zu beeinflussen. Dieses Design sorgt für Robustheit: Ein Fehler in der Darstellungslogik kann den Agentenworkflow nicht
unterbrechen. Gleichzeitig ermöglicht ein hierarchisches Scoping – von `Run`- über `Display`- bis zum `Thread`-Kontext –
eine präzise Kontextualisierung jeder Aktion und damit eine hohe Granularität für Tracing und Debugging. Dieses
hierarchische Scoping bildet auch die Grundlage des Sicherheitsmodells, indem Zugriffe auf der `Thread`-Ebene gewährt
werden.

### Technische Umsetzung im Swiss AI Hub: SAAP und OpenTelemetry-basiertes Tracing

Der Swiss AI Hub implementiert seine transparente Architektur durch das **Swiss AI Agent Protokoll (SAAP)** und nutzt
**OpenInference Semantic Conventions** in Verbindung mit OpenTelemetry für tiefgehende Einblicke. Jeder Agentenlauf
(`Run`) wird mit einer hierarchischen Span-Struktur getraced, die den gesamten Workflow, von der `UserMessageEvent` bis
zum `StopEvent`, abbildet. Individuelle `Step`-Spans zeigen Eingaben, Ausgaben, Verarbeitungszeiten und semantische
Ereignisse. Diese Agenten-Workflows werden über den `AgentRunTracer` strukturiert erfasst.

Der `EventDisplayer` im SDK ermöglicht es Agentenentwicklern, `Display Events` wie `ThoughtEvent` (Einblick in die
Argumentation des Agenten) und `ChunkEvent` (Streaming von Textteilen) an die Benutzeroberfläche zu senden, um den
Denkprozess der KI in Echtzeit sichtbar zu machen. LLM-Aufrufe, Embeddings und Retrieval-Operationen werden mit
spezialisierten semantischen Attributen erfasst. Die Transparenz erstreckt sich auch auf die verwendeten Tools und
externen Systeme: Alle NATS-Messaging, Datenbankoperationen, HTTP-Aufrufe, LLM-Interaktionen und Vektorsuchen werden
durch die `AihubInstrumentor`-Komponente automatisch instrumentiert und in den Traces sichtbar gemacht. Dies eliminiert
blinde Flecken in komplexen verteilten KI-Systemen. Für die visuelle Aufbereitung dieser Informationen während der
Entwicklung bietet die Plattform die **Phoenix UI**, die unter `http://localhost:6006` LLM-spezifische Observability mit
Timeline-Ansichten, Token-Nutzung und Inspektionsmöglichkeiten abgerufener Dokumente bereitstellt.

## 2. Lückenlose Audit-Trails und Data Lineage: Vertrauen durch Beweiskette

### Mehrwert und Nutzen: Regulatorische Sicherheit und nachweisbare Rechtmässigkeit

In regulierten Branchen ist die revisionssichere Protokollierung und die Nachvollziehbarkeit der Datenherkunft keine
Option, sondern eine zwingende Anforderung. Der Swiss AI Hub stellt sicher, dass Organisationen diese Anforderungen
erfüllen und das Vertrauen in ihre KI-Systeme untermauern können. Eine lückenlose Beweiskette für alle KI-Interaktionen
und Systemaufrufe ermöglicht interne Revisionen, forensische Analysen und die Erfüllung gesetzlicher Prüfauflagen. Dies
ist entscheidend, um die Rechtmässigkeit der Datenverarbeitung nachzuweisen und Auskunftsrechte gemäss revDSG (Art. 25)
und DSGVO (Art. 15) umfassend zu unterstützen. Durch die detaillierte Erfassung von Fehler-Traces mit vollem Kontext
wird zudem die Zeit zur Ursachenanalyse drastisch reduziert, was die betriebliche Zuverlässigkeit erhöht.

### Konzepte & Prozesse: Unveränderliche Protokollierung und Kontext-Assoziation

Jede relevante Interaktion innerhalb der Plattform erzeugt einen unveränderlichen Ereignisdatensatz, der im Audit-Trail
erfasst wird. Diese Protokolle dokumentieren, wer, wann, welche Aktion ausgeführt hat und mit welchem Ergebnis. Der
Kontext jedes Ereignisses wird über die hierarchischen Scopes (`Thread`, `Display`, `Run`) präzise zugeordnet. Alle
diese Logs sind zentralisiert, strukturiert und über den OpenTelemetry Collector verarbeitbar.

Besonderes Augenmerk liegt auf der **Data Lineage**: Für RAG-Antworten (Retrieval Augmented Generation) wird exakt
festgehalten, welche spezifischen Quelldokumente, Dokumentversionen oder Text-Chunks als Basis für eine KI-generierte
Antwort dienten. Dies ermöglicht eine transparente Überprüfung der Faktenbasis, minimiert das Risiko von
"Halluzinationen" und stellt eine präzise Zuordnung der Datenherkunft für regulatorische Audits sicher.

### Technische Umsetzung im Swiss AI Hub: Distributed Tracing und Dagster Metadaten

Der Swiss AI Hub nutzt **OpenTelemetry für End-to-End Distributed Tracing**, um jeden Anfragefluss über Dienste, Agenten
und LLM-Interaktionen hinweg zu verfolgen. Jede Operation erhält einen eindeutigen Trace-Identifikator, der alle
zugehörigen Aktivitäten verbindet. Dies umfasst spezialisierte Ereignisse wie `LLMEvent`, `RetrieverEvent` und
`LLMCostEvent`, die detaillierte Metadaten zu LLM-Aufrufen, Prompt-Konstruktionen, Token-Nutzung und abgerufenen
Dokumenten liefern.

Für die Dokumentation der Datenherkunft in Datenpipelines kommt **Dagster UI Monitoring** zum Einsatz. Hier wird eine
visuelle Verfolgung der Asset-Abstammung und -Abhängigkeiten bereitgestellt (`@graph_asset`, `AssetIn`).
Asset-Materialisierungen können mit umfassenden Metadaten angereichert werden, die Details wie Dateigrösse,
Verarbeitungszeit, Dokumentseiten, Textlänge und verwendete Parserversionen erfassen (`context.add_output_metadata`).
Diese Metadaten gewährleisten eine lückenlose Dokumentation der Verarbeitungsschritte und der Herkunft der verwendeten
Dokumente. Alle Traces und Logs, einschliesslich der detaillierten Audit-Protokolle, werden über verschlüsselte Kanäle
(TLS/HTTPS) übertragen und sind durch die rollenbasierte Zugriffskontrolle (RBAC) der Observability-Plattform geschützt,
um Manipulationssicherheit zu gewährleisten. Die Plattform bietet APIs für Benutzerprofile, Konversations-Threads und
Audit-Logs, um Auskunftsrechten nachzukommen und eine lückenlose Beweiskette für alle KI-Interaktionen bereitzustellen.

## 3. Umfassende Observability und Integration in bestehende Monitoring-Systeme

### Mehrwert und Nutzen: Proaktive Problemerkennung und zentrale Verwaltung

Der produktive Betrieb von KI-Systemen erfordert mehr als nur Funktionsfähigkeit; er verlangt Transparenz,
Zuverlässigkeit und Vorhersehbarkeit. Der Swiss AI Hub bietet eine umfassende, integrierte Observability Suite, die ein
vollständiges Bild der Gesundheit, Leistung und Kosten der Plattform liefert. Dies ermöglicht IT-Teams, Probleme
proaktiv zu erkennen und zu beheben, bevor sie Benutzer beeinträchtigen, Leistungsengpässe präzise zu identifizieren und
die Ressourcennutzung effizient zu planen. Die nahtlose Integration in bestehende zentrale Monitoring- und
SIEM-Landschaften reduziert den administrativen Aufwand und sichert die langfristige forensische Auswertbarkeit und
Qualitätssicherung.

### Konzepte & Prozesse: Die Säulen der Observability und offene Standards

Die Überwachungsphilosophie der Plattform basiert auf den branchenüblichen Säulen der Observability:

- **Health Checks**: Der Herzschlag der Plattform überprüft kontinuierlich, ob jede Komponente aktiv und funktionsfähig
  ist (native Docker Checks, Application Endpoint Checks, Synthetic Probes).
- **Metriken**: Quantitative Messungen verfolgen Leistung und Ressourcennutzung über die Zeit (Infrastruktur- und
  Anwendungsmetriken).
- **Logs**: Detaillierte, chronologische Aufzeichnungen jedes Ereignisses liefern Kontext für die Ursachenanalyse
  (Anwendungs-, Container-, Request-, Security Logs).

Alle Daten werden zentralisiert, strukturiert und durchsuchbar gemacht. Die Plattform setzt auf **OpenTelemetry (OTel)**
als herstellerneutralen, branchenüblichen Standard für das Sammeln, Verarbeiten und Exportieren von Telemetriedaten
(Metriken, Logs, Traces). Diese architektonische Entscheidung bietet maximale Flexibilität, da sie Vendor Lock-in
vermeidet, Metriken, Logs und Traces konsistent miteinander verknüpft und die Plattform zukunftssicher macht, indem sie
von der kontinuierlichen Innovation der Observability-Community profitiert. Dashboards und flexible
Alarmierungsfunktionen ermöglichen eine schnelle Visualisierung und proaktive Benachrichtigung bei kritischen
Ereignissen.

### Technische Umsetzung im Swiss AI Hub: OTel Collector und SigNoz Integration

Das gesamte Überwachungs- und Alarmierungssystem des Swiss AI Hub basiert auf **OpenTelemetry**. Ein zentraler
**OpenTelemetry Collector** empfängt Daten von allen Diensten, reichert sie mit Metadaten an und exportiert sie sicher
an die gewählten Ziele. Dieser Collector verwendet verschiedene Receiver (OTLP, `docker_stats`, `filelog`), Prozessoren
(Batching, Ressourcen-Erkennung, Attribut-Bearbeitung, Filterung) und Exporter. Die automatische Instrumentierung
umfasst NATS Messaging, Datenbankoperationen (FerretDB, ValKey, Milvus), HTTP-Aufrufe, LLM-Interaktionen, Embeddings und
Retrieval-Operationen, ohne Codeänderungen zu erfordern. Die `AihubInstrumentor`-Komponente konfiguriert diese
umfassende automatische Instrumentierung.

Als offiziell unterstütztes Observability-Backend dient **SigNoz**, eine Open-Source-, OpenTelemetry-native Plattform,
die vereinheitlichte Logs, Metriken und Traces in einer Oberfläche bereitstellt. SigNoz bietet Dashboards für
Infrastruktur, KI-Operationen (Modellnutzung, Token-Verbrauch, Kosten pro Operation), Anwendungsleistung und
Log-Analyse. Alarme können für kritische Dienstausfälle, Leistungsverschlechterung, Ressourcenlimits, Kostenmanagement
und Sicherheitsereignisse konfiguriert und an Kanäle wie E-Mail, Slack oder Microsoft Teams weitergeleitet werden. Für
Produktionsbereitstellungen wird die Selbst-Hinterlegung von SigNoz auf einer dedizierten VM dringend empfohlen, um
Leistungsisolation, hohe Verfügbarkeit, Datenhoheit und Netzwerksicherheit zu gewährleisten. Durch die OTel-Grundlage
können Telemetriedaten auch an alternative OTLP-kompatible Backends wie Grafana, Datadog, Splunk, Prometheus,
Elasticsearch/ELK oder New Relic exportiert werden, indem lediglich die Collector-Konfiguration angepasst wird.

## 4. Menschliche Kontrolle und Kostenmanagement: Absicherung und Effizienz in der Produktion

### Mehrwert und Nutzen: Absicherung kritischer Entscheidungen und volle Kostentransparenz

Nicht jede KI-Entscheidung kann vollständig automatisiert werden, insbesondere in sensiblen oder kritischen
Geschäftsprozessen. Die Plattform ermöglicht die nahtlose Integration menschlicher Kontrolle, um die Verantwortung zu
sichern und Compliance bei Prozessen zu gewährleisten, die menschliches Urteilsvermögen erfordern. Gleichzeitig ist das
Management der Betriebskosten von KI-Systemen für Organisationen von grosser Bedeutung. Der Swiss AI Hub bietet
detaillierte Funktionen zur Kostentransparenz, um Ausgaben zu optimieren, Investitionen zu rechtfertigen und Budgets
präzise zu prognostizieren, was eine verursachergerechte Verrechnung auf Abteilungs- oder Projektebene ermöglicht.

### Konzepte & Prozesse: Human-in-the-Loop und Token-basierte Kostenmodelle

Für kritische Entscheidungsprozesse sind **Human-in-the-Loop (HITL)**-Workflows vorgesehen. Ein Agent kann seinen
Workflow pausieren und auf menschliche Eingaben, Genehmigungen oder Korrekturen warten. Dies ist weit mehr als eine
einfache Eingabeaufforderung: Der Workflow wird am exakten Punkt der Pause mit vollem Gedächtnis aller
Zwischenergebnisse und Schritte fortgesetzt. Jede menschliche Interaktion – die gestellte Frage, die Antwort, die
Entscheidung – wird revisionssicher als Ereignis protokolliert, was eine vollständige Verantwortlichkeit für Compliance
und Auditing gewährleistet. Dies umfasst auch Eskalationsmechanismen bei problematischen KI-Outputs oder die Integration
von Nutzer-Feedback zur Qualitätsverbesserung.

Die Kosten von KI-Operationen werden primär durch die **Token-Nutzung** bestimmt. Tokens sind kleine Textabschnitte, die
Modelle verarbeiten, und verursachen Kosten für Prompt-Tokens (Ihre Eingabe), Completion-Tokens (KI-Antworten) und
Embedding-Tokens (Dokumentenverarbeitung). Die Wahl des LLM-Modells, das in Stufen wie "Flaggschiff", "Ausgewogen" oder
"Effizient" kategorisiert wird, beeinflusst ebenfalls die Kosten erheblich. Der Swiss AI Hub verfolgt diese Kosten für
jede Konversation, unabhängig vom LLM-Anbieter (Cloud oder selbst gehostet). Dies ermöglicht eine granulare Analyse,
welche Agenten, Workflows oder sogar einzelne Abfragen die höchsten Kosten verursachen.

### Technische Umsetzung im Swiss AI Hub: HITL Events und `LLMCostEvent`

Das **Human-in-the-Loop**-Muster wird durch das Swiss AI Agent Protokoll über spezielle Events orchestriert: Ein Schritt
im Agenten-Workflow gibt ein `HumanInTheLoopRequestEvent` zurück, das den Workflow pausiert und eine Aufgabe in der
Benutzeroberfläche erstellt. Die Antwort des Benutzers löst ein `HumanInTheLoopResponseEvent` aus, welches den Workflow
fortsetzt. Diese Ereignisse tragen den vollen Kontext und gewährleisten die lückenlose Dokumentation menschlicher
Eingriffe und Overrides.

Für die Kostenkontrolle erfasst die Plattform automatisch die Token-Nutzung und berechnet die Kosten für jede
LLM-Interaktion. Der `cost_reporting_llm()` Context Manager umhüllt das LLM in Agenten-Workflows, um die Token-Nutzung
und die Veröffentlichung von `LLMCostEvent`s zu automatisieren, sobald der Kontext verlassen wird. Diese `LLMCostEvent`s
sind `Display Events` und enthalten Details zu Token-Anzahl und zugehörigen Ausgaben. Diese Informationen werden im
Konversationsverlauf angezeigt und ermöglichen es Administratoren, Ausgaben auf Agenten-, Benutzer- oder Thread-Ebene zu
verfolgen. Die Plattform unterstützt zudem über LiteLLM pro-Benutzer-Budget- und Ratenbegrenzungsfunktionen wie maximale
Budgets, Soft Budgets, Budgetdauer, Tokens pro Minute (TPM) und Anfragen pro Minute (RPM) sowie maximale parallele
Anfragen. Diese Funktionen sind über Umgebungsvariablen konfigurierbar und werden automatisch durch den Proxy
durchgesetzt, sind jedoch standardmässig nicht aktiviert. Dies ermöglicht eine detaillierte Nachverfolgung, um teure
Queries zu identifizieren und die Modellauswahl für Kostenoptimierungen anzupassen.
