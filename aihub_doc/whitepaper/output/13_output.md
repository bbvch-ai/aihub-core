# Kapitel 13: AI-Agenten und Kernkonzepte

Während die vorangegangenen Kapitel die Infrastruktur, Sicherheit und Integration beleuchtet haben, widmet sich dieser
Abschnitt dem Herzstück der Wertschöpfung: den KI-Agenten selbst. In der öffentlichen Wahrnehmung werden Agenten oft mit
autonomen Chatbots gleichgesetzt, die frei improvisieren. Im Unternehmenskontext ist Improvisation jedoch ein Risiko.
Geschäftsprozesse verlangen nach Konsistenz, Nachvollziehbarkeit und Kontrolle.

Der Swiss AI Hub bricht mit dem Paradigma der undurchsichtigen «Black Box». Anstatt monolithische Modelle entscheiden zu
lassen, setzt die Plattform auf eine Architektur aus spezialisierten, workflow-basierten Komponenten. Dieses Kapitel
beschreibt, wie durch deterministische Baupläne, strikte Protokolle und menschliche Interventionsmöglichkeiten
(«Human-in-the-Loop») verlässliche KI-Systeme entstehen, die auch komplexen Anforderungen in regulierten Branchen
genügen.

## Auf einen Blick

- **Deterministische Workflows:** Agenten folgen fest definierten Pfaden (Closed Workflows) statt autonomer
  Improvisation, was das Verhalten vorhersagbar und auditierbar macht.
- **Transparenz durch Protokoll:** Das Swiss AI Agent Protokoll trennt strikt zwischen Steuerungslogik («Control
  Events») und Benutzerinformation («Display Events») für lückenlose Nachvollziehbarkeit.
- **Human-in-the-Loop:** Kritische Prozesse können asynchron pausieren, um eine menschliche Genehmigung einzuholen,
  bevor der Agent seine Arbeit fortsetzt.
- **Multi-Agenten-Orchestrierung:** Komplexe Aufgaben werden durch das «Agent-in-the-Loop»-Muster in spezialisierte
  Teilaufgaben zerlegt, die von dedizierten Worker-Agenten bearbeitet werden.
- **Aktive Qualitätssicherung:** Integrierte «Guardrails» validieren Eingaben und prüfen Antworten auf Faktenbasis
  (Context Sufficiency), um Halluzinationen technisch zu unterbinden.

## Deterministische Workflow-Steuerung statt «Black Box»

### Geschäftlicher Nutzen

Ein fundamentaler Hinderungsgrund für den KI-Einsatz in kritischen Bereichen ist die Unvorhersehbarkeit. Wenn ein
Sprachmodell halluziniert oder eine Entscheidung auf einer undurchsichtigen Basis trifft, entstehen Haftungsrisiken.
Unternehmen und Behörden benötigen die Gewissheit, dass ein Agent definierten Regeln folgt. Ein «Workflow-basierter
Agent» bietet diese Sicherheit. Er garantiert, dass Prozesse immer denselben validierten Pfaden folgen,
Audit-Anforderungen erfüllen und nicht vom vorgesehenen Skript abweichen. Dies verwandelt KI von einem unberechenbaren
Experiment in ein stabiles Werkzeug für die Prozessautomatisierung.

### Konzeptioneller Ansatz

Das Konzept unterscheidet strikt zwischen der «Intelligenz» des Sprachmodells und der «Steuerung» des Prozesses. Anstatt
dem Modell eine vage Anweisung zu geben und auf das Beste zu hoffen, wird der Agent in einen «Closed Workflow»
eingebettet. Dieser Workflow definiert eine Kette von Schritten, die deterministisch ausgeführt werden. Das Sprachmodell
wird dabei lediglich als kognitiver Motor innerhalb einzelner Schritte genutzt – etwa um Text zu analysieren oder zu
formulieren –, während die Entscheidungslogik über den nächsten Schritt (Verzweigungen, Schleifen, Abbruchbedingungen)
fest im Code verankert ist. Die Ausführung erfolgt ereignisgesteuert, wobei der Zustand zwischen Schritten sicher
verwaltet wird.

### Technische Umsetzung im Swiss AI Hub

Im Swiss AI Hub wird dieses Konzept durch die Trennung von **Agenten-Bauplan** und **Agenten-Profil** sowie den **Agent
Dispatcher** realisiert:

- **Agenten-Bauplan (Blueprint):** Dies ist der unveränderliche Python-Code, der die Logik und die Abfolge der Schritte
  (`@step`) definiert. Der Bauplan legt fest, wie Ereignisse verarbeitet werden und welche Aktionen (z.B.
  Datenbankabfrage, API-Call) erlaubt sind.
- **Agenten-Profil:** Dies ist die instanziierte Konfiguration eines Bauplans via `AgentConfig`. Ein Profil bestimmt,
  auf welche spezifischen Datenquellen oder Modelle der Agent zugreifen darf. So können auf demselben Bauplan basierend
  ein «HR-Agent» und ein «IT-Support-Agent» erstellt werden, die strikt getrennt operieren.
- **Agent Dispatcher:** Diese Komponente orchestriert die Ausführung zur Laufzeit. Der Dispatcher analysiert die
  Typ-Signaturen der Schritt-Methoden und injiziert automatisch notwendige Abhängigkeiten wie die Konfiguration
  (`StepConfig`) oder Kontext-Speicher (`RunContext`, `ThreadContext`). Dies stellt sicher, dass der Agent niemals
  ausserhalb der definierten Parameter agieren kann und jeder Schritt isoliert testbar ist.

## Transparenz durch das Swiss AI Agent Protokoll

### Geschäftlicher Nutzen

Um Vertrauen in automatisierte Systeme zu schaffen, muss jede Aktion erklärbar sein. Auditoren und
Compliance-Beauftragte müssen rekonstruieren können, warum ein Agent zu einem bestimmten Ergebnis kam. Proprietäre
Agenten-Frameworks verstecken diese internen Abläufe oft. Eine offene Standardisierung der Kommunikation ermöglicht
hingegen eine lückenlose Überwachung («Observability») und Fehleranalyse. Dies ist essenziell, um regulatorische
Anforderungen an die Erklärbarkeit von KI-Entscheidungen (z.B. im Rahmen des EU AI Acts) zu erfüllen, ohne sich in
proprietäre Abhängigkeiten zu begeben.

### Konzeptioneller Ansatz

Die Plattform nutzt für die interne Kommunikation das **Swiss AI Agent Protokoll**. Dieses ereignisgesteuerte Modell
definiert eine klare Sprache für alle Interaktionen innerhalb der Plattform. Es unterscheidet sich von Protokollen wie
dem «Model Context Protocol» (MCP), welches für die Anbindung externer Tools gedacht ist, indem es den Fokus auf die
interne Orchestrierung und Beobachtbarkeit legt. Kernprinzip ist die strikte Unterscheidung zwischen Steuerung und
Anzeige. Während Steuerungsereignisse den logischen Fluss vorantreiben (z.B. «Suche gestartet», «Entscheidung
getroffen»), dienen Anzeigeereignisse der Information des Nutzers (z.B. «Gedankenprotokoll», «Antwort-Stream»).

### Technische Umsetzung im Swiss AI Hub

Das Protokoll wird über einen zentralen Message Bus (NATS) abgewickelt und definiert präzise Ereignis-Typen und Scopes:

- **Control Events:** Diese Ereignisse (wie `RetrieveEvent` oder `StopEvent`) sind die einzigen Trigger, die einen
  Zustandsübergang im Workflow auslösen dürfen. Sie bilden den auditierbaren Pfad der Entscheidung.
- **Display Events:** Ereignisse wie `ThoughtEvent` oder `ChunkEvent` streamen Zwischenstände oder «Überlegungen» des
  Agenten an das Frontend, ohne den Prozessstatus zu ändern.
- **Hierarchische Scopes:** Jedes Ereignis ist in eine dreistufige Kontext-Hierarchie eingebettet, die im Topic kodiert
  ist:
  - **Thread-Kontext:** Hält den langfristigen Zustand einer Konversation (bis zu 30 Tage).
  - **Display-Kontext:** Gruppiert UI-Interaktionen, was besonders bei der Zusammenarbeit mehrerer Agenten wichtig ist,
    um dem Nutzer eine nahtlose Ansicht zu bieten.
  - **Run-Kontext:** Isoliert die technische Ausführung eines einzelnen Workflow-Durchlaufs für präzises Tracing.

## Spezialisierung und Multi-Agenten-Kollaboration

### Geschäftlicher Nutzen

Der Versuch, einen einzigen «Super-Agenten» für alle Unternehmensaufgaben zu bauen, führt zu komplexen, fehleranfälligen
und schwer wartbaren Systemen. Effizienter ist der Einsatz spezialisierter Experten-Agenten, die jeweils eine Aufgabe
perfekt beherrschen – sei es die Analyse von Rechtsdokumenten oder die Berechnung von Offerten. Die Fähigkeit, diese
Spezialisten dynamisch zu Teams zu verknüpfen, ermöglicht die Lösung komplexer Probleme durch Arbeitsteilung, ähnlich
wie in einer menschlichen Organisation. Dies erhöht die Wiederverwendbarkeit von Modulen und die Robustheit des
Gesamtsystems.

### Konzeptioneller Ansatz

Die Architektur unterstützt **Multi-Agenten-Systeme** durch das «Agent-in-the-Loop»-Muster. Ein primärer
Orchestrator-Agent zerlegt eine komplexe Anfrage in Teilaufgaben und delegiert diese an spezialisierte Worker-Agenten.
Diese Worker operieren in ihren eigenen isolierten Workflows und geben lediglich das Ergebnis zurück. Dieser modulare
Ansatz verhindert Seiteneffekte, da der Worker keinen direkten Zugriff auf den internen Speicher des Orchestrators hat,
sondern nur über definierte Schnittstellen kommuniziert.

### Technische Umsetzung im Swiss AI Hub

Die Plattform stellt verschiedene vorgefertigte Agenten-Typen und Muster bereit:

- **RAG-Agent:** Dieser Spezialist nutzt «Retrieval-Augmented Generation», um Antworten ausschliesslich auf Basis der in
  der Wissensdatenbank gefundenen Vektoren zu generieren. Er nutzt Mechanismen wie «Re-Ranking» und
  «Multi-Hop-Retrieval», um auch verstreute Informationen über mehrere Dokumente hinweg zu synthetisieren.
- **Expert Asking Agent:** Wenn die Wissensbasis nicht ausreicht, kann dieser Agent über eine Slack- oder
  Teams-Integration proaktiv menschliche Experten befragen. Die Antwort wird nicht nur an den Nutzer weitergeleitet,
  sondern auch in die Wissensdatenbank zurückgespeist, wodurch das System organisch lernt.
- **Orchestrierung:** Über Ereignisse wie `AgentInTheLoop.request` kann ein Agent einen anderen aufrufen. Die Plattform
  verwaltet dabei die Kontext-Übergabe (`share_thread_id`), sodass für den Endanwender die Illusion einer nahtlosen
  Konversation entsteht, während im Hintergrund ein Team von Spezialisten arbeitet.

## Menschliche Kontrolle (Human-in-the-Loop) und Qualitätssicherung

### Geschäftlicher Nutzen

Trotz aller Fortschritte gibt es Situationen, in denen eine KI nicht autonom entscheiden darf – sei es bei hohen
finanziellen Freigabegrenzen oder ethisch sensiblen Fragen. Unternehmen benötigen einen «Not-Aus-Schalter» und
Freigabeprozesse. Das Prinzip «Human-in-the-Loop» integriert menschliche Entscheider direkt in den technischen Workflow.
Dies ermöglicht Automatisierung bis zum Entscheidungspunkt, reduziert die Bearbeitungszeit drastisch und wahrt
gleichzeitig die menschliche Hoheit über kritische Resultate.

### Konzeptioneller Ansatz

Ein Agenten-Workflow im Swiss AI Hub ist nicht auf sofortige Ausführung beschränkt. Er kann asynchron pausieren und in
einen Wartezustand übergehen. Der Agent sendet eine Anfrage an einen Menschen und friert seinen aktuellen Zustand
(Speicher, Variablen) ein. Dieser Zustand kann Minuten oder Tage persistiert werden. Erst wenn die menschliche
Interaktion erfolgt – etwa eine Genehmigung per Klick –, wird der Agent «aufgeweckt» und setzt seine Arbeit mit den
neuen Eingaben fort.

### Technische Umsetzung im Swiss AI Hub

Die Qualitätssicherung wird durch zwei komplementäre Mechanismen durchgesetzt:

- **Interaktive Unterbrechung:** Durch das `HumanInTheLoop.request` wird der Workflow gestoppt und eine Aufgabe im
  Frontend generiert. Die Antwort (`HumanInTheLoop.response`) rehydriert den Prozess. Dies ist essenziell für
  Genehmigungsprozesse oder wenn der Agent bei Unsicherheit Rückfragen stellen muss.
- **Guardrails (Schutzmechanismen):** Um die Qualität der Antworten automatisch zu sichern, kommen **Input-** und
  **Output-Guards** zum Einsatz, die zusätzlich zum plattformweiten PII-Schutz (Presidio) agieren:
  - *Input Guards* (z.B. Few-Shot-Guard oder Agentenbeschreibungs-Guard) validieren, ob eine Frage thematisch zulässig
    ist und den Richtlinien entspricht.
  - *Output Guards* (z.B. Context Sufficiency Guard) analysieren vor dem Absenden der Antwort, ob die gefundenen Quellen
    die Aussage tatsächlich belegen. Ist die Faktenbasis zu dünn, wird die Antwort unterdrückt, um Halluzinationen zu
    verhindern. Zudem kann ein spezifischer *Sensitive-Info-Guard* Daten redigieren, die zwar im Dokument stehen, aber
    dem Nutzer nicht angezeigt werden sollen.
