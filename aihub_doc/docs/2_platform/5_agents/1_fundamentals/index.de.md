---
title: Grundlagen von Agents
source_sha: 621b31e7ab5304a99327778f65077a1dbf06981c01c53e9385ac6053d883998a
---

# Grundlagen von Agents

Agents nutzen eine ereignisgesteuerte Architektur. Benutzer können über Chat-Schnittstellen interagieren oder Agents
können autonom ausgeführt werden. Workflows, Kontextverwaltung und Ereignisbehandlung laufen im Hintergrund ab.

## Strukturierte Workflows

Jeder Agent folgt einem vordefinierten Workflow, der seine genaue Abfolge von Operationen festlegt. Anstatt einem Agent
Tools zu geben und ihn entscheiden zu lassen, wie er diese verwendet, legen Workflows jeden Schritt fest, den der Agent
ausführt.

Workflows bieten:

- Transparenz: Entwickler und Compliance-Beauftragte können die Workflow-Definition lesen und verstehen, was der Agent
  tut
- Testbarkeit: Jeder Schritt kann unabhängig entwickelt und getestet werden
- Kontrolle: Der Agent kann nicht auf unautorisierte Daten zugreifen oder Aktionen außerhalb seines Workflows ausführen

Schritte können bei Bedarf Sprachmodelle für Argumentations- und Natural-Language-Aufgaben verwenden, aber viele
Schritte führen deterministische Operationen wie Datenvalidierung, Formatierung oder bedingtes Routing ohne
LLM-Beteiligung aus. Der Workflow steuert den gesamten Ausführungspfad.

## Kontextverwaltung

Agents verwenden drei Kontextebenen zur Zustandsverwaltung:

**Thread-Kontext** speichert den persistenten Zustand über mehrere Agentenläufe innerhalb desselben Threads. Ein Thread
stellt eine kontinuierliche Interaktionssitzung dar – für Chat-Agents ist dies eine Konversation; für autonome Agents
ist es eine Reihe verwandter Ausführungen. Wenn Sie zu einer gestern begonnenen Konversation zurückkehren, ermöglicht
der Thread-Kontext dem Agenten, sich an frühere Austausche zu erinnern. Dieser Kontext hat eine Gültigkeitsdauer von 30
Tagen. Die Zugriffskontrolle wird auf dieser Ebene angewendet.

**Display-Kontext** verwaltet, was in der Benutzeroberfläche erscheint. Er gruppiert Aktionen, um sie als eine einzige
Interaktion darzustellen. Wenn Agents zusammenarbeiten, steuert der primäre Agent, ob die Arbeit des Sub-Agenten dem
Benutzer angezeigt wird oder verborgen bleibt.

**Run-Kontext** enthält temporäre Daten für einen einzelnen Agentenlauf. Er enthält Zwischenberechnungen und
zwischengespeicherte Daten für diese spezifische Ausführung. Dieser Kontext läuft nach 30 Tagen ab, ist aber zwischen
verschiedenen Läufen isoliert.

## Ereignisgesteuerte Architektur

Agents agieren innerhalb eines Ökosystems von Komponenten, die über asynchrone Nachrichten auf einem Message Bus (NATS)
kommunizieren.

Vier Beteiligte:

**Agent**: Führt die in seinem Workflow definierte Geschäftslogik aus. Empfängt Anweisungen und erzeugt Ergebnisse und
Telemetriedaten.

**API Gateway**: Authentifiziert Benutzer, übersetzt HTTP-Anfragen in interne Ereignisse und streamt Agent-Antworten
zurück an die Benutzeroberfläche.

**Frontend**: Empfängt die Agent-Ausgabe und rendert sie in Echtzeit als Streaming-Text und UI-Elemente.

**Process Orchestrator**: Verwaltet Multi-Agent-Workflows, indem er überwacht, wann ein Agent abgeschlossen ist, und den
nächsten Beteiligten auslöst.

Diese entkoppelte Architektur verhindert, dass Probleme in einer Komponente andere beeinträchtigen. Eine Verlangsamung
im Frontend kann den Workflow eines Agenten nicht zum Absturz bringen.

## Kollaborationsmuster

### Human-in-the-Loop

Agent-Workflows können pausieren, um menschliche Eingaben anzufordern. Der Workflow erstellt eine Aufgabe in der
Benutzeroberfläche des Benutzers mit Kontext und Auswahlmöglichkeiten. Der Workflow bleibt pausiert (Minuten, Stunden
oder Tage), bis der Benutzer antwortet, und setzt dann die Ausführung fort.

Hauptmerkmale:

- Kontexterhaltung: Der Workflow wird genau an der Stelle fortgesetzt, an der er pausiert wurde, mit vollständiger
  Erinnerung an Zwischenergebnisse
- Audit-Trail: Jede Interaktion (Frage, Antwortender, Entscheidung, Zeitstempel) wird protokolliert
- Anwendungsfälle: Regulatorische Genehmigungen, Qualitätssicherungsprüfungen, mehrdeutige Situationen, die Klärung
  erfordern, Zustimmungs-Workflows

### Agent-zu-Agent-Delegation

Ein primärer Agent kann Aufgaben an spezialisierte Agents delegieren. Zum Beispiel kann ein Dokumentenanfrage-Agent, der
eine komplexe Rechtsfrage erhält, an einen Rechtskonformitäts-Agent delegieren.

Vorteile:

- Wiederverwendbarkeit: Erstellen Sie fokussierte Agents für spezifische Aufgaben (Entitätsextraktion, PII-Erkennung,
  Compliance-Prüfung) und orchestrieren Sie diese für größere Probleme
- Isolation: Der delegierte Agent läuft in seinem eigenen Workflow und kann nicht auf den internen Zustand des primären
  Agenten zugreifen
- Sichtbarkeitskontrolle: Der primäre Agent steuert den Display-Kontext und kann die Delegation dem Benutzer anzeigen
  oder verbergen
- Skalierbarkeit: Hochleistungsfähige spezialisierte Agents können unabhängig skalieren
