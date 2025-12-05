# Plattform-Transparenz und Prüfbarkeit

## Vom «Black Box»-Mythos zur auditierbaren Gewissheit

Der Einsatz generativer KI in Unternehmen wird oft von einer fundamentalen Sorge begleitet: der Unsicherheit gegenüber
der sogenannten «Black Box». In vielen kommerziellen KI-Produkten geben Benutzer einen Prompt ein und erhalten eine
Antwort, ohne jeglichen Einblick in die dahinterliegenden Entscheidungsprozesse oder die verwendeten Datenquellen. Für
ein experimentelles Startup mag dies akzeptabel sein, doch für Schweizer Finanzinstitute, Versicherungen oder die
öffentliche Verwaltung stellt dieser Mangel an Transparenz ein inakzeptables Risiko dar. Wenn eine KI eine
Kreditentscheidung vorbereitet oder patientenbezogene Daten zusammenfasst, muss der Weg zur Antwort ebenso klar belegbar
sein wie das Ergebnis selbst.

Der Swiss AI Hub begegnet dieser Herausforderung mit einem Architekturansatz der radikalen Transparenz. Die Plattform
behandelt KI nicht als undurchsichtiges Orakel, sondern als eine Abfolge deterministischer, technischer Prozessschritte.
Durch die Implementierung von «Deep Observability» wird jeder Denkschritt, jeder Datenbankzugriff und jede externe
API-Interaktion protokolliert. Dies verwandelt die Black Box in ein «Glass Box»-System, das Auditoren,
Compliance-Beauftragten und IT-Administratoren jederzeit Rede und Antwort stehen kann.

## Nachvollziehbarkeit durch das Swiss AI Agent Protokoll

### Deterministische Abläufe statt chaotischer Autonomie

In geschäftskritischen Szenarien reicht ein korrektes Ergebnis allein oft nicht aus; die Herleitung muss validierbar
sein. Führungskräfte müssen verstehen, warum ein Agent eine bestimmte Empfehlung ausgesprochen hat oder warum eine
Anfrage abgelehnt wurde. Fehlt diese Erklärbarkeit (Explainability), sinkt das Vertrauen der Nutzer, und die
Fehleranalyse bei inkorrekten Antworten («Halluzinationen») wird unmöglich. Ein System, das seine interne Logik
verbirgt, entzieht sich der effektiven Steuerung.

### Trennung von Steuerung und Beobachtung

Der Swiss AI Hub löst dieses Problem durch das zugrundeliegende **Swiss AI Agent Protokoll**. Dieses Protokoll definiert
eine strikte Ereignisarchitektur, die sicherstellt, dass die Beobachtung eines Agenten dessen Arbeitsweise niemals
beeinflusst. Anders als monolithische Chatbots, die lediglich Text generieren, emittieren Agenten auf der Plattform
während ihrer Arbeit kontinuierlich strukturierte Ereignisse.

Technisch unterscheidet das Protokoll strikt zwischen zwei Ereignistypen:

1. **Control Events (Steuerung):** Diese Ereignisse treiben den Workflow voran und ändern den Zustand des Systems (z.B.
   `StartEvent`, `StopEvent` oder Datenbankabfragen). Sie sind die technische «Wahrheit» des Prozessablaufs.
2. **Display Events (Beobachtung):** Diese Ereignisse dienen rein der Information für den Benutzer oder Auditor (z.B.
   `ThoughtEvent` oder `ChunkEvent`). Sie legen die internen Überlegungen («Reasoning») des Sprachmodells offen, ohne
   den technischen Ablauf zu verändern.

Diese Trennung ermöglicht es einem Auditor oder Administrator, exakt nachzuvollziehen, wie der Agent eine
Benutzeranfrage interpretiert hat («Thought Process»), welche Zwischenschritte er geplant hat und warum er sich für eine
bestimmte Aktion entschied.

### Hierarchische Kontext-Sicherheit

Die Nachvollziehbarkeit wird durch eine dreistufige Hierarchie im Protokoll strukturiert, die auch das Sicherheitsmodell
definiert. Ein `Thread` bündelt langfristige Konversationen oder Prozesse und regelt die Zugriffskontrolle – nur wer
Zugriff auf den Thread hat, darf die Daten sehen. Darunter gruppiert der `Display`-Kontext zusammengehörige
Interaktionen für die Benutzeroberfläche, während der `Run`-Kontext die technische Ausführung eines einzelnen Workflows
kapselt. Diese Granularität stellt sicher, dass selbst bei komplexen Multi-Agenten-Systemen jede einzelne Aktion
zweifelsfrei einem Auslöser und einem Kontext zugeordnet werden kann.

## Lückenlose Auditierung mit OpenTelemetry

### Der Anspruch an Revisionssicherheit

Regulatorische Vorgaben (wie FINMA-Rundschreiben oder DSG) verlangen oft den Nachweis, wer wann auf welche Daten
zugegriffen hat. In einer verteilten KI-Architektur ist dies komplex, da eine einzelne Benutzeranfrage Dutzende von
internen Service-Aufrufen auslösen kann. Herkömmliche Logging-Ansätze scheitern hier oft, da sie die Zusammenhänge
zwischen diesen isolierten Ereignissen verlieren. Ohne eine durchgängige Verbindung («Correlation») zwischen der Eingabe
eines Nutzers und der Datenbankabfrage im Backend bleibt die Beweiskette lückenhaft.

### Standardisierung und Dual-Backend-Strategie

Um eine lückenlose Beweiskette zu garantieren, setzt der Swiss AI Hub konsequent auf den Industriestandard
**OpenTelemetry (OTel)**. Anstatt proprietäre Log-Formate zu erfinden, die einen Vendor Lock-in erzeugen, instrumentiert
die Plattform sämtliche Komponenten – vom API-Gateway über den `AgentRunTracer` bis hin zu Datenbank-Clients und
LLM-Aufrufen via `LlamaIndexInstrumentor`.

Jede Interaktion erhält beim Eintritt in das System eine eindeutige Trace-ID. Der zentrale **OpenTelemetry Collector**
fungiert dabei als intelligente Drehscheibe, die Telemetriedaten über zwei spezialisierte Pipelines verarbeitet:

1. **Operatives Monitoring (traces/cloud):** Technische Metriken und Logs werden an Systeme wie **SigNoz** oder
   bestehende Unternehmens-SIEMs (z.B. Splunk, Datadog) geleitet. Hier überwacht der IT-Betrieb Latenzen, Fehlerraten
   und Systemressourcen («Ist das System gesund?»).
2. **LLM-Observability (traces/phoenix):** KI-spezifische Daten – inklusive Prompts, Token-Nutzung und RAG-Retrievals –
   werden parallel an spezialisierte Tools wie **Phoenix** gesendet. Dies ermöglicht KI-Entwicklern und
   Fachverantwortlichen eine tiefe Inspektion der KI-Logik («Warum hat das Modell so geantwortet?»).

Diese Dual-Strategie stellt sicher, dass sowohl operative Stabilität als auch inhaltliche Qualität überwacht werden,
ohne dass sensible KI-Inhalte zwingend mit allgemeinen Infrastruktur-Logs vermischt werden.

## Datenherkunft und Quellen-Transparenz (Data Lineage)

### Validierung der Informationsbasis

Eine der grössten Herausforderungen bei Retrieval-Augmented Generation (RAG) Systemen ist die Quellenprüfung. Wenn ein
Agent behauptet: «Gemäss der HR-Richtlinie haben Sie Anspruch auf 25 Tage Urlaub», muss verifizierbar sein, auf welchem
Dokument diese Aussage beruht. In intransparenten Systemen bleibt unklar, ob die KI diese Information tatsächlich in den
Unternehmensdaten gefunden oder halluziniert hat.

### Granulare Nachverfolgung der Dokumenten-Chunks

Der Swiss AI Hub implementiert eine präzise Nachverfolgung der Datenherkunft (Data Lineage). Wenn ein Agent eine
Wissensdatenbank konsultiert, wird dies durch ein `RetrieveEvent` protokolliert. Dieses Ereignis speichert nicht nur die
Tatsache des Zugriffs, sondern die exakten Metadaten der abgerufenen Informationen:

1. **Dokumenten-ID:** Welches spezifische PDF oder Word-Dokument wurde verwendet?
2. **Versionierung:** War es die aktuelle Richtlinie oder eine veraltete Version aus der Sammlung?
3. **Chunk-Referenz:** Welcher Textabschnitt (Paragraph) innerhalb des Dokuments diente als Grundlage?

Diese Informationen werden direkt mit der Antwort verknüpft. Im Audit-Trail ist somit ersichtlich, dass die Antwort auf
Benutzerfrage X zu 80% auf Abschnitt Y des Dokuments Z basiert. Diese Transparenz ist entscheidend für die
Qualitätssicherung und ermöglicht es Fachabteilungen, fehlerhafte Antworten auf unklare Formulierungen in den
Quelldokumenten der Daten-zu-Wissen-Pipeline zurückzuführen, anstatt pauschal der «Technik» die Schuld zu geben.

## Menschliche Kontrolle im Loop (Human-in-the-Loop)

### Das 4-Augen-Prinzip für KI

Trotz aller Automatisierung gibt es Entscheidungen, die nicht allein einer KI überlassen werden dürfen – sei es die
Freigabe einer Pressemitteilung oder die Genehmigung einer Transaktion. Ein rein technisches System ohne menschliche
Interventionsmöglichkeit stellt in solchen Fällen ein Compliance-Risiko dar. Es muss möglich sein, den automatisierten
Prozess anzuhalten und eine menschliche Bestätigung einzufordern, ohne den digitalen Audit-Pfad zu unterbrechen.

### Protokollierte Interventionen

Die Plattform integriert hierfür das **Human-in-the-Loop (HITL)** Muster tief in die Protokollebene. Ein Agent kann so
konfiguriert werden, dass er an kritischen Punkten ein `HumanInTheLoopRequestEvent` auslöst. Der Workflow wird in diesem
Moment technisch pausiert ("suspendiert"), und der gesamte Kontext des bisherigen Verlaufs wird sicher gespeichert
(State Persistence).

Das System wartet nun auf eine explizite Interaktion eines berechtigten Benutzers. Sobald dieser die Aktion genehmigt
oder ablehnt, wird ein `HumanInTheLoopResponseEvent` generiert. Entscheidend ist hierbei die Nachvollziehbarkeit: Das
Audit-Log verzeichnet nicht nur die Entscheidung der KI, sondern auch die Identität des genehmigenden Mitarbeiters und
den exakten Zeitstempel der Freigabe. Damit wird die hybride Zusammenarbeit von Mensch und Maschine revisionssicher
dokumentiert. Sollte es später zu Rückfragen kommen, ist beweisbar, dass die kritische Entscheidung letztlich durch
einen Menschen autorisiert wurde.

## Proaktive Qualitätssicherung: Testen vor dem Betrieb

Transparenz bedeutet nicht nur, Fehler im Nachhinein zu finden, sondern sie proaktiv zu vermeiden. Während herkömmliche
Chatbots oft manuell getestet werden ("Trial and Error"), ermöglicht der Swiss AI Hub durch das
**AgentTestRunner**-Framework eine automatisierte Qualitätssicherung.

Entwickler und QA-Teams können Szenarien in natürlicher Sprache definieren (Behavior-Driven Development), die
beschreiben, wie sich ein Agent verhalten soll. Diese Tests werden automatisch ausgeführt, wobei der `AgentTestRunner`
eine Sandbox-Umgebung bereitstellt. So lässt sich vor jedem Deployment verifizieren, dass ein Agent Compliance-Regeln
einhält, Iterations-Limits respektiert und in definierten Szenarien die korrekten Ereignisse auslöst. Dies verschiebt
die "Prüfbarkeit" vom reaktiven Audit hin zur präventiven Qualitätssicherung.

## Finanzielle Transparenz und FinOps

### Kostenkontrolle statt Blindflug

In vielen Organisationen werden KI-Kosten als Gemeinkosten betrachtet, die schwer zuzuordnen sind. Da LLM-Anbieter pro
Token (Wortteil) abrechnen, kann die intensive Nutzung durch eine einzelne Abteilung das IT-Budget unverhältnismässig
belasten. Ohne detaillierte Einsicht ist es unmöglich, Verursacher hoher Kosten zu identifizieren oder den ROI (Return
on Investment) von KI-Projekten zu berechnen.

### Verursachergerechte Abrechnung und Budgetierung

Der Swiss AI Hub nutzt seine tiefe Instrumentierung auch für finanzielle Transparenz (FinOps). Da jeder Aufruf an ein
Sprachmodell durch das zentrale LLM-Gateway und die Tracing-Infrastruktur läuft, werden Metriken zur Token-Nutzung
(Prompt- und Completion-Tokens) automatisch erfasst und über `LLMCostEvent` mit dem Benutzerkontext angereichert.

Über Dashboards oder exportierte Daten lässt sich exakt aufschlüsseln, welche Kosten ein spezifischer Benutzer, ein Team
oder ein bestimmter Agent im Zeitverlauf verursacht hat. Zusätzlich ermöglicht der integrierte Proxy die Durchsetzung
harter Budgetgrenzen über Umgebungsvariablen, um Kostensicherheit zu garantieren:

- **Hard Limits:** Festlegung eines maximalen Budgets pro User (z.B. via `LITE_LLM_PROXY_USER_MAX_BUDGET`), bei dessen
  Überschreitung Anfragen blockiert werden.
- **Soft Limits:** Konfiguration von Warnschwellen (`LITE_LLM_PROXY_USER_SOFT_BUDGET`), um Administratoren proaktiv zu
  benachrichtigen, bevor Kosten aus dem Ruder laufen.
- **Rate Limiting:** Technische Begrenzung von Anfragen pro Minute (RPM) oder Tokens pro Minute (TPM) zur Verhinderung
  von Missbrauch oder versehentlichen Endlosschleifen.

Diese Kostentransparenz verwandelt KI von einem unvorhersehbaren Kostenrisiko in eine planbare und steuerbare Ressource.
Unternehmen behalten die wirtschaftliche Kontrolle und können Investitionen gezielt dort tätigen, wo sie nachweisbaren
Mehrwert schaffen.
