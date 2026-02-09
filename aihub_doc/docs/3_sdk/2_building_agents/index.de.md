```markdown
---
title: Agents entwickeln
source_sha: "c2620f974ef391b611e915afd873da77a434df91bd7891ba2160236761bf0045"
---

# Agents mit dem AI-Hub SDK entwickeln

Ein Agent im Schweizer AI-Hub ist ein Workflow, der durch eine Reihe von Schritten definiert wird, die Ereignisse verarbeiten. Agents können mit Benutzern interagieren, externe Services aufrufen und sich mit anderen Agents koordinieren, um komplexe Aufgaben auszuführen.

Diese Dokumentation führt Sie durch die Architektur, Muster und Best Practices zum Entwickeln robuster und skalierbarer Agents.

::: warning
Bevor Sie beginnen, schließen Sie bitte das [Einrichten der Entwicklungsumgebung](../1_quick_start/1_dev_environment_setup/) ab und erstellen Sie [Ihren ersten Agent](../1_quick_start/3_your_first_agent/).
:::

## Inhalt

Diese Anleitung ist so strukturiert, dass sie Ihr Wissen schrittweise aufbaut:

1.  [**Agenten-Grundlagen**](./1_agent_fundamentals/) - Die Kernarchitektur, einschließlich Ereignissen, Schritten und Konfiguration.
2.  [**Kernmuster**](./2_core_patterns/) - Wesentliche Workflow-Muster wie bedingte Logik, Schleifen und Zustandsmanagement.
3.  [**Human in the Loop**](./3_human_in_the_loop/) - Entwicklung interaktiver Workflows, die menschliche Genehmigung oder Eingabe erfordern.
4.  [**Multi-Agenten-Systeme**](./4_multi_agent_systems/) - Koordination mehrerer Agents zur Lösung komplexer Probleme.
5.  [**Speicher**](./5_memory/) - Hinzufügen von persistentem Speicher zu Ihren Agents für Benutzerpräferenzen und Organisationswissen.
6.  [**Testen und Debugging**](./6_testing_and_debugging/) - Best Practices zur Gewährleistung der Zuverlässigkeit und Korrektheit Ihres Agents.
7.  [**Produktions-Deployment**](./7_production_deployment/) - Richtlinien für das Packen und Deployen Ihres Agents.
8.  [**Agent-Observability**](./8_agent_observation/) - Überwachung des Verhaltens und der Leistung Ihres Agents mit integriertem Tracing.
9.  [**Konfigurierbare Agent-Formulare**](./8_configurable_agents/) - Bearbeitung der Agent-Konfiguration über die Admin UI mithilfe des Form Duality Pattern.

## Kernprinzipien des SDK

Das SDK basiert auf einigen Kernprinzipien, um die Entwicklung intuitiv und skalierbar zu gestalten:

-   **Ereignisgesteuert von Natur aus**: Agents reagieren auf einen Strom von Ereignissen. Diese asynchrone, nachrichtenbasierte Architektur macht Workflows dynamisch und widerstandsfähig.
-   **Deklarative Workflows**: Sie definieren, *was* jeder Schritt mit dem `@step`-Decorator tut. Das SDK kümmert sich automatisch um das *Wie* der Ereignisweiterleitung und der Verbindung Ihrer Schritte.
-   **Verwalteter Zustand**: Verwalten Sie Konversationsspeicher und Laufzeitdaten mühelos mit injizierbaren `RunContext`- und `ThreadContext`-Objekten, die von einem verteilten Speicher unterstützt werden.
-   **Für die Produktion entwickelt**: Mit streng typisierter Konfiguration, einem dedizierten Test-Framework und integrierter Observability.

## Der Entwicklungs-Workflow

Das Erstellen eines hochwertigen Agents durchläuft typischerweise diese vier Phasen:

::: tip
Ein zentrales Designprinzip ist, dass jeder Agent eine Aufgabe gut erledigen sollte. Komplexe Probleme lassen sich am besten durch die Koordination mehrerer spezialisierter Agents lösen.
:::

1.  **Entwerfen Sie Ihren Workflow**: Skizzieren Sie den Zweck Ihres Agents, die Ereignisse, die er verarbeiten wird, und die Abfolge der Schritte, die er zur Erreichung seines Ziels unternehmen wird.
2.  **Implementieren Sie die Kernlogik**: Schreiben Sie Ihre `Agent`-Klasse, definieren Sie ihre streng typisierte `AgentConfig` und implementieren Sie die `@step`-Methoden, die Ereignisse transformieren.
3.  **Testen und Debuggen**: Verwenden Sie den `AgentTestRunner` für Unit-Tests und ein Tracing-Tool wie Phoenix, um den Ereignisfluss durch Ihren Agent visuell zu debuggen.
4.  **Deployen und Überwachen**: Packen Sie Ihren Agent und deployen Sie ihn im AI-Hub, wo seine Leistung und sein Verhalten in Echtzeit überwacht werden können.

## Nächste Schritte

Beginnen Sie mit den [Agenten-Grundlagen](./1_agent_fundamentals/), um die Kernarchitektur zu verstehen, und erkunden Sie anschließend die spezifischen Muster und Techniken in den folgenden Abschnitten.
```
