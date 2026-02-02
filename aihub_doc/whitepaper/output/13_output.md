# Kapitel 13: AI-Agenten und Kernkonzepte

Während die vorangegangenen Kapitel die Infrastruktur, Sicherheit und Datenintegration beleuchtet haben, widmet sich
dieser Abschnitt dem Herzstück der Wertschöpfung: den KI-Agenten selbst. In der öffentlichen Wahrnehmung werden Agenten
oft mit autonomen Chatbots gleichgesetzt, die frei improvisieren. Im Unternehmenskontext ist Improvisation jedoch ein
Risiko. Geschäftsprozesse verlangen nach Konsistenz, Nachvollziehbarkeit und strikter Kontrolle.

Der Swiss AI Hub bricht mit dem Paradigma der undurchsichtigen «Black Box». Anstatt monolithische Modelle unkontrolliert
entscheiden zu lassen, setzt die Plattform auf eine Architektur aus spezialisierten, workflow-basierten Komponenten.
Dieses Kapitel beschreibt, wie durch deterministische Baupläne, das Swiss AI Agent Protokoll und menschliche
Interventionsmöglichkeiten («Human-in-the-Loop») verlässliche KI-Systeme entstehen, die auch komplexen regulatorischen
Anforderungen genügen.

## Auf einen Blick

- **Deterministische Workflows:** Agenten folgen fest definierten Pfaden (Closed Workflows) statt autonomer
  Improvisation, was das Verhalten vorhersagbar und auditierbar macht.
- **Transparenz durch Protokoll:** Das Swiss AI Agent Protokoll trennt strikt zwischen Steuerungslogik («Control
  Events») und Benutzerinformation («Display Events») für eine lückenlose Nachvollziehbarkeit.
- **Managed State & Context:** Eine dreistufige Kontext-Hierarchie (Run, Display, Thread) isoliert technische
  Ausführungen und sichert das Langzeitgedächtnis über 30 Tage.
- **Human- & Agent-in-the-Loop:** Kritische Prozesse können asynchron pausieren, um menschliche Genehmigungen einzuholen
  oder Aufgaben an spezialisierte Worker-Agenten zu delegieren.
- **Aktive Qualitätssicherung:** Integrierte Schutzmechanismen (Guards) validieren Eingaben und prüfen Antworten auf
  Faktenbasis (Context Sufficiency), um Halluzinationen technisch zu unterbinden.

## Deterministische Workflow-Steuerung statt «Black Box»

### Geschäftlicher Nutzen

Ein fundamentaler Hinderungsgrund für den KI-Einsatz in kritischen Bereichen ist die Unvorhersehbarkeit. Wenn ein
Sprachmodell halluziniert oder eine Entscheidung auf einer undurchsichtigen Basis trifft, entstehen Haftungs- und
Prozessrisiken. Unternehmen und Behörden benötigen die Gewissheit, dass ein Agent definierten Regeln folgt. Ein
«Workflow-basierter Agent» bietet diese Sicherheit. Er garantiert, dass Prozesse immer denselben validierten Pfaden
folgen, Audit-Anforderungen erfüllen und nicht vom vorgesehenen Skript abweichen. Dies verwandelt KI von einem
unberechenbaren Experiment in ein stabiles Werkzeug für die professionelle Prozessautomatisierung.

### Konzeptioneller Ansatz

Das Konzept unterscheidet strikt zwischen der «Intelligenz» des Sprachmodells und der «Steuerung» des Prozesses. Anstatt
dem Modell eine vage Anweisung zu geben und auf eine korrekte Werkzeugwahl zu hoffen, wird der Agent in einen «Closed
Workflow» eingebettet. Dieser Workflow definiert eine präzise Kette von Schritten, die deterministisch ausgeführt
werden. Das Sprachmodell wird dabei lediglich als kognitiver Motor innerhalb einzelner Schritte genutzt – etwa um Text
zu analysieren oder zu formulieren –, während die Entscheidungslogik über den nächsten Schritt (Verzweigungen,
Schleifen, Abbruchbedingungen) fest im Code verankert bleibt.

### Technische Umsetzung im Swiss AI Hub

Im Swiss AI Hub wird dieses Konzept durch die Trennung von **Agenten-Bauplan** und **Agenten-Profil** sowie den **Agent
Dispatcher** realisiert:

- **Agenten-Bauplan:** Dies ist der unveränderliche Python-Code, der die Logik und die Abfolge der Schritte definiert.
  Der Bauplan legt fest, wie Ereignisse verarbeitet werden und welche Aktionen (z. B. Datenbankabfrage via RAG) erlaubt
  sind.
- **Agenten-Profil:** Dies ist die instanziierte Konfiguration eines Bauplans. Ein Profil bestimmt, auf welche
  spezifischen Wissensdatenbanken oder Modelle der Agent zugreifen darf. So können auf demselben Bauplan basierend ein
  «HR-Agent» und ein «Rechts-Agent» erstellt werden, die strikt getrennt operieren.
- **Agent Dispatcher:** Diese Kernkomponente orchestriert die Ausführung. Durch Introspektion analysiert der Dispatcher
  die Schritte des Bauplans und injiziert mittels «Dependency Injection» automatisch notwendige Objekte wie die
  Konfiguration, den `RunContext` (temporärer Speicher) oder den `ThreadContext` (langfristiges Gedächtnis).

## Transparenz durch das Swiss AI Agent Protokoll

### Geschäftlicher Nutzen

Um Vertrauen in automatisierte Systeme zu schaffen, muss jede Aktion erklärbar sein. Auditoren müssen rekonstruieren
können, warum ein Agent zu einem bestimmten Ergebnis kam. Proprietäre Frameworks verstecken diese internen Abläufe oft.
Eine offene Standardisierung der Kommunikation ermöglicht hingegen eine lückenlose Beobachtbarkeit («Observability») und
Fehleranalyse. Dies ist essenziell, um regulatorische Anforderungen an die Erklärbarkeit von KI-Entscheidungen zu
erfüllen, ohne sich in proprietäre Abhängigkeiten zu begeben.

### Konzeptioneller Ansatz

Die Plattform nutzt für die interne Kommunikation das **Swiss AI Agent Protokoll**. Dieses ereignisgesteuerte Modell
definiert eine klare Sprache für alle Interaktionen. Kernprinzip ist die strikte Unterscheidung zwischen Steuerung und
Anzeige. Während Steuerungsereignisse den logischen Fluss vorantreiben, dienen Anzeigeereignisse der Information des
Nutzers (z. B. Gedankenprotokolle). Jedes Ereignis ist ein unveränderlicher Faktennachweis, der in einer dreistufigen
Hierarchie (Run, Display, Thread) verortet ist.

### Technische Umsetzung im Swiss AI Hub

Das Protokoll wird über einen zentralen Message Bus (NATS) abgewickelt und definiert präzise Ereignis-Typen:

- **Control Events:** Ereignisse wie `StartEvent`, `UserMessageEvent` oder `StopEvent` sind die einzigen Trigger, die
  einen Zustandsübergang im Workflow auslösen dürfen.
- **Display Events:** Ereignisse wie `ThoughtEvent` oder `ChunkEvent` streamen Zwischenstände oder «Überlegungen» des
  Agenten an das Frontend, ohne den Prozessstatus zu beeinflussen.
- **Hierarchische Scopes:** Jedes Ereignis trägt Metadaten zu seinem Scope. Der `Run-Kontext` isoliert die technische
  Ausführung, während der `Thread-Kontext` den persistenten Zustand über Konversationen hinweg speichert (bis zu 30
  Tage). Dies stellt sicher, dass Agenten sich an frühere Interaktionen erinnern, während die Zugriffskontrolle auf
  Thread-Ebene gewahrt bleibt.

## Spezialisierung und Multi-Agenten-Kollaboration

### Geschäftlicher Nutzen

Der Versuch, einen einzigen «Super-Agenten» für alle Unternehmensaufgaben zu bauen, führt zu komplexen und schwer
wartbaren Systemen. Effizienter ist der Einsatz spezialisierter Experten-Agenten, die jeweils eine Aufgabe perfekt
beherrschen. Die Fähigkeit, diese Spezialisten dynamisch zu Teams zu verknüpfen, ermöglicht die Lösung komplexer
Probleme durch Arbeitsteilung. Dies erhöht die Wiederverwendbarkeit von Modulen und die Robustheit des Gesamtsystems, da
Fehler in einem Teil-Agenten nicht den gesamten Prozess gefährden.

### Konzeptioneller Ansatz

Die Architektur unterstützt Multi-Agenten-Systeme durch das «Agent-in-the-Loop»-Muster. Ein primärer Orchestrator-Agent
zerlegt eine komplexe Anfrage in Teilaufgaben und delegiert diese an spezialisierte Worker-Agenten. Diese Worker
operieren in ihren eigenen isolierten Workflows. Ein besonderes Muster ist hierbei die Parallelverarbeitung («Fan-Out /
Fan-In»), bei der Aufgaben gleichzeitig an mehrere Agenten verteilt und deren Ergebnisse anschliessend aggregiert
werden.

### Technische Umsetzung im Swiss AI Hub

Die Plattform stellt verschiedene Muster und spezialisierte Agenten bereit:

- **RAG-Agent:** Nutzt Retrieval-Augmented Generation, um Antworten ausschliesslich auf Basis der Wissensdatenbank zu
  generieren. Er verwendet «Multi-Hop-Retrieval», um Informationen über mehrere Dokumente hinweg zu synthetisieren.
- **Expert Asking Agent:** Wenn die Wissensbasis nicht ausreicht, eskaliert dieser Agent die Frage an menschliche
  Experten via Microsoft Teams oder Slack. Die Antwort wird erfasst und kann automatisch in die Wissensdatenbank
  zurückgespeist werden, wodurch das System organisch lernt.
- **Orchestrierung:** Über `AgentInTheLoop.invoke()` kann ein Agent einen anderen aufrufen. Dabei kann konfiguriert
  werden, ob der `Thread-Kontext` geteilt wird (`share_thread_id`), um eine nahtlose Konversationshistorie über
  Agentengrenzen hinweg zu wahren.

## Menschliche Kontrolle und Qualitätssicherung

### Geschäftlicher Nutzen

Trotz aller Fortschritte gibt es Situationen, in denen eine KI nicht autonom entscheiden darf – etwa bei hohen
finanziellen Freigaben oder rechtlich sensiblen Fragen. Unternehmen benötigen einen «Not-Aus-Schalter» und
Freigabeprozesse. Das Prinzip «Human-in-the-Loop» integriert menschliche Entscheider direkt in den technischen Workflow.
Dies ermöglicht Automatisierung bis zum Entscheidungspunkt und wahrt gleichzeitig die menschliche Hoheit über kritische
Resultate.

### Konzeptioneller Ansatz

Ein Agenten-Workflow im Swiss AI Hub kann asynchron pausieren. Der Agent sendet eine Anfrage an einen Menschen und
friert seinen aktuellen Zustand (Speicher, Variablen) ein. Erst wenn die menschliche Interaktion erfolgt, wird der Agent
«aufgeweckt» und setzt seine Arbeit fort. Parallel dazu sorgen automatisierte Schutzmechanismen («Guards») dafür, dass
sowohl die Eingaben der Nutzer als auch die Ausgaben der Agenten vordefinierte Qualitäts- und Sicherheitsstandards
erfüllen.

### Technische Umsetzung im Swiss AI Hub

Die Qualitätssicherung wird durch zwei komplementäre Mechanismen durchgesetzt:

- **Human-in-the-Loop:** Durch `HumanInTheLoop.request` wird der Workflow gestoppt und eine Aufgabe im Frontend
  generiert. Der Agent behält alle Zwischenergebnisse im Speicher, bis die Antwort (`HumanInTheLoop.response`)
  eintrifft.
- **Schutzmechanismen (Guards):** Diese validieren Interaktionen in Echtzeit:
  - **Eingangs-Schutzmechanismen:** Der «Agentenbeschreibungs-Schutzmechanismus» oder «Few-shot-Schutzmechanismus»
    prüft, ob eine Anfrage thematisch zulässig ist.
  - **Ausgangs-Schutzmechanismen:** Der «Context Sufficiency Guard» prüft vor dem Absenden, ob die gefundenen Quellen
    die Antwort tatsächlich belegen. Der «Schutzmechanismus für sensible Informationen» redigiert PII
    (Personenidentifizierbare Informationen), die aus internen Dokumenten stammen könnten, bevor sie dem Benutzer
    angezeigt werden.
