# Kapitel 04: Plattform-Transparenz und Prüfbarkeit

Eine der grössten Hürden für den produktiven Einsatz generativer KI in Schweizer Unternehmen ist das
«Black-Box»-Problem. Wenn ein KI-Modell eine Entscheidung trifft, eine Empfehlung ausspricht oder einen Text generiert,
bleibt oft unklar, wie dieses Ergebnis zustande kam. Für regulierte Branchen, die öffentliche Verwaltung und
sicherheitsbewusste Unternehmen ist dieser Zustand inakzeptabel. Compliance-Vorgaben, interne Revisionsrichtlinien und
das revidierte Datenschutzgesetz (revDSG) verlangen lückenlose Nachvollziehbarkeit.

Der Swiss AI Hub begegnet dieser Herausforderung mit einem fundamentalen Architekturprinzip: Radikale Transparenz durch
einen «White-Box»-Ansatz. Dieses Kapitel beschreibt, wie die Plattform technische Abläufe, Datenflüsse und
Entscheidungsketten nicht nur ausführt, sondern lückenlos und auditierbar dokumentiert, um Vertrauen durch technische
Beweisbarkeit zu ersetzen.

## Auf einen Blick

- **Lückenlose Kausalkette:** Durch das Swiss AI Agent Protokoll wird jeder logische Schritt eines Agenten als
  unveränderliches Ereignis dokumentiert, wodurch Entscheidungen deterministisch nachvollziehbar werden.
- **Beweisbare Datenherkunft:** Data Lineage verknüpft jede KI-Antwort direkt mit den verwendeten Quell-Dokumenten
  (Chunks), um Halluzinationen auditierbar auszuschliessen.
- **Dual-Pipeline Observability:** Eine innovative Architektur trennt Entwickler-Tracing (Phoenix) von operativem
  Monitoring (SigNoz), um sowohl tiefe KI-Inspektion als auch stabilen Betrieb zu gewährleisten.
- **Vendor-Neutralität:** Dank OpenTelemetry-Standard können Audit-Daten ohne Anpassung in bestehende SIEM-Systeme wie
  Datadog, Splunk oder Dynatrace exportiert werden.
- **Integrierte Finanzkontrolle:** Das LLM-Gateway erzwingt Budgets und Ratenlimits technisch, um Kostenexplosionen
  proaktiv zu verhindern.

## Nachvollziehbarkeit von KI-Entscheidungen

### Geschäftlicher Nutzen

In kritischen Geschäftsprozessen reicht ein korrektes Ergebnis allein nicht aus; der Weg dorthin muss erklärbar sein
(«Explainability»). Wenn ein Agent einen Kreditantrag ablehnt oder eine medizinische Empfehlung zusammenfasst, müssen
Fachabteilungen und Auditoren verstehen, welche logischen Schritte durchlaufen wurden. Mangelnde Erklärbarkeit ist ein
massives Haftungsrisiko. Der Swiss AI Hub eliminiert dieses Risiko, indem er die internen Denkprozesse der KI sichtbar
macht. Dies schafft Vertrauen bei den Anwendern und ermöglicht es Compliance-Beauftragten, die Einhaltung von
Richtlinien zu verifizieren, ohne sich auf das Wort der KI verlassen zu müssen.

### Konzeptioneller Ansatz

Die Lösung verabschiedet sich vom Konzept monolithischer, undurchsichtiger Chatbots. Stattdessen setzt die Plattform auf
Workflow-basierte Agenten. Ein Agent folgt keinem Zufallspfad, sondern einem definierten Agenten-Bauplan, der in
einzelne, diskrete Schritte unterteilt ist. Jeder dieser Schritte – sei es das Analysieren einer Eingabe, das Suchen von
Informationen oder das Formulieren einer Antwort – erzeugt ein unveränderliches Ereignis. Die Summe dieser Ereignisse
bildet einen lückenlosen Pfad, der exakt aufzeigt, was der Agent zu welchem Zeitpunkt «gedacht» und getan hat. Durch
eine hierarchische Kontext-Struktur (Thread, Display, Run) lassen sich dabei komplexe, langlaufende Prozesse logisch
gruppieren und bis auf die einzelne Ausführung hinunterbrechen.

### Technische Umsetzung im Swiss AI Hub

Technisch basiert diese Transparenz auf dem **Swiss AI Agent Protokoll**. Dieses interne Kommunikationsmodell definiert
eine strikte Trennung zwischen Steuerungs- und Anzeigeinformationen mittels typisierter Events, die über NATS publiziert
werden:

- **Control Events:** Diese Ereignisse (z.B. `CondenseQuestionEvent`, `RetrieveEvent`) steuern die Geschäftslogik. Sie
  sind die «Befehle», die den Workflow vorantreiben und dokumentieren jeden Zustandsübergang im Backend. Sie machen den
  internen Entscheidungspfad sichtbar, auch wenn dieser dem Endnutzer in der Benutzeroberfläche verborgen bleibt.
- **Display Events:** Diese Ereignisse (z.B. `ThoughtEvent`, `ChunkEvent`) dienen der reinen Information («Kommentar»)
  und Kommunikation mit dem Benutzer. Sie zeigen beispielsweise Zwischenergebnisse oder «Gedanken» des Agenten an,
  dürfen aber niemals den logischen Fluss des Workflows beeinflussen.

Jedes Ereignis ist in einer dreistufigen Hierarchie verankert: Der **Thread-Kontext** hält den langfristen Status einer
Konversation, der **Display-Kontext** gruppiert zusammengehörige UI-Interaktionen (auch über mehrere Agenten hinweg),
und der **Run-Kontext** isoliert die technische Ausführung eines einzelnen Workflow-Durchlaufs. Dies ermöglicht eine
forensische Analyse bis auf die Millisekunde genau.

## Revisionssichere Datenherkunft (Data Lineage)

### Geschäftlicher Nutzen

Bei der Nutzung von Retrieval-Augmented Generation (RAG) ist die häufigste Frage von Auditoren: «Woher stammt diese
Information genau?» Halluzinationen – das Erfinden von Fakten durch die KI – stellen ein signifikantes Qualitätsrisiko
dar. Unternehmen müssen sicherstellen, dass Antworten ausschliesslich auf validierten Unternehmensdaten basieren und
nicht auf dem allgemeinen Trainingswissen des Modells. Für rechtliche Prüfungen ist es unerlässlich beweisen zu können,
welches spezifische Dokument in welcher Version zu einem bestimmten Zeitpunkt als Grundlage für eine Auskunft diente.

### Konzeptioneller Ansatz

Das Konzept der Datenherkunft (Data Lineage) wird im Swiss AI Hub durch eine strikte Referenzierung und semantische
Konventionen umgesetzt. Eine generierte Antwort steht niemals für sich allein. Sie ist untrennbar mit den Quellen
verknüpft, die zu ihrer Erstellung herangezogen wurden. Das System protokolliert nicht nur, *dass* gesucht wurde,
sondern exakt *was* gefunden wurde (inklusive Relevanz-Scores). Dies ermöglicht eine Rekonstruktion der
Informationsbasis: Auditoren können sehen, welche Wissensschnipsel dem Modell zur Verfügung standen und ob veraltete
oder nicht freigegebene Dokumente fälschlicherweise berücksichtigt wurden.

### Technische Umsetzung im Swiss AI Hub

In der technischen Implementierung nutzt die Plattform **OpenInference Semantic Conventions**, um KI-spezifische
Operationen standardisiert zu erfassen. RAG-Operationen erzeugen spezialisierte **Retriever-Spans** innerhalb des
Tracing-Systems:

- **Quellennachweis:** Sobald ein Agent die Wissensdatenbank abfragt, wird ein `RetrieverEvent` generiert. Dieses
  enthält die IDs der abgerufenen Dokumenten-Chunks («Nodes») sowie deren Ähnlichkeits-Scores.
- **Attributierung:** Die Plattform verknüpft die Antwort (Output) semantisch mit den abgerufenen Kontextdaten. In der
  Tracing-Oberfläche (Phoenix) wird sichtbar, welche Textpassagen an das LLM übergeben wurden.
- **Embedding-Transparenz:** Auch der Schritt der Vektorisierung wird getraced, um sicherzustellen, dass die semantische
  Suche technisch korrekt funktioniert hat. Dies garantiert, dass die «Grounding»-Qualität – also die Verankerung der
  Antwort in Fakten – jederzeit messbar und beweisbar ist.

## Deep Observability und Integration in Enterprise-Monitoring

### Geschäftlicher Nutzen

Eine KI-Plattform darf keine isolierte Insel («Black Box») in der IT-Landschaft sein. Betriebsteams benötigen eine
zentrale Sicht auf die Gesundheit aller Systeme, um Ausfälle proaktiv zu verhindern. Proprietäre Monitoring-Tools von
KI-Herstellern führen oft zu Datensilos und erschweren die Fehleranalyse («Root Cause Analysis»). CIOs fordern daher
Lösungen, die sich nahtlos in bestehende SIEM- und Monitoring-Landschaften integrieren lassen, um die Hoheit über die
operativen Daten zu behalten und langfristige Trendanalysen ohne Vendor-Lock-in zu ermöglichen.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine Strategie der maximalen Interoperabilität durch offene Standards. Die Plattform setzt
konsequent auf **OpenTelemetry (OTel)** als universelle Sprache für Telemetriedaten. Dieser Industriestandard stellt
sicher, dass Metriken (Zahlen), Logs (Text) und Traces (Abläufe) einheitlich erfasst und korreliert werden. Der Kunde
entscheidet selbst, wohin diese Daten fliessen – sei es in eine lokale Analyseinstanz oder in unternehmensweite
Dashboards.

### Technische Umsetzung im Swiss AI Hub

Das Herzstück der Observability-Architektur ist der zentrale **OpenTelemetry Collector**. Er fungiert als
Datendrehscheibe, die Telemetrie aus Containern, Datenbanken und Agenten sammelt und über zwei spezialisierte Pipelines
routet:

- **Pipeline `traces/phoenix` (KI-Analyse):** Diese Pipeline filtert KI-spezifische Traces und sendet sie an
  **Phoenix**. Phoenix ist ein spezialisiertes Tool für LLM-Observability, das Entwicklern erlaubt, Prompt-Templates,
  Retrieval-Qualität und Token-Nutzung im Detail zu debuggen.
- **Pipeline `traces/cloud` (Operations):** Diese Pipeline bereinigt die Daten von Rauschen (z.B. Health Checks) und
  sendet operative Metriken an ein Langzeit-Backend. Standardmässig wird **SigNoz** unterstützt, aber durch reine
  Konfigurationsänderung kann der Export auf jedes OTLP-kompatible System wie Datadog, Splunk, Dynatrace oder Grafana
  umgestellt werden.

Diese Dual-Backend-Strategie ermöglicht es, Entwicklern tiefe Einblicke zu geben, ohne das operative Monitoring-System
der IT-Abteilung mit Debugging-Daten zu überfluten.

## Menschliche Kontrolle (Human-in-the-Loop)

### Geschäftlicher Nutzen

Trotz fortschrittlicher Modelle gibt es Entscheidungen, die nicht vollständig automatisiert werden dürfen – sei es aus
ethischen Gründen, wegen hohem finanziellem Risiko oder aufgrund regulatorischer Vorschriften (z.B. Art. 22 DSGVO).
Unternehmen benötigen einen Mechanismus, der die Effizienz der KI nutzt, aber die Letztentscheidung beim Menschen
belässt. Ein «Human-in-the-Loop»-Prozess verhindert, dass automatisierte Systeme aus dem Ruder laufen, und stellt
sicher, dass kritische Aktionen (z.B. das Versenden einer Vertragsänderung) explizit freigegeben werden.

### Konzeptioneller Ansatz

Das System integriert den Menschen als aktive Komponente in den Workflow. Ein Agenten-Prozess ist nicht zwingend eine
durchlaufende Kette von Maschinenbefehlen. Er kann an definierten Punkten pausieren und den Zustand «einfrieren». Erst
wenn eine autorisierte menschliche Interaktion erfolgt – eine Bestätigung, eine Korrektur oder eine Ablehnung – wird der
Prozess fortgesetzt. Wichtig ist dabei die lückenlose Dokumentation: Auch der menschliche Eingriff wird als Ereignis im
Audit-Trail festgehalten, sodass später klar ersichtlich ist, wer die Entscheidung getroffen hat.

### Technische Umsetzung im Swiss AI Hub

Die Umsetzung erfolgt über asynchrone Ereignismuster im Swiss AI Agent Protokoll, die persistente Zustände unterstützen:

- **Unterbrechung:** Ein Agent sendet ein `HumanInTheLoopRequestEvent`. Der Workflow stoppt, und der gesamte Kontext
  (Variablen, bisherige Ergebnisse) wird sicher im Redis-basierten Run-Kontext persistiert.
- **Interaktion:** Das System generiert eine Aufgabe für den Benutzer. Der Prozess kann Minuten oder Tage in diesem
  Wartezustand verbleiben, ohne Rechenressourcen zu blockieren.
- **Wiederaufnahme:** Sobald der Benutzer reagiert, wird ein `HumanInTheLoopResponseEvent` in den Event Bus gespeist.
  Der Agent wird rehydriert – also in seinen vorherigen Zustand versetzt – und setzt die Arbeit mit den menschlichen
  Eingaben fort. Diese Architektur ermöglicht komplexe Genehmigungsketten, ohne dass Entwickler eigene Statusmaschinen
  bauen müssen.

## Finanzielle Transparenz und Kostenkontrolle

### Geschäftlicher Nutzen

Die Abrechnungsmodelle grosser Sprachmodelle (Pay-per-Token) bergen ein erhebliches Kostenrisiko. Eine fehlerhafte
Schleife in einem Agenten oder die exzessive Nutzung durch eine Abteilung kann Budgets innert kürzester Zeit sprengen.
CFOs benötigen daher nicht nur eine nachträgliche Rechnung, sondern Echtzeit-Transparenz und harte Limits («Circuit
Breakers»), um die Kosten pro Abteilung, Projekt oder Benutzer steuern zu können. Dies ist die Grundlage für eine
verursachergerechte interne Leistungsverrechnung (Chargeback).

### Konzeptioneller Ansatz

Kostenkontrolle ist im Swiss AI Hub keine nachgelagerte Analyse, sondern in den Kern des Routings integriert. Jede
Interaktion mit einem Modell wird vermessen, bewertet und einem Verursacher zugeordnet. Das System unterscheidet dabei
zwischen verschiedenen Kostenarten (Prompt- vs. Completion-Tokens). Durch die Definition von Budgets und Ratenlimits
(Rate Limiting) wird sichergestellt, dass die Ressourcennutzung innerhalb der definierten Leitplanken bleibt.

### Technische Umsetzung im Swiss AI Hub

Das **LLM-Gateway** (LiteLLM) agiert als zentraler Wächter über die Kosten und setzt Limits technisch durch:

- **Budget-Durchsetzung:** Administratoren können über Umgebungsvariablen harte Obergrenzen (z.B.
  `LITE_LLM_PROXY_USER_MAX_BUDGET`) und Warnschwellen (`SOFT_BUDGET`) definieren. Wird ein Limit erreicht, blockiert das
  Gateway weitere Anfragen automatisch.
- **Rate Limiting:** Um Missbrauch oder fehlerhafte Skripte zu stoppen, können Limits für Tokens pro Minute (TPM) oder
  Anfragen pro Minute (RPM) gesetzt werden.
- **Echtzeit-Tracking:** Jeder Aufruf erzeugt `LLMCostEvents`, die Token-Anzahlen und berechnete Kosten enthalten. Diese
  fliessen in die Monitoring-Dashboards und ermöglichen granulare Reports darüber, welche Anwendungsfälle den grössten
  Wert im Verhältnis zu den Kosten liefern.
