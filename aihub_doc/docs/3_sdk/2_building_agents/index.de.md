---
title: Agents entwickeln
source_sha: "a9d6eff4ad7b747efc149cbfe989d7c6d5abc02c6bd960728b4cff0db0515b37"
---

# Agents entwickeln mit dem AI-Hub SDK

Ein Agent im Swiss AI-Hub ist ein Workflow, der durch eine Reihe von Schritten definiert ist, die Ereignisse verarbeiten. Agents können mit Benutzern interagieren, externe Services aufrufen und sich mit anderen Agents koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices für die Entwicklung robuster und skalierbarer Agents.

::: warning
Bevor Sie beginnen, schließen Sie bitte die [Einrichtung der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie [Ihren ersten Agenten](../1_quick_start/3_your_first_agent/).
:::

## Inhalt

Dieser Leitfaden ist so strukturiert, dass er Ihr Wissen schrittweise aufbaut:

1.  [**Agent-Grundlagen**](./1_agent_fundamentals/) - Die Kernarchitektur, einschließlich Ereignissen, Schritten und Konfiguration.
2.  [**Kernmuster**](./2_core_patterns/) - Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und State Management.
3.  [**Human-in-the-Loop**](./3_human_in_the_loop/) - Aufbau interaktiver Workflows, die menschliche Genehmigung oder Eingaben erfordern.
4.  [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) - Koordination mehrerer Agents zur Lösung komplexer Probleme.
5.  [**Speicher**](./5_memory/) - Hinzufügen von persistentem Speicher zu Ihren Agents für Benutzerpräferenzen und organisatorisches Wissen.
6.  [**Testen und Debugging**](./6_testing_and_debugging/) - Best Practices, um sicherzustellen, dass Ihr Agent zuverlässig und korrekt ist.
7.  [**Produktions-Deployment**](./7_production_deployment/) - Richtlinien für das Packaging und Deployment Ihres Agents.
8.  [**Agent-Observability**](./8_agent_observation/) - Überwachung des Verhaltens und der Leistung Ihres Agents mit integriertem Tracing.

## Schlüsselprinzipien des SDK

Das SDK wurde um einige Kernprinzipien herum entwickelt, um die Entwicklung intuitiv und skalierbar zu gestalten:

-   **Event-Driven by Nature**: Agents reagieren auf einen Strom von Ereignissen. Diese asynchrone, Nachrichten-basierte Architektur macht Workflows dynamisch und resilient.
-   **Deklarative Workflows**: Sie definieren, *was* jeder Schritt tut, indem Sie den `@step`-Decorator verwenden. Das SDK kümmert sich automatisch um das *Wie* des Routings von Ereignissen und der Verbindung Ihrer Schritte.
-   **Managed State**: Verwalten Sie Konversationsgedächtnis und Laufzeitdaten mühelos mit injizierbaren `RunContext`- und `ThreadContext`-Objekten, die durch einen verteilten Speicher unterstützt werden.
-   **Für die Produktion entwickelt**: Mit stark typisierter Konfiguration, einem dedizierten Test-Framework und integrierter Observability.

## Der Entwicklungs-Workflow

Der Aufbau eines qualitativ hochwertigen Agents folgt typischerweise diesen vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme werden am besten durch die Koordination mehrerer spezialisierter Agents gelöst.
:::

1.  **Designen Sie Ihren Workflow**: Skizzieren Sie den Zweck Ihres Agents, die Ereignisse, die er verarbeiten wird, und die Abfolge der Schritte, die er unternehmen wird, um sein Ziel zu erreichen.
2.  **Implementieren Sie die Kernlogik**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie ihre stark typisierte `AgentConfig` und implementieren Sie die `@step`-Methoden, die Ereignisse transformieren.
3.  **Testen und Debuggen**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Phoenix, um den Ereignisfluss durch Ihren Agent visuell zu debuggen.
4.  **Deployen und Überwachen**: Packen Sie Ihren Agent und deployen Sie ihn im AI-Hub, wo seine Leistung und sein Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agent-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden Sie dann die spezifischen Muster und Techniken in den folgenden Abschnitten.
