---
title: Agenten erstellen
source_sha: ea725effe06b9410d295ce1ddbdf699c7b342b123417a62149ab3214d7812bb6
---

# Agenten mit dem AI-Hub SDK erstellen

Ein Agent im Swiss AI-Hub ist ein Workflow, der durch eine Reihe von Schritten definiert ist, die Ereignisse
verarbeiten. Agenten können mit Benutzern interagieren, externe Dienste aufrufen und sich mit anderen Agenten
koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices zum Erstellen robuster und skalierbarer
Agenten.

::: warning
Bevor Sie beginnen, schließen Sie bitte die
[Einrichtung der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie
[Ihren ersten Agenten](../1_quick_start/3_your_first_agent/).
:::

## Inhalt

Dieser Leitfaden ist so strukturiert, dass er Ihr Wissen schrittweise aufbaut:

1. [**Agenten-Grundlagen**](./1_agent_fundamentals/) - Die Kernarchitektur, einschließlich Ereignissen, Schritten und
   Konfiguration.
2. [**Kernmuster**](./2_core_patterns/) - Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und
   Zustandsverwaltung.
3. [**Human in the Loop**](./3_human_in_the_loop/) - Erstellen interaktiver Workflows, die menschliche Genehmigung oder
   Eingabe erfordern.
4. [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) - Koordinierung mehrerer Agenten zur Lösung komplexer Probleme.
5. [**Testen und Debuggen**](./5_testing_and_debugging/) - Best Practices zur Gewährleistung der Zuverlässigkeit und
   Korrektheit Ihres Agenten.
6. [**Produktions-Deployment**](./6_production_deployment/) - Richtlinien zum Paketieren und Deployen Ihres Agenten.
7. [**Agenten-Beobachtung**](./7_agent_observation/) - Überwachung des Verhaltens und der Leistung Ihres Agenten mit
   integriertem Tracing.

## Schlüsselprinzipien des SDK

Das SDK wurde nach einigen Kernprinzipien entwickelt, um die Entwicklung intuitiv und skalierbar zu gestalten:

- **Ereignisgesteuert**: Agenten reagieren auf einen Strom von Ereignissen. Diese asynchrone, nachrichtenbasierte
  Architektur macht Workflows dynamisch und resilient.
- **Deklarative Workflows**: Sie definieren *was* jeder Schritt mithilfe des `@step`-Decorators tut. Das SDK kümmert
  sich automatisch um das *wie* der Ereignisweiterleitung und der Verknüpfung Ihrer Schritte.
- **Verwalteter Zustand**: Verwalten Sie den Konversationsspeicher und Laufzeitdaten mühelos mit injizierbaren
  `RunContext`- und `ThreadContext`-Objekten, die von einem verteilten Speicher unterstützt werden.
- **Für die Produktion entwickelt**: Mit stark typisierter Konfiguration, einem dedizierten Test-Framework und
  integrierter Observability.

## Der Entwicklungs-Workflow

Die Entwicklung eines qualitativ hochwertigen Agenten durchläuft typischerweise diese vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme lassen sich am
besten durch die Koordination mehrerer spezialisierter Agenten lösen.
:::

1. **Entwerfen Sie Ihren Workflow**: Skizzieren Sie den Zweck Ihres Agenten, die Ereignisse, die er verarbeiten wird,
   und die Abfolge der Schritte, die er zur Erreichung seines Ziels unternehmen wird.
2. **Implementieren Sie die Kernlogik**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie ihre stark typisierte
   `AgentConfig` und implementieren Sie die `@step`-Methoden, die Ereignisse transformieren.
3. **Testen und Debuggen**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Phoenix, um den
   Ereignisfluss durch Ihren Agenten visuell zu debuggen.
4. **Deployen und Überwachen**: Paketieren Sie Ihren Agenten und deployen Sie ihn im AI-Hub, wo seine Leistung und sein
   Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agenten-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden
Sie dann die spezifischen Muster und Techniken in den folgenden Abschnitten.
