---
title: Agents entwickeln
source_sha: e4224d6d96b12d8b6ab0b3f5769a7dff32f3873b1b9828063fa26f16d1f9f759
---

# Agents mit dem AI-Hub SDK erstellen

Ein Agent im Swiss AI-Hub ist ein Workflow, der durch eine Reihe von Schritten definiert ist, die Ereignisse
verarbeiten. Agents können mit Benutzern interagieren, externe Services aufrufen und sich mit anderen Agents
koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices für die Entwicklung robuster und
skalierbarer Agents.

::: warning
Bevor Sie beginnen, schließen Sie bitte das
[Einrichten der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie
[Ihren ersten Agent](../1_quick_start/3_your_first_agent/).
:::

## Inhalt

Dieser Leitfaden ist so strukturiert, dass er Ihr Wissen schrittweise aufbaut:

1. [**Agent-Grundlagen**](./1_agent_fundamentals/) – Die Kernarchitektur, einschließlich Ereignissen, Schritten und
   Konfiguration.
2. [**Kernmuster**](./2_core_patterns/) – Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und
   Zustandsverwaltung.
3. [**Human in the Loop**](./3_human_in_the_loop/) – Interaktive Workflows erstellen, die menschliche Genehmigung oder
   Eingabe erfordern.
4. [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) – Mehrere Agents koordinieren, um komplexe Probleme zu lösen.
5. [**Testen und Debugging**](6_testing_and_debugging/) – Best Practices, um die Zuverlässigkeit und Korrektheit Ihres
   Agents sicherzustellen.
6. [**Produktions-Deployment**](7_production_deployment/) – Richtlinien für das Packaging und Deployment Ihres Agents.
7. [**Agent-Beobachtung**](8_agent_observation/) – Überwachung des Verhaltens und der Leistung Ihres Agents mit
   integriertem Tracing.

## Schlüsselprinzipien des SDK

Das SDK basiert auf einigen Kernprinzipien, um die Entwicklung intuitiv und skalierbar zu gestalten:

- **Ereignisgesteuert**: Agents reagieren auf einen Strom von Ereignissen. Diese asynchrone, nachrichtenbasierte
  Architektur macht Workflows dynamisch und resilient.
- **Deklarative Workflows**: Sie definieren, *was* jeder Schritt mithilfe des `@step`-Decorators tut. Das SDK kümmert
  sich automatisch um das *Wie* des Routings von Ereignissen und der Verknüpfung Ihrer Schritte.
- **Verwalteter Zustand**: Verwalten Sie den Konversationsspeicher und Laufzeitdaten mühelos mit injizierbaren
  `RunContext`- und `ThreadContext`-Objekten, die von einem verteilten Speicher unterstützt werden.
- **Für die Produktion gebaut**: Mit stark typisierter Konfiguration, einem dedizierten Testframework und integrierter
  Observability.

## Der Entwicklungsworkflow

Die Entwicklung eines qualitativ hochwertigen Agents durchläuft typischerweise diese vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme lassen sich am
besten durch die Koordination mehrerer spezialisierter Agents lösen.
:::

1. **Gestalten Sie Ihren Workflow**: Skizzieren Sie den Zweck Ihres Agents, die Ereignisse, die er verarbeiten wird, und
   die Abfolge der Schritte, die er zur Erreichung seines Ziels unternehmen wird.
2. **Implementieren Sie die Kernlogik**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie ihre stark typisierte
   `AgentConfig` und implementieren Sie die `@step`-Methoden, die Ereignisse transformieren.
3. **Testen und Debugging**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Phoenix, um den
   Ereignisfluss durch Ihren Agent visuell zu debuggen.
4. **Deployen und Überwachen**: Packen Sie Ihren Agent und deployen Sie ihn im AI-Hub, wo seine Leistung und sein
   Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agent-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden Sie
dann die spezifischen Muster und Techniken in den folgenden Abschnitten.
