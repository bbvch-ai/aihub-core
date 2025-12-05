# Kapitel 13: AI-Agenten und Kernkonzepte

## Jenseits der Black Box: Deterministische Prozesssicherheit

Der Einsatz von künstlicher Intelligenz in geschäftskritischen Bereichen scheitert oft an einem fundamentalen
Vertrauensproblem: Klassische KI-Modelle agieren als intransparente «Black Box». Ein Anwender stellt eine Frage, und das
System generiert eine Antwort – doch der Weg dorthin bleibt im Dunkeln. Für Schweizer Unternehmen, die strengen
Compliance-Vorgaben und Revisionsanforderungen unterliegen, ist diese Unvorhersehbarkeit inakzeptabel. Ein System, das
heute so und morgen anders entscheidet, lässt sich nicht auditieren.

Der Swiss AI Hub bricht mit diesem Paradigma der unkontrollierten Autonomie. Die Plattform betrachtet KI-Agenten nicht
als magische Orakel, sondern als Software-Komponenten, die strikten, deterministischen Workflows folgen. Anstatt einem
Sprachmodell lediglich Werkzeuge bereitzustellen und ihm die Wahl der Vorgehensweise zu überlassen, definiert der
**Agenten-Bauplan** präzise Prozessschritte. Diese Workflow-basierte Steuerung garantiert, dass sich die KI stets
innerhalb definierter Leitplanken bewegt.

Fachlich bedeutet dies den Übergang von probabilistischer Improvisation zu deterministischer Prozessausführung. Ein
Agent auf der Plattform ist ein spezialisierter Assistent, der eine Aufgabe durch eine vordefinierte Sequenz von
Operationen löst. Technisch realisiert der Swiss AI Hub dies durch das proprietäre **Swiss AI Agent Protokoll**. Dieses
ereignisgesteuerte Framework trennt strikt zwischen der Steuerungslogik («Control Events») und der Ausgabe («Display
Events»). Während der Agent im Hintergrund komplexe Entscheidungsbäume durchläuft oder Datenbanken abfragt, dienen
Display-Ereignisse wie `ThoughtEvent` oder `ChunkEvent` dazu, dem Benutzer den «Gedankengang» des Agenten transparent zu
machen, ohne die logische Ausführung zu beeinflussen.

Zentral für die Sicherheit ist hierbei das hierarchische Kontext-Management. Das Protokoll unterscheidet zwischen dem
**Run-Kontext** (für die isolierte Ausführung eines einzelnen Workflows), dem **Display-Kontext** (für die Darstellung
in der Benutzeroberfläche) und dem **Thread-Kontext**. Letzterer speichert den Zustand einer Konversation sicher über
bis zu 30 Tage. Dies gewährleistet, dass ein Agent sich an frühere Interaktionen erinnert, ohne dass Daten
unkontrolliert zwischen verschiedenen Mandanten oder Prozessen diffundieren.

## Integration von Unternehmenswissen durch RAG-Agenten

Ein häufiges Missverständnis bei der Einführung von KI ist die Annahme, man müsse Modelle mit eigenen Daten
«trainieren», um sie nutzbar zu machen. Dieser Ansatz ist nicht nur kostenintensiv, sondern führt dazu, dass veraltetes
Wissen im Modell eingefroren wird. Unternehmen benötigen jedoch Antworten, die auf den aktuellen Richtlinien,
Preislisten und Verträgen basieren, nicht auf dem Stand des letzten Trainings vor sechs Monaten.

Der Swiss AI Hub setzt daher auf spezialisierte **RAG-Agenten (Retrieval-Augmented Generation)**. Diese Agenten besitzen
kein statisches Wissen, sondern die Fähigkeit, dynamisch auf aktuelle Unternehmensdaten zuzugreifen, die über die
**Daten-zu-Wissen-Pipeline** in einer **Wissensdatenbank** bereitgestellt werden. Der Workflow beginnt mit dem
Verständnis der Frage und der gezielten Suche in den zugewiesenen Sammlungen. Erst wenn relevante Informationen
abgerufen wurden, synthetisiert das Sprachmodell eine Antwort, die ausschliesslich auf diesen Fakten basiert.

Dieser Ansatz bietet zwei entscheidende Vorteile: Aktualität und Quellen-Transparenz. Sobald ein Dokument in der
Wissensdatenbank aktualisiert wird, nutzt der Agent sofort die neue Version, ohne dass eine Zeile Code geändert werden
muss. Zudem liefert der Agent stets die Referenz zur Quelle mit. Ein Nutzer muss nicht blind vertrauen, sondern kann
verifizieren, aus welchem Abschnitt welcher Richtlinie die Information stammt. Technisch wird dies durch semantische
Suche und Re-Ranking-Modelle unterstützt, wobei spezialisierte Events (`RetrieverEvent`) genau protokollieren, welche
Dokumente für eine Antwort herangezogen wurden.

## Die menschliche Kontrollinstanz (Human-in-the-Loop)

Trotz aller Automatisierung gibt es Entscheidungspunkte, die nicht vollständig an eine Maschine delegiert werden dürfen
– sei es aus ethischen Gründen, zur Qualitätssicherung oder aufgrund regulatorischer Vorschriften (z.B.
Vier-Augen-Prinzip). Ein rein autonomes System, das Aktionen ohne Rücksprache ausführt, stellt in solchen Szenarien ein
Compliance-Risiko dar.

Die Architektur des Swiss AI Hub integriert daher das **Human-in-the-Loop (HITL)** Muster als native Kernfunktion. Ein
Agenten-Workflow kann so konfiguriert werden, dass er an kritischen Punkten seine Ausführung technisch pausiert
(«suspendiert»). Der gesamte Zustand des Agenten – sein Kontext, die bisher gesammelten Daten und der geplante nächste
Schritt – wird sicher persistiert. Das System generiert daraufhin über ein `HumanInTheLoopRequestEvent` eine Aufgabe für
einen menschlichen Benutzer.

Erst wenn die autorisierte Person die Aktion genehmigt, korrigiert oder ablehnt, wird der Prozess fortgesetzt.
Bemerkenswert ist hierbei die zeitliche Entkopplung: Die Wartezeit kann Sekunden, Stunden oder Tage betragen, ohne dass
Systemressourcen blockiert werden. Das System nimmt den Arbeitsprozess exakt dort wieder auf, wo er unterbrochen wurde.
Damit wird revisionssicher im Audit-Trail dokumentiert, wer wann welche Entscheidung der KI freigegeben hat.

## Orchestrierung und Interoperabilität

Komplexe Geschäftsprobleme lassen sich selten von einem einzelnen Generalisten lösen. Analog zu menschlichen Teams setzt
der Swiss AI Hub auf die Kollaboration spezialisierter Agenten. Ein Orchestrierungs-Agent kann Aufgaben an Sub-Agenten
delegieren («Agent-to-Agent Delegation»).

Das System unterstützt dabei komplexe Muster wie **Fan-Out/Fan-In**, bei dem ein Orchestrator eine Aufgabe in mehrere
parallele Teilaufgaben zerlegt (z.B. die gleichzeitige Analyse von fünf Vertragsdokumenten durch fünf parallele
Instanzen eines Analyse-Agenten) und die Ergebnisse anschliessend aggregiert. Ein spezifischer Anwendungsfall ist der
**Expert Asking Agent**: Stösst ein RAG-Agent an seine Grenzen, halluziniert er keine Antwort, sondern eskaliert den
Fall via Slack oder Teams an einen menschlichen Experten. Die Antwort des Experten fliesst automatisch in die
Wissensdatenbank zurück, wodurch implizites Kopf-Wissen in explizites Unternehmenswissen umgewandelt wird.

Um nicht in einem geschlossenen System gefangen zu sein, unterstützt der Swiss AI Hub zudem offene Standards für die
Interoperabilität. Während das interne Protokoll die Sicherheit der Plattform garantiert, ermöglicht die Unterstützung
des **Model Context Protocol (MCP)** die standardisierte Anbindung externer Tools und Datenquellen. Ein Agent kann so
über MCP-Adapter sicher auf externe APIs zugreifen, ohne dass die interne Sicherheitsarchitektur kompromittiert wird.

## Qualitätssicherung durch Guards und automatisiertes Testen

Vertrauen in KI entsteht durch die Abwesenheit von Fehlern. Um das Risiko von Halluzinationen zu minimieren,
implementiert die Plattform ein mehrschichtiges System von **Guards (Schutzmechanismen)**.

Bevor eine Anfrage bearbeitet wird, validieren Eingangs-Guards («Topic Adherence»), ob die Frage in den
Zuständigkeitsbereich des Agenten fällt. Noch kritischer ist die Prüfung der Ausgabe: Der **Context Sufficiency Guard**
analysiert bei RAG-Anfragen, ob die gefundenen Dokumente tatsächlich ausreichen, um die Frage zu beantworten. Ist die
Faktenlage zu dünn, wird die Antwort unterdrückt. Ergänzend prüfen Ausgangs-Guards auf sensible Daten (PII) und
schwärzen diese bei Bedarf («Redaction»), selbst wenn der Agent berechtigten Zugriff auf das Quelldokument hatte.

Qualitätssicherung beginnt jedoch bereits vor dem Betrieb. Mit dem **AgentTestRunner** bietet die Plattform eine
Umgebung für **Behavior-Driven Development (BDD)**. Entwickler können Test-Szenarien in natürlicher Sprache definieren
(z.B. «Wenn der Nutzer nach X fragt, muss der Agent Y tun»). Diese Tests laufen automatisiert ab und verifizieren, dass
der Agent deterministisch reagiert, bevor er produktiv geschaltet wird. Dies verschiebt die Kontrolle von der reaktiven
Überwachung hin zur proaktiven Garantie von Verhaltensweisen.
