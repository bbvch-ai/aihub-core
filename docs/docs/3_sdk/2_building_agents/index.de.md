---
title: Agents entwickeln
source_sha: 141793b3734f1d467124010619f29e2418bb6f44f5c4549ed1c9e8d8b49b9720
---

# Agents mit dem Swiss AI Hub SDK entwickeln

Ein Agent im Swiss AI Hub ist ein Workflow, der durch eine Reihe von Schritten definiert ist, die Ereignisse
verarbeiten. Agents können mit Benutzern interagieren, externe Services aufrufen und sich mit anderen Agents
koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices für die Entwicklung robuster und
skalierbarer Agents.

::: warning
Bevor Sie beginnen, schließen Sie bitte das
[Einrichten der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie
[Ihren ersten Agent](../1_quick_start/3_your_first_agent/).
:::

## Inhalt dieses Leitfadens

Dieser Leitfaden ist so strukturiert, dass er Ihr Wissen schrittweise aufbaut:

01. [**Agent-Grundlagen**](./1_agent_fundamentals/) - Die Kernarchitektur, einschließlich Events, Schritten und
    Konfiguration.
02. [**Kernmuster**](./2_core_patterns/) - Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und
    Zustandsverwaltung.
03. [**Human in the Loop**](./3_human_in_the_loop/) - Erstellung interaktiver Workflows, die menschliche Genehmigung
    oder Eingabe erfordern.
04. [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) - Koordination mehrerer Agents zur Lösung komplexer Probleme.
05. [**Speicher**](./5_memory/) - Hinzufügen von persistentem Speicher zu Ihren Agents für Benutzerpräferenzen und
    Organisationswissen.
06. [**Testen und Debugging**](./6_testing_and_debugging/) - Best Practices, um die Zuverlässigkeit und Korrektheit
    Ihres Agents sicherzustellen.
07. [**Produktions-Deployment**](./7_production_deployment/) - Richtlinien für das Packaging und Deployment Ihres
    Agents.
08. [**Agent-Beobachtung**](./8_agent_observation/) - Überwachung des Verhaltens und der Performance Ihres Agents mit
    integriertem Tracing.
09. [**Konfigurierbare Agent-Formulare**](./8_configurable_agents/) - Bearbeitbare Agent-Konfiguration über die Admin UI
    mithilfe des Form Duality Pattern.
10. [**Ausführungsmodell**](./9_execution_model/) - Wie der Dispatcher Schritte ausführt, Synchronisations-Primitive,
    Anti-Patterns und Fehlerbehebung.
11. [**Event-Referenz**](./10_events_reference/) - Vollständige Event-Hierarchie, Auswahl des richtigen Basis-Events und
    Katalog verfügbarer Events.

## Kernprinzipien des SDK

Das SDK basiert auf einigen Kernprinzipien, um die Entwicklung intuitiv und skalierbar zu gestalten:

- **Ereignisgesteuert von Natur aus**: Agents reagieren auf einen Strom von Ereignissen. Diese asynchrone,
  nachrichtenbasierte Architektur macht Workflows dynamisch und resilient.
- **Deklarative Workflows**: Sie definieren, *was* jeder Schritt mithilfe des `@step`-Decorators tut. Das SDK kümmert
  sich automatisch darum, *wie* Events geroutet und Ihre Schritte miteinander verbunden werden.
- **Verwalteter Zustand**: Verwalten Sie Gesprächsspeicher und Laufzeitdaten mühelos mit injizierbaren `RunContext`- und
  `ThreadContext`-Objekten, die durch einen verteilten Speicher unterstützt werden.
- **Für die Produktion gebaut**: Mit stark typisierter Konfiguration, einem dedizierten Test-Framework und integrierter
  Observability.

## Der Entwicklungs-Workflow

Der Aufbau eines qualitativ hochwertigen Agents folgt typischerweise diesen vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme lassen sich am
besten durch die Koordination mehrerer spezialisierter Agents lösen.
:::

1. **Workflow entwerfen**: Skizzieren Sie den Zweck Ihres Agents, die Events, die er verarbeiten wird, und die Abfolge
   der Schritte, die er unternehmen wird, um sein Ziel zu erreichen.
2. **Kernlogik implementieren**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie ihre stark typisierte `AgentConfig`
   und implementieren Sie die `@step`-Methoden, die Events transformieren.
3. **Testen und Debuggen**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Langfuse, um den
   Fluss von Events durch Ihren Agent visuell zu debuggen.
4. **Deployen und Überwachen**: Packen Sie Ihren Agent und deployen Sie ihn im Swiss AI Hub, wo seine Performance und
   sein Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agent-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden Sie
dann die spezifischen Muster und Techniken in den folgenden Abschnitten.
