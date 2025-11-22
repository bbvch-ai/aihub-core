# Kapitel 13: AI-Agenten und Kernkonzepte

Die transformative Kraft der Künstlichen Intelligenz (KI) entfaltet sich in Unternehmen am wirkungsvollsten, wenn sie
nicht als unkontrollierbare Black Box agiert, sondern als präziser, steuerbarer und nachvollziehbarer Assistent.
Besonders für Schweizer Organisationen, die höchsten Anforderungen an Datensouveränität, Compliance und Transparenz
unterliegen, ist eine Architektur unerlässlich, die Verlässlichkeit und Kontrollierbarkeit von KI-Systemen
gewährleistet. Dieses Kapitel beleuchtet, wie der Swiss AI Hub durch seine workflow-basierte Agentenarchitektur diesen
Bedarf adressiert und eine Grundlage für vertrauenswürdige, revisionssichere KI-Anwendungen schafft.

## Einleitung: Von Black-Box zu White-Box – Die Notwendigkeit kontrollierter KI-Agenten

Herkömmliche Large Language Models (LLMs) und offene Chatbots bieten zwar beeindruckende konversationelle Fähigkeiten,
bergen jedoch erhebliche Risiken für den Unternehmenseinsatz: fehlende Nachvollziehbarkeit von Entscheidungen, das
Risiko von "Halluzinationen" (erfundene Antworten) und mangelnde Kontrolle über Datenzugriffe oder Aktionen. Für
Schweizer Unternehmen, insbesondere im öffentlichen Sektor, sind solche intransparenten "Black-Box"-Systeme
unakzeptabel.

Der Swiss AI Hub begegnet dieser Herausforderung mit einer grundlegend anderen Philosophie: Er setzt auf spezialisierte
KI-Assistenten, sogenannte **Agenten**, die in einem strukturierten, transparenten und zuverlässigen Rahmen agieren.
Jeder Agent ist wie ein erfahrener Fachkollege konzipiert, der definierte Workflows befolgt, um Aufgaben präzise und
auditierbar zu lösen. Dies transformiert unvorhersehbare KI in ein transparentes und vertrauenswürdiges
Unternehmenswerkzeug, das den kritischen Anforderungen an Governance, Sicherheit und Compliance gerecht wird.

## 1. Determinismus durch Workflow-basierte Architektur

Die Fähigkeit, das Verhalten von KI-Systemen zu verstehen und zu steuern, ist für den Unternehmenseinsatz von
grundlegender Bedeutung. Der Swiss AI Hub löst die Intransparenz autonomer KI durch eine Architektur, die auf
deterministischen, workflow-basierten Prozessen beruht.

### Mehrwert und Nutzen: Vorhersehbarkeit, Sicherheit und Auditierbarkeit

Für C-Level-Führungskräfte bedeutet die deterministische Workflow-Steuerung, dass KI-Agenten stets ein vorhersehbares
und kontrollierbares Verhalten zeigen. Dies reduziert operationelle und regulatorische Risiken erheblich, da
unerwünschte oder unautorisierte Aktionen der KI ausgeschlossen werden. Im Gegensatz zu autonomer Tool-Auswahl, bei der
die KI selbständig über den Einsatz von Werkzeugen entscheidet, verhindert der workflow-basierte Ansatz, dass Agenten
unautorisierte Datenzugriffe durchführen oder Berechtigungsgrenzen überschreiten. Jedes Verhalten ist klar definiert und
kann vorab validiert werden. IT-Verantwortliche profitieren von einer transparenten Architektur, die die
Nachvollziehbarkeit und Testbarkeit von KI-Anwendungen massgeblich verbessert.

### Konzepte & Prozesse: Strukturierte Workflows und das Swiss AI Agent Protokoll (SAAP)

Im Kern der Agentenarchitektur steht der **Workflow** – eine explizit vordefinierte, Schritt-für-Schritt-Abfolge von
Operationen. Ein Agent ist durch seinen Workflow eingeschränkt und kann keine Aktionen ausserhalb dieser vordefinierten
Reihenfolge ausführen. Innerhalb jedes Schrittes kann der Agent zwar die volle Leistung der KI nutzen, um zu
argumentieren und intelligente Entscheidungen zu treffen, der Gesamtpfad wird jedoch durch den definierten Workflow
gesteuert.

Die Kommunikation zwischen den internen Komponenten der Plattform, einschliesslich der Agenten, wird durch das **Swiss
AI Agent Protokoll (SAAP)** geregelt. Dieses ereignisgesteuerte Modell ist für die interne Kohäsion der Swiss AI Hub
Instanz konzipiert und definiert standardisierte Events, die den Daten- und Kontrollfluss steuern. Hierbei wird strikt
zwischen `Control Events` (die den Workflow steuern und Zustandsänderungen verursachen) und `Display Events` (die rein
informativ sind und Statusupdates für die Benutzeroberfläche liefern) unterschieden. Ein `Control Event` löst die
Ausführung eines Agenten-Schritts aus, während `Display Events` niemals den logischen Fluss des Workflows beeinflussen.

Das Gedächtnis eines Agenten wird durch ein hierarchisches Kontextmanagement in drei Scopes organisiert:

- **`Thread Context`**: Das Langzeitgedächtnis für eine gesamte Konversation oder einen langlaufenden Geschäftsprozess,
  mit einer Gültigkeitsdauer von 30 Tagen. Die Zugriffskontrolle wird auf dieser Ebene angewendet.
- **`Display Context`**: Für die Aggregation und Darstellung von Aktionen in der Benutzeroberfläche, auch über mehrere
  Agenten hinweg.
- **`Run Context`**: Das Kurzzeit-Arbeitsgedächtnis für eine einzelne, nachverfolgbare Aufgabe, das nach 30 Tagen
  abläuft und zwischen Läufen isoliert ist.

### Technische Umsetzung im Swiss AI Hub: SDK und Event-Routing

Das AI-Hub SDK unterstützt Entwickler beim Erstellen solcher Agenten, indem es einen `Agent Dispatcher` bereitstellt.
Dieser Dispatcher inspiziert mit dem `@step`-Decorator markierte Methoden, analysiert deren Parameter und Rückgabetypen
und erstellt eine Workflow-Karte. Wenn ein Schritt ein `Control Event` zurückgibt, fängt der Dispatcher es ab und leitet
es an den nächsten Schritt weiter, der diesen spezifischen Ereignistyp annehmen kann, wodurch die Schritte automatisch
verkettet werden. Benutzerdefinierte `Control Events`, die von `aihub_agent.events.ControlEvent` erben, können Daten
zwischen Schritten übergeben. Die Kommunikation über SAAP erfolgt asynchron über einen zentralen Message Bus (NATS),
wodurch das System hoch skalierbar und resilient wird. Jeder Agenten-Schritt ist eine `async`-Methode, die eine
einzelne, logische Operation ausführt und durch den `@step`-Decorator registriert wird. Die Konfiguration erfolgt über
stark typisierte `AgentConfig`- und `StepConfig`-Klassen, die dynamisch in die Schrittmethoden injiziert werden, um die
Logik von den Einstellungen zu trennen und Wiederverwendbarkeit zu fördern.

## 2. Spezialisierte Agenten für spezifische Aufgaben und Integration

Um komplexe Unternehmensaufgaben effizient und sicher zu lösen, setzt der Swiss AI Hub auf spezialisierte Agenten-Typen,
die nahtlos in bestehende Fachanwendungen integriert werden können.

### Mehrwert und Nutzen: Gezielte Problemlösung und Investitionsschutz

Spezialisierte Agenten ermöglichen es Unternehmen, KI gezielt für hochspezifische Anwendungsfälle einzusetzen, von der
Beantwortung von Fragen aus internen Dokumenten bis zur Unterstützung bei komplexen Entscheidungsprozessen. Dies
maximiert den Nutzen der KI, da sie genau auf den jeweiligen Kontext zugeschnitten ist. Die gesicherten Schnittstellen
gewährleisten zudem, dass diese Agenten sicher in bestehende IT-Systeme integriert werden können, was den
Investitionsschutz vorhandener Infrastrukturen sicherstellt und teure Insellösungen vermeidet. C-Level-Führungskräfte
profitieren von einer effizienteren Problemlösung und der Möglichkeit, wertvolles, aber zuvor unstrukturiertes
Unternehmenswissen zu erschliessen.

### Konzepte & Prozesse: RAG-Agenten, Experten-Agenten und Multi-Agenten-Systeme

Der Swiss AI Hub bietet vorgefertigte Agenten für gängige Unternehmensanforderungen:

- **RAG-Agenten (Retrieval-Augmented Generation)**: Diese Agenten sind Wissensspezialisten, die Fragen durch die
  Konsultation interner Dokumente und Datenquellen beantworten. Sie überwinden die Wissenslücke von generischen LLMs,
  indem sie relevante Informationen aus unternehmenseigenen Wissensdatenbanken abrufen und darauf basierend Antworten
  synthetisieren. Ihr Workflow umfasst Fragenverständnis, Wissensabruf, Kontextrekonstruktion, Re-Ranking und
  Antwortsynthese, einschliesslich der Zitation von Quellen zur Überprüfung. Sie können auch Multi-Hop-Retrieval
  durchführen, wenn die initiale Suche unzureichend ist.
- **Experten-Agenten (Expert Grounded Agent / Expert Asking Agent)**: Dieses Agentenpaar überbrückt die Lücke zwischen
  KI-Fähigkeiten und menschlichem Fachwissen. Wenn der Expert Grounded Agent eine Frage nicht zuverlässig beantworten
  kann, leitet er diese an den Expert Asking Agent weiter, der sie einem menschlichen Experten (z.B. über Slack) zur
  Klärung vorlegt. Die Expertenantwort wird erfasst und dauerhaft in der Wissensdatenbank gespeichert, wodurch die KI
  kontinuierlich lernt und die Wissensbasis erweitert wird.
- **Multi-Agenten-Systeme**: Das "Agent in the Loop (AITL)"-Muster ermöglicht die Delegation von Aufgaben von einem
  primären Orchestrator-Agenten an spezialisierte Worker-Agenten. Dies fördert modulare, wiederverwendbare Komponenten
  und die Trennung von Zuständigkeiten.

### Technische Umsetzung im Swiss AI Hub: LiteLLM und AgentInTheLoop

Der RAG-Agent nutzt das `LiteLLM-Proxy`-Gateway, um auf verschiedene Sprachmodelle zuzugreifen und diese für die
Aufbereitung von Prompts und die Synthese von Antworten zu verwenden. Die Anbindung an Wissensdatenbanken und die
Nutzung von vLLM oder llama.cpp für lokale LLMs sind Teil dieser Implementierung. Die Zusammenarbeit zwischen Agenten
wird durch das `AgentInTheLoop`-Ereignismuster orchestriert. Der Orchestrator-Agent sendet ein
`AgentInTheLoop.request`-Ereignis mit einem `start_event` an den Worker-Agenten. Der Worker führt seinen Workflow aus
und sendet ein `StopEvent` zurück, das der Orchestrator als `AgentInTheLoop.response`- oder
`AgentInTheLoop.exception`-Ereignis empfängt. Dies ermöglicht komplexe Ketten und parallele Workflows, während die
konversationellen Fähigkeiten der Agenten durch die Verwaltung des `ThreadContext` und `DisplayContext` gewahrt bleiben.

## 3. Menschliche Aufsicht und Human-in-the-Loop-Muster

Nicht jede KI-Entscheidung kann oder sollte vollständig automatisiert werden. Für kritische Geschäftsprozesse ist die
Möglichkeit zur menschlichen Kontrolle und Genehmigung unerlässlich.

### Mehrwert und Nutzen: Verantwortung, Compliance und menschliche Expertise

Die Implementierung von Human-in-the-Loop (HITL)-Mechanismen stellt sicher, dass in sensiblen oder kritischen
Entscheidungsprozessen stets menschliches Urteilsvermögen integriert ist. Dies gewährleistet Compliance-Anforderungen,
minimiert Risiken und sichert die Verantwortung bei entscheidenden Schritten. Führungskräfte erhalten die Gewissheit,
dass KI als leistungsstarker Assistent dient, aber die finale Kontrolle beim Menschen verbleibt. Zudem ermöglichen
HITL-Muster die effektive Erfassung menschlicher Expertise in der Wissensbasis, was die KI kontinuierlich intelligenter
macht.

### Konzepte & Prozesse: Workflow-Pause, Kontextkonservierung und Audit-Spur

HITL-Workflows ermöglichen es einem Agenten, seinen Prozess an einem kritischen Punkt zu pausieren und auf menschliche
Eingaben, Genehmigungen oder Korrekturen zu warten. Der Workflow wird genau an diesem Punkt fortgesetzt, wobei das volle
Gedächtnis aller Zwischenergebnisse und vorheriger Schritte bewahrt bleibt. Dies ist weitaus leistungsfähiger als
einfache Benutzereingabeaufforderungen. Die Wartezeiten können Minuten, Stunden oder sogar Tage betragen, was die
Bearbeitung langlaufender Genehmigungsprozesse unterstützt. Jede menschliche Interaktion – die gestellte Frage, die
Antwort, die Entscheidung – wird unveränderlich als Ereignis protokolliert, was eine vollständige Verantwortlichkeit für
Compliance und Auditing gewährleistet.

### Technische Umsetzung im Swiss AI Hub: `HumanInTheLoop` Events

Das HITL-Muster wird durch ein Paar von Events orchestriert: Ein Schritt im Agenten gibt ein
`HumanInTheLoop.request`-Event zurück, das den Workflow pausiert und dem Benutzer eine Frage in der UI präsentiert. Die
Antwort des Benutzers wird als `HumanInTheLoop.response`-Event an das System zurückgesendet und löst die Fortsetzung des
Workflows in einem dafür vorgesehenen Schritt aus. Die `HumanInTheLoop`-Helferklasse im SDK vereinfacht die
Implementierung dieser Muster für einzelne oder mehrstufige Genehmigungsprozesse. Alle menschlichen Interaktionen werden
im Rahmen der lückenlosen Nachvollziehbarkeit aufgezeichnet.

## 4. Lückenlose Nachvollziehbarkeit und Auditierbarkeit

Ein vertrauenswürdiges KI-System erfordert vollständige Transparenz und die Fähigkeit, jede Entscheidung bis zu ihrer
Quelle zurückzuverfolgen.

### Mehrwert und Nutzen: Vertrauen, Compliance und effizientes Debugging

Für Unternehmen, insbesondere im öffentlichen Sektor, ist die revisionssichere Nachvollziehbarkeit von KI-Entscheidungen
eine zentrale Anforderung für Governance, Compliance (revDSG, DSGVO) und interne Audits. Dies schafft Vertrauen in die
KI-Systeme und ermöglicht die effektive Bearbeitung von Auskunftsrechten. IT-Teams profitieren von detaillierten
Einblicken, die eine präzise Ursachenanalyse bei Fehlern ermöglichen, Leistungsengpässe identifizieren und die
Kostenattribution auf granularer Ebene erlauben.

### Konzepte & Prozesse: Hierarchischer Kontext, unveränderliche Protokollierung und Data Lineage

Jede bedeutsame Aktion und Zustandsänderung innerhalb der Plattform wird als unveränderliches Ereignis protokolliert.
Das hierarchische Scoping (`Thread`, `Display`, `Run`) stellt sicher, dass jeder Vorgang präzise kontextualisiert ist.
Das SAAP definiert jede bedeutsame Aktion, jeden Gedanken oder jede Zustandsänderung als ein eigenständiges Ereignis,
was für detailliertes Tracing und Debugging unerlässlich ist. Für RAG-Antworten wird eine lückenlose **Data Lineage**
gewährleistet: Es wird exakt festgehalten, welche spezifischen Quelldokumente, Dokumentversionen oder Text-Chunks die
Basis für eine KI-generierte Antwort bildeten. Dies ist entscheidend, um die Faktenbasis zu überprüfen und
"Halluzinationen" zu identifizieren. LLM-Aufrufe mit Prompts und Responses werden geloggt, ebenso wie die Tool-Nutzung.

### Technische Umsetzung im Swiss AI Hub: OpenTelemetry, OpenInference und LLM-Tracing

Der Swiss AI Hub nutzt **OpenTelemetry (OTel)** als fundamentalen Observability-Standard, ergänzt durch **OpenInference
Semantic Conventions** für KI/ML-Workloads. Jeder Agentenlauf wird mit hierarchischen Span-Strukturen getraced, die den
gesamten Workflow von der Benutzereingabe bis zur endgültigen Ausgabe abbilden. Der `AgentRunTracer` erstellt einen
Zwei-Span-Ansatz mit einem initialen AGENT-Span als Elternteil und einem finalen CHAIN-Span, der die Gesamtdauer
erfasst. Individuelle STEP-Spans zeigen Eingaben, Ausgaben, Verarbeitungszeit und semantische Ereignisse. `LLMEvent`s
erfassen Details zu LLM-Aufrufen, Prompts, Antworten und Token-Nutzung, während `RetrieverEvent`s die abgerufenen
Dokumente aus der Wissensbasis protokollieren. `LLMCostEvent`s zeichnen die berechneten Kosten einer LLM-Interaktion auf
und ermöglichen die Kostenattribution pro Agent-Execution. Diese Daten werden an Observability-Backends wie die
**Phoenix UI** (für Entwicklung, `http://localhost:6006`) oder **SigNoz** (für Produktion) exportiert. Die Phoenix UI
bietet spezialisierte Ansichten mit Timeline-Ansichten, Token-Nutzung und Inspektionsmöglichkeiten abgerufener
Dokumente, wodurch der Denkprozess und die Faktenbasis der KI sichtbar werden. Die `AihubInstrumentor`-Komponente
instrumentiert automatisch NATS Messaging, Datenbankoperationen, HTTP-Aufrufe, LLM-Interaktionen und Vektorsuchen.

## 5. Qualitätssicherung und Halluzinationsvermeidung

Die Zuverlässigkeit und Genauigkeit von KI-generierten Antworten sind für den Unternehmenseinsatz entscheidend. Der
Swiss AI Hub implementiert vielfältige Massnahmen zur Qualitätssicherung und zur präventiven Vermeidung von
Halluzinationen.

### Mehrwert und Nutzen: Verlässlichkeit, Vertrauen und Responsible AI

Durch stringente Kontrollmechanismen wird das Risiko von Fehlinformationen oder falschen Ausgaben minimiert, was die
Verlässlichkeit der KI-Systeme massgeblich erhöht und das Vertrauen der Nutzer stärkt. C-Level-Verantwortliche können
sich auf präzise und ethisch korrekte KI-Ergebnisse verlassen, was die Prinzipien von "Responsible AI"
operationalisiert. IT- und Fachteams erhalten Werkzeuge zur kontinuierlichen Verbesserung der KI-Performance und zur
Einhaltung von Qualitätsstandards.

### Konzepte & Prozesse: LLM-Wächter, PII-Anonymisierung und Agentenbewertungen

Der Swiss AI Hub setzt sogenannte **LLM-Wächter (Guardrails)** ein, die Agenten-Interaktionen in Echtzeit überprüfen:

- **Input-Wächter**: Analysieren Benutzerfragen, bevor der Agent sie verarbeitet, und filtern themenfremde Anfragen oder
  Richtlinienverstösse heraus. Dazu gehören der `Agentenbeschreibungs-Schutzmechanismus` und der
  `Few-shot-Schutzmechanismus`.
- **Output-Wächter**: Prüfen generierte Antworten vor der Auslieferung, um deren Qualität, Angemessenheit und Sicherheit
  zu verifizieren. Der `Kontext-Ausreichend-Schutzmechanismus` ist besonders für RAG-Agenten wichtig, da er prüft, ob
  ausreichend Informationen aus den Wissensdatenbanken für eine präzise Antwort vorhanden sind, und so Halluzinationen
  entgegenwirkt. Ein `Wächter für sensible Informationen` erkennt und redigiert vertrauliche oder personenbezogene Daten
  (PII) aus Agentenantworten.

Für den Schutz sensibler Daten ist die **automatische PII-Anonymisierung** durch die Integration von Presidio
implementiert. Persönlich identifizierbare Informationen werden in der LiteLLM-Proxy-Schicht anonymisiert oder
geschwärzt, bevor sie externe LLMs erreichen. Domänenspezifisches Prompt-Engineering (z.B. für Schweizer Recht) wird
durch die flexible Konfiguration der Agenten und die Nutzung spezialisierter Wissensdatenbanken ermöglicht. Strikte
Input-Validierungen gegen bösartige Eingaben (Dateityp-Whitelisting, MIME-Typ-Validierung, Dateinamenprüfung) sind
ebenfalls implementiert.

Die **Qualität des Outputs** wird zudem durch **Agentenbewertungen** gemessen. Hierbei werden Agenten anhand
vordefinierter Datasets (Fragen mit Referenzantworten) durch drei unabhängige KI-Richter (LLMs) evaluiert. Diese
bewerten die Agentenantworten nach **Korrektheit, Vollständigkeit und Prägnanz** (0-5 Sterne), was eine messbare
Qualitätskontrolle vor und nach dem Deployment ermöglicht. Integriertes Benutzerfeedback (Daumen hoch/runter) fliesst in
ein Elo-basiertes Ranglistensystem ein und trägt zur kontinuierlichen Verbesserung bei.

**UNKLARHEIT IN DER DOKU - BITTE PRÜFEN:** Eine explizite Anzeige des Konfidenzgrades oder der Unsicherheit der
KI-Antwort als UI-Funktion ist in der Quelldokumentation nicht beschrieben. Der "Context Sufficiency Guard" erfüllt eine
ähnliche Funktion, indem er unzureichenden Kontext markiert. **UNKLARHEIT IN DER DOKU - BITTE PRÜFEN:** Automatisierte
Bias-Überwachung oder Modell-Drift-Erkennung ist in der Plattform derzeit nicht implementiert. Das Bewertungs-Framework
und OpenTelemetry-Tracing bieten jedoch grundlegende Funktionen, die für eine Erweiterung genutzt werden könnten.

### Technische Umsetzung im Swiss AI Hub: Konfigurierbare Wächter und Bewertungsdienst

Die LLM-Wächter sind als konfigurierbare Komponenten in die Agenten-Workflows integrierbar. Beispielsweise kann der
`Few-Shot-Wächter` über konfigurierbare Beispiele für zulässige oder unzulässige Fragen trainiert werden. Die
PII-Anonymisierung mittels Presidio erfolgt präventiv in der Verarbeitungskette. Der Bewertungsdienst ermöglicht das
Erstellen von Datasets und das Ausführen von Experimenten, wobei die drei KI-Richter Bewertungen nach den Metriken
Korrektheit, Vollständigkeit und Prägnanz abgeben. Die Ergebnisse werden detailliert in der UI angezeigt und dienen als
Grundlage für Optimierungen.

## 6. Sichere Orchestrierung von Multi-Agenten-Systemen

Komplexe Probleme erfordern oft die Koordination mehrerer spezialisierter Agenten. Die Architektur des Swiss AI Hub
ermöglicht die sichere Orchestrierung von Multi-Agenten-Systemen unter Einhaltung strenger Governance-Vorgaben.

### Mehrwert und Nutzen: Modularität, Skalierbarkeit und kontrollierte Prozesse

Die Möglichkeit, Multi-Agenten-Systeme zu erstellen, fördert die Entwicklung modularer, wiederverwendbarer KI-Lösungen
und ermöglicht die Aufteilung komplexer Aufgaben in spezialisierte Teilbereiche. Dies steigert die Skalierbarkeit und
Wartbarkeit der gesamten KI-Landschaft. Für Unternehmen bedeutet dies, dass komplexe Geschäftsprozesse durch ein
Zusammenspiel von spezialisierten KI-Agenten automatisiert werden können, wobei strikte Governance-Vorgaben eingehalten
und unautorisierte Aktionen oder Berechtigungsgrenzen vermieden werden.

### Konzepte & Prozesse: Agent-zu-Agent-Delegation und Kontextfreigabe

Das **Agent in the Loop (AITL)**-Muster ermöglicht die Delegation von Aufgaben von einem Orchestrator-Agenten an einen
oder mehrere Worker-Agenten. Der Worker-Agent führt seine Aufgabe in einem eigenen, isolierten Workflow aus. Dabei kann
die **Kontextfreigabe** gesteuert werden: Standardmässig teilen sich Worker denselben Konversationsspeicher
(`ThreadContext`) und UI-Stream (`DisplayContext`) mit dem Orchestrator, während sie in einem eigenen, unabhängigen
`RunContext` operieren. Dies gewährleistet eine kontrollierte Zusammenarbeit. Gängige Multi-Agenten-Muster umfassen
spezialisierte Verarbeitung (Router), sequentielle Agentenketten und parallele Agentenausführung (Fan-Out/Fan-In).

### Technische Umsetzung im Swiss AI Hub: `AgentInTheLoop.invoke` und Dispatcher

Die Delegation wird durch das `AgentInTheLoop.invoke`-Kommando orchestriert, das den `agent_id`, `agent_class` und das
`start_event` für den Worker-Agenten enthält. Der Dispatcher leitet das `start_event` an den Worker weiter, der seinen
Workflow ausführt und das Ergebnis als `StopEvent` an den Orchestrator zurückgibt. Die `AgentInTheLoop`-Klasse
ermöglicht die flexible Steuerung der Kontextfreigabe (`share_thread_id`, `share_display_id`, `share_run_id`). Letzteres
ist standardmässig `False`, um eine strikte Isolation der Laufzeitkontexte zu gewährleisten und unerwünschte
Nebenwirkungen zu verhindern. Dies verhindert, dass automatisierte Prozesse unautorisierte Aktionen ausführen oder
Berechtigungsgrenzen überschreiten, da jeder Agent in seinem definierten Rahmen agiert.
