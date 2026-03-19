---
title: Agents entwickeln
source_sha: "f0e52bce851daa740f2f72de674fd3eac8c1c97c63510f3fefca6031682a2f24"
---

# Agents mit dem Swiss AI Hub SDK entwickeln

Ein Agent im Swiss AI Hub ist ein Workflow, der durch eine Reihe von Schritten definiert wird, die Ereignisse verarbeiten. Agents können mit Benutzern interagieren, externe Services aufrufen und sich mit anderen Agents koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices zum Aufbau robuster und skalierbarer Agents.

::: warning
Bevor Sie beginnen, schließen Sie bitte die [Einrichtung der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie [Ihren ersten Agenten](../1_quick_start/3_your_first_agent/).
:::

## Inhalt

Dieser Leitfaden ist so strukturiert, dass er Ihr Wissen schrittweise aufbaut:

01. [**Agent-Grundlagen**](./1_agent_fundamentals/) - Die Kernarchitektur, einschließlich Ereignissen, Schritten und
    Konfiguration.
02. [**Kernmuster**](./2_core_patterns/) - Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und Zustandsverwaltung.
03. [**Human-in-the-Loop**](./3_human_in_the_loop/) - Aufbau interaktiver Workflows, die menschliche Genehmigung oder
    Eingaben erfordern.
04. [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) - Koordination mehrerer Agents zur Lösung komplexer Probleme.
05. [**Speicher**](./5_memory/) - Hinzufügen von persistentem Speicher zu Ihren Agents für Benutzerpräferenzen und
    organisatorisches Wissen.
06. [**Testen und Debuggen**](./6_testing_and_debugging/) - Best Practices zur Sicherstellung der Zuverlässigkeit und
    Korrektheit Ihres Agenten.
07. [**Produktions-Deployment**](./7_production_deployment/) - Richtlinien für das Packaging und Deployment Ihres Agenten.
08. [**Agent-Beobachtung**](./8_agent_observation/) - Überwachung des Verhaltens und der Performance Ihres Agenten mit
    integriertem Tracing.
09. [**Konfigurierbare Agenten-Formulare**](./8_configurable_agents/) - Bearbeitbare Agentenkonfiguration über die
    Admin-Benutzeroberfläche mithilfe des Form Duality Patterns.
10. [**Ausführungsmodell**](./9_execution_model/) - Wie der Dispatcher Schritte ausführt, Synchronisations-Primitive,
    Anti-Muster und Fehlerbehebung.
11. [**Ereignisreferenz**](./10_events_reference/) - Vollständige Ereignishierarchie, Auswahl des richtigen
    Basisereignisses und Katalog der verfügbaren Ereignisse.

## Schlüsselprinzipien des SDK

Das SDK ist um einige Kernprinzipien herum konzipiert, um die Entwicklung intuitiv und skalierbar zu gestalten:

- **Ereignisgesteuert von Natur aus**: Agents reagieren auf einen Strom von Ereignissen. Diese asynchrone,
  nachrichtenbasierte Architektur macht Workflows dynamisch und widerstandsfähig.
- **Deklarative Workflows**: Sie definieren, *was* jeder Schritt mithilfe des `@step`-Decorators tut. Das SDK kümmert
  sich automatisch um das *Wie* des Routings von Ereignissen und der Verbindung Ihrer Schritte.
- **Verwalteter Zustand**: Verwalten Sie den Konversationsspeicher und Laufzeitdaten mühelos mit injizierbaren
  `RunContext`- und `ThreadContext`-Objekten, die durch einen verteilten Speicher unterstützt werden.
- **Für die Produktion entwickelt**: Mit stark typisierter Konfiguration, einem dedizierten Test-Framework und
  integrierter Observability.

## Der Entwicklungs-Workflow

Der Aufbau eines qualitativ hochwertigen Agenten folgt typischerweise diesen vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme lassen sich am
besten durch die Koordination mehrerer spezialisierter Agents lösen.
:::

1.  **Entwerfen Sie Ihren Workflow**: Skizzieren Sie den Zweck Ihres Agenten, die Ereignisse, die er verarbeiten wird,
    und die Abfolge der Schritte, die er unternehmen wird, um sein Ziel zu erreichen.
2.  **Implementieren Sie die Kernlogik**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie deren stark typisierte
    `AgentConfig` und implementieren Sie die `@step`-Methoden, die Ereignisse transformieren.
3.  **Testen und Debuggen**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Langfuse, um
    den Ereignisfluss durch Ihren Agenten visuell zu debuggen.
4.  **Deployen und Überwachen**: Packen Sie Ihren Agenten und deployen Sie ihn im Swiss AI Hub, wo seine Performance und
    sein Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agent-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden Sie
dann die spezifischen Muster und Techniken in den folgenden Abschnitten.
