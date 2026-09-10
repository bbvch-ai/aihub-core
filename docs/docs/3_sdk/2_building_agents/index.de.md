---
title: Agenten erstellen
source_sha: e54a8455991a3ea256b915b33b9bd0321a010adbbcd1ec20ca1003527ee15725
---

# Agenten mit dem Swiss AI Hub SDK erstellen

Ein Agent im Swiss AI Hub ist ein Workflow, der durch eine Reihe von Schritten definiert ist, die Ereignisse
verarbeiten. Agents können mit Benutzern interagieren, externe Services aufrufen und sich mit anderen Agents
koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices für die Entwicklung robuster und
skalierbarer Agents.

::: warning
Bevor Sie beginnen, schliessen Sie bitte die
[Einrichtung der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie
[Ihren ersten Agenten](../1_quick_start/3_your_first_agent/).
:::

## Inhalt

Diese Anleitung ist so strukturiert, dass sie Ihr Wissen schrittweise aufbaut:

01. [**Agenten-Grundlagen**](./1_agent_fundamentals/) - Die Kernarchitektur, einschliesslich Ereignissen, Schritten und
    Konfiguration.
02. [**Kernmuster**](./2_core_patterns/) - Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und
    Zustandsverwaltung.
03. [**Human in the Loop**](./3_human_in_the_loop/) - Aufbau interaktiver Workflows, die menschliche Genehmigung oder
    Eingabe erfordern.
04. [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) - Koordination mehrerer Agents zur Lösung komplexer Probleme.
05. [**Speicher**](./5_memory/) - Hinzufügen von persistentem Speicher zu Ihren Agents für Benutzerpräferenzen und
    organisatorisches Wissen.
06. [**Testen und Debugging**](./6_testing_and_debugging/) - Best Practices zur Sicherstellung der Zuverlässigkeit und
    Korrektheit Ihres Agents.
07. [**Produktions-Deployment**](./7_production_deployment/) - Richtlinien für das Packaging und Deployment Ihres
    Agents.
08. [**Agenten-Beobachtung**](./8_agent_observation/) - Überwachung des Verhaltens und der Leistung Ihres Agents mit
    integriertem Tracing.
09. [**Konfigurierbare Agentenformulare**](./8_configurable_agents/) - Die Agentenkonfiguration über die Admin UI mit
    dem Form Duality Pattern bearbeitbar machen.
10. [**Ausführungsmodell**](./9_execution_model/) - Wie der Dispatcher Schritte ausführt, Synchronisations-Primitive,
    Anti-Patterns und Fehlerbehebung.
11. [**Ereignisreferenz**](./10_events_reference/) - Vollständige Ereignishierarchie, Auswahl des richtigen
    Basisereignisses und verfügbarer Ereigniskatalog.
12. [**Verwendung von MCP Tools**](./11_using_mcp_tools/) - Agents mit externen MCP-Servern verbinden, um deren Tools
    aufzurufen.

## Schlüsselprinzipien des SDKs

Das SDK wurde um einige Kernprinzipien herum entwickelt, um die Entwicklung intuitiv und skalierbar zu gestalten:

- **Ereignisgesteuert**: Agents reagieren auf einen Ereignisstrom. Diese asynchrone, nachrichtenbasierte Architektur
  macht Workflows dynamisch und resilient.
- **Deklarative Workflows**: Sie definieren, *was* jeder Schritt mithilfe des `@step`-Decorators tut. Das SDK kümmert
  sich automatisch um das *Wie* des Routings von Ereignissen und der Verknüpfung Ihrer Schritte.
- **Verwalteter Zustand**: Verwalten Sie den Konversationsspeicher und Laufzeitdaten mühelos mit injizierbaren
  `RunContext`- und `ThreadContext`-Objekten, die durch einen verteilten Speicher unterstützt werden.
- **Für die Produktion entwickelt**: Mit stark typisierter Konfiguration, einem dedizierten Test-Framework und
  integrierter Observability.

## Der Entwicklungsworkflow

Der Aufbau eines hochwertigen Agenten durchläuft typischerweise diese vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme lassen sich am
besten durch die Koordination mehrerer spezialisierter Agents lösen.
:::

1. **Entwerfen Sie Ihren Workflow**: Skizzieren Sie den Zweck Ihres Agents, die Ereignisse, die er verarbeiten wird, und
   die Abfolge der Schritte, die er zur Erreichung seines Ziels unternehmen wird.
2. **Implementieren Sie die Kernlogik**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie ihre stark typisierte
   `AgentConfig` und implementieren Sie die `@step`-Methoden, die Ereignisse transformieren.
3. **Testen und Debuggen**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Langfuse, um den
   Ereignisfluss durch Ihren Agenten visuell zu debuggen.
4. **Deployen und Überwachen**: Packen Sie Ihren Agenten und deployen Sie ihn im Swiss AI Hub, wo seine Leistung und
   sein Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agenten-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden
Sie dann die spezifischen Muster und Techniken in den folgenden Abschnitten.
