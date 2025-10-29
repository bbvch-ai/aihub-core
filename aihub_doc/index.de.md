---
# https://vitepress.dev/reference/default-theme-home-page
layout: home
source_sha: "0abcfeb4fc4dfc2b85435942f8d22b0a3a2542283ee4c191dc2dd58a0fa682ce"

hero:
  name: Swiss AI Hub
  text: Die offene KI-Plattform, die Sie besitzen und kontrollieren
  tagline: Komplette Infrastruktur für produktive KI. Deployment in Ihrem Rechenzentrum. Vertrauensvoll entwickeln. Ihre Daten bleiben in der Schweiz.
  actions:
    - theme: brand
      text: Schnellstart
      link: /de/docs/2_platform/1_quick_start/
    - theme: alt
      text: Plattformübersicht
      link: /de/docs/2_platform/2_architecture/1_core_components/
    - theme: alt
      text: Warum Swiss AI Hub
      link: /de/docs/1_vision_and_positioning/1_introduction

features:
  - title: KI in 30 Minuten deployen
    details: Ein Befehl startet alles. LLM-Gateway, Vektordatenbanken, Chat-Oberfläche, Authentifizierung, Monitoring. Vorgefertigte Agenten funktionieren sofort. Keine Cloud-Konten, keine komplexe Einrichtung.
  - title: Ihre Daten bleiben bei Ihnen
    details: Betreiben Sie alles On-Premise oder in Schweizer Rechenzentren. Lokale LLMs bedeuten, dass sensible Daten Ihr Netzwerk niemals verlassen. Sie bestimmen, wo jedes Byte verarbeitet und gespeichert wird.
  - title: Sehen Sie genau, was KI tut
    details: Jede Entscheidung ist nachvollziehbar. Jeder Workflow-Schritt ist sichtbar. Jede Kosten werden verfolgt. Wenn KI eine Antwort gibt, können Sie sehen, warum. Vertrauen durch Transparenz, nicht durch Versprechen.
  - title: Entwickeln Sie ohne Infrastruktur-Kopfschmerzen
    details: Authentifizierung, Bereitstellung, Überwachung, Skalierung sind bereits gelöst. Schreiben Sie die Geschäftslogik Ihres Agenten, die Plattform kümmert sich um alles andere. Konzentrieren Sie sich auf das, was Sie einzigartig macht.
  - title: Funktioniert mit dem, was Sie bereits haben
    details: OpenAI-kompatible API verbindet bestehende Tools. Teams- und Slack-Bots erreichen Benutzer dort, wo sie arbeiten. Integration mit SharePoint, FTP und Ihren Systemen über Standardprotokolle.
  - title: Wachsen Sie mit dem Ökosystem
    details: Jede Schweizer Organisation, die die Plattform nutzt, macht sie stärker. Teilen Sie gemeinsame Agenten, halten Sie strategische privat. Arbeiten Sie an der Infrastruktur zusammen, konkurrieren Sie bei Innovationen.
---

<div style="height: 500px"></div>

## FAQ

::: details Wie kann unsere Schweizer Organisation KI einsetzen und dabei alle Daten On-Premise behalten?
Der Swiss AI Hub ist eine **Open-Source KI-Plattform**, die *Sie* bereitstellen und kontrollieren. Er wurde speziell für die **On-Premise-Installation** in Ihrem eigenen Schweizer Rechenzentrum entwickelt. Das bedeutet, Sie können die gesamte KI-Infrastruktur – einschliesslich Sprachmodell-Gateways und Wissensdatenbanken – auf Ihren Servern betreiben und haben so die volle Kontrolle und Datenisolation. Mehr Details finden Sie in unseren [Deployment Options](/aihub-core/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass wir bei der Nutzung von KI die Schweizer Datenschutzgesetze (DSG/nDSG) einhalten?
Die Gewährleistung der **Schweizer Datenhoheit** ist ein Kernprinzip der Swiss AI Hub Community. Da *Sie* die Plattform bereitstellen, entscheiden *Sie*, *wo* sie läuft – entweder auf Ihren eigenen Servern in der Schweiz oder in vertrauenswürdigen Schweizer Rechenzentren. Durch die Nutzung lokaler Large Language Models (LLMs) verbleibt die Verarbeitung sensibler Daten vollständig unter Ihrer Kontrolle, was Ihnen hilft, die **DSG/nDSG-Anforderungen** zu erfüllen. Lesen Sie mehr über unseren Ansatz unter [The Swiss Way: Privacy, Sovereignty, and Transparency](/aihub-core/docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details Was ist eine vertrauenswürdige Open-Source KI-Plattform-Alternative zu grossen Cloud-Anbietern wie Azure AI oder Google Vertex AI?
Der Swiss AI Hub bietet eine **Open-Source-Alternative**, die von einer auf Benutzerkontrolle fokussierten Community entwickelt wird. Die Kerninfrastruktur der Plattform ist unter der Apache 2.0 Lizenz lizenziert, was bedeutet, dass *Sie* Ihre Bereitstellung besitzen. Dies befreit Sie von **Vendor Lock-in** und gibt Ihnen Unabhängigkeit von spezifischen Ökosystemen und unvorhersehbaren Preisstrukturen, die bei grossen Cloud-Anbietern üblich sind. Sehen Sie, wie wir uns vergleichen, in der [Comparison Matrix](/aihub-core/docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/).
:::

::: details Wie können wir sicherstellen, dass KI-Entscheidungen in unserem Schweizer Unternehmen nachvollziehbar und auditierbar sind?
Die Swiss AI Hub Community legt Wert auf **Transparenz für Vertrauen**. Unsere Plattform bietet umfassende Observability-Funktionen. Jeder Schritt, den ein KI-Agent unternimmt, ist sichtbar, Entscheidungen werden mit Kontext protokolliert und Kosten verfolgt. Werkzeuge wie Phoenix ermöglichen die Nachverfolgung jeder Interaktion, sodass Sie immer verstehen können, *warum* eine KI eine bestimmte Antwort gegeben hat, was für **Compliance und Auditierung** entscheidend ist. Entdecken Sie diese Funktionen unter [Auditing & Observability](/aihub-core/docs/2_platform/12_auditing/).
:::

::: details Gibt es einen fertigen KI-Infrastruktur-Stack (Authentifizierung, Monitoring, Vektor-DBs), den wir selbst bereitstellen können?
Ja, der Swiss AI Hub bietet einen **vollständigen, vorintegrierten KI-Infrastruktur-Stack**, den *Sie* bereitstellen. Er bündelt wesentliche Komponenten wie Authentifizierung, Monitoring, verschiedene Datenbanken (einschliesslich Vektordatenbanken für KI), Datenverarbeitungspipelines und Benutzeroberflächen direkt «out-of-the-box». Dies löst viele gängige **Herausforderungen bei der KI-Produktivsetzung** vom ersten Tag an. Erfahren Sie mehr darüber unter [The 'Day 2' Advantage](/aihub-core/docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details Was ist der schnellste Weg, eine sichere, produktionsbereite KI-Plattform in der Schweiz bereitzustellen?
Sie können die gesamte Swiss AI Hub Plattform in etwa **30 Minuten mit einem einzigen Befehl** bereitstellen. Als Open-Source-Plattform, die Sie selbst installieren, enthält sie vorgefertigte Agenten und Schnittstellen, die sofort funktionieren und einen schnellen Mehrwert ohne komplexe Setups bieten. Beginnen Sie mit dem [Quick Start Guide](/aihub-core/docs/2_platform/1_quick_start/).
:::

::: details Wie können unsere Mitarbeitenden sicher auf unternehmensspezifische KI-Hilfe direkt in Microsoft Teams oder Slack zugreifen?
Die Swiss AI Hub Plattform bietet **native Integrationen für Microsoft Teams und Slack**. Dies ermöglicht Ihren Teams, sicher mit KI-Agenten zu interagieren, die Zugriff auf relevantes Unternehmenswissen haben, direkt in den Kollaborationstools, die sie täglich nutzen, was den Arbeitsablauf verbessert. Details finden Sie unter [Slack & Teams Integrations](/aihub-core/docs/2_platform/15_slack_teams_integrations/).
:::

::: details Wie kann unsere Organisation den Zugriff auf und die Nutzung verschiedener KI-Modelle (z.B. GPT-4, Gemini, lokale Modelle) zentral verwalten?
Der Swiss AI Hub enthält einen **integrierten LLM Proxy (LiteLLM)**, der als einheitliches Gateway zu all Ihren konfigurierten KI-Modellen fungiert. Sie können den Modellzugriff zentral verwalten, Anfragen basierend auf Richtlinien intelligent weiterleiten, Kosten über verschiedene Anbieter hinweg verfolgen und sogar Failover-Mechanismen einrichten. Weitere Informationen finden Sie unter [Language Models](/aihub-core/docs/2_platform/13_language_models/).
:::

::: details Wie können wir die Betriebskosten (OPEX) im Zusammenhang mit der Nutzung von KI-Modellen effektiv kontrollieren und vorhersagen?
Unsere Community hat den Swiss AI Hub mit Blick auf **transparente Kostenkontrolle** entwickelt. Der integrierte LLM Proxy verfolgt den Token-Verbrauch für jede Interaktion, pro Benutzer oder Agent. Sie können die KI-Ausgaben in Echtzeit-Dashboards überwachen und Budgets konfigurieren, um unerwartete Kosten zu vermeiden. Erfahren Sie mehr über [Cost Control](/aihub-core/docs/2_platform/14_cost_control/).
:::

::: details Unser Schweizer Unternehmen kann aufgrund strenger Datenschutzbestimmungen keine öffentlichen KI-Cloud-Dienste nutzen. Welche sichere KI-Lösung können wir verwenden?
Der Swiss AI Hub ist hierfür ideal. Als Open-Source-Plattform, die *Sie* bereitstellen, können Sie ihn **vollständig On-Premise** installieren und **lokale, selbst gehostete LLMs** verwenden. Dies stellt sicher, dass absolut keine Daten (Prompts, Antworten, Dokumente) jemals Ihr sicheres Netzwerk verlassen. Überprüfen Sie unsere umfassenden [Security features](/aihub-core/docs/2_platform/18_security/).
:::

::: details Wir haben KI-Prototypen mit Frameworks wie LangChain entwickelt, finden aber die zuverlässige Bereitstellung in der Produktion schwierig. Wie kann der Swiss AI Hub helfen?
Der Swiss AI Hub stellt die notwendige **produktionsreife Infrastruktur** bereit, die Entwicklungsframeworks oft fehlt. Während LangChain hilft, die KI-Logik zu bauen, liefert unsere Plattform die wesentlichen umgebenden Komponenten: robuste Bereitstellungsmechanismen, Unternehmensauthentifizierung, Skalierung, Monitoring und Benutzeroberflächen, die für einen **zuverlässigen Unternehmenseinsatz** benötigt werden. Siehe [Our Solution](/aihub-core/docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details Wie können wir unsere internen Firmendokumente (wie PDFs oder Word-Dateien) sicher nutzen, damit KI-Agenten Fragen dazu beantworten können (RAG)?
Der Swiss AI Hub enthält ein sicheres **Retrieval-Augmented Generation (RAG) System**. Sie konfigurieren automatisierte [Data Pipelines](/aihub-core/docs/2_platform/6_pipelines/), um Dokumente aus Ihren Quellen (wie SharePoint) aufzunehmen. Diese Pipelines verarbeiten die Dokumente sicher und indexieren sie in einer Vektordatenbank, *die Sie besitzen und kontrollieren*, sodass Agenten sicher auf Unternehmenswissen zugreifen können.
:::

::: details Verschiedene Teams in unserer Organisation nutzen unterschiedliche KI-Tools, was zu Silos führt. Wie können wir einen einheitlichen, gesteuerten KI-Ansatz schaffen?
Der Swiss AI Hub kann als Ihre **zentrale, einheitliche KI-Plattform** dienen. Er bietet eine gemeinsame Infrastruktur, auf der alle Teams aufbauen können, gewährleistet konsistente Governance- und Sicherheitsrichtlinien, bietet einheitliches Monitoring und enthält eine [OpenAI-Compatible API](/aihub-core/docs/2_platform/16_api/1_openai_compatible_api/), die die Integration vieler bestehender Tools ermöglicht und so hilft, die **Fragmentierung zu reduzieren**.
:::

::: details Was ist ein effizienter und skalierbarer Weg, um die Aufnahme und Vektor-Einbettung von Tausenden von Firmendokumenten für KI zu handhaben?
Der Swiss AI Hub nutzt **Data Pipelines**, die auf dem robusten Orchestrator Dagster basieren. Diese Pipelines automatisieren den gesamten Workflow: Verbindung zu Ihren Datenquellen, intelligentes Parsen verschiedener Dateiformate, Erstellung semantischer Chunks, Generierung von Vektor-Einbettungen und Indexierung in Ihrer Vektordatenbank (wie Milvus). Details finden Sie im Abschnitt [Pipelines](/aihub-core/docs/2_platform/6_pipelines/).
:::

::: details Können wir eine komplette KI-Plattform vollständig offline in einem Air-Gapped-Netzwerk innerhalb der Schweiz bereitstellen und betreiben?
Ja. Wenn Sie den Swiss AI Hub **On-Premise** bereitstellen und ihn so konfigurieren, dass nur **selbst gehostete Large Language Models (LLMs)** verwendet werden, kann die gesamte Plattform ohne externe Internetverbindung betrieben werden. Dies macht sie geeignet für **Air-Gapped-Umgebungen** mit höchsten Sicherheitsanforderungen. Siehe [Deployment Options](/aihub-core/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass die KI-Agenten vertrauenswürdige Antworten liefern und nicht nur "halluzinieren" oder Dinge erfinden?
Vertrauen ist entscheidend. Swiss AI Hub **Agents** sind darauf ausgelegt, expliziten, definierten Workflows zu folgen. Sie verwenden primär **Retrieval-Augmented Generation (RAG)**, was bedeutet, dass ihre Antworten auf Informationen basieren, die aus *Ihren* verifizierten Firmendokumenten abgerufen wurden. Agenten **zitieren auch ihre Quellen**, und eingebaute "Guardrails" prüfen, ob die abgerufenen Informationen ausreichen, um **zuverlässige, faktenbasierte Antworten** zu gewährleisten. Erfahren Sie mehr über [Agents](/aihub-core/docs/2_platform/5_agents/).
:::

::: details Ist es möglich, dass KI-Agenten auf dieser Plattform bei komplexen Aufgaben Hilfe oder Genehmigungen von menschlichen Experten anfordern?
Ja, unsere Plattform unterstützt **Human-in-the-Loop (HITL)** und **Bot-in-the-Loop (BITL)** Workflows. Ein KI-Agent kann so konzipiert werden, dass er seinen Prozess an einem bestimmten Schritt anhält, eine Anfrage für Input oder Genehmigung an einen benannten menschlichen Experten sendet (zum Beispiel über eine Slack-Nachricht) und dann seine Arbeit nahtlos wieder aufnimmt, sobald der Mensch geantwortet hat. Entdecken Sie [Agent Fundamentals](/aihub-core/docs/3_sdk/2_building_agents/1_agent_fundamentals/), die diese Muster ermöglichen.
:::

::: details Wie verbindet und integriert sich der Swiss AI Hub mit unseren bestehenden Unternehmenssystemen wie SharePoint oder internen Datenbanken?
Die Plattform bietet **flexible Integrationsoptionen**. KI-Agenten können direkte API-Aufrufe an externe Systeme tätigen; externe Systeme können Agenten über die [Agent Interaction API](/aihub-core/docs/2_platform/16_api/2_agent_interaction_api/) der Plattform auslösen; automatisierte Data Pipelines können Wissen aus Quellen wie SharePoint synchronisieren; und Standardprotokolle werden für benutzerdefinierte Verbindungen unterstützt. Siehe [External Integrations](/aihub-core/docs/2_platform/20_external_integrations/).
:::

::: details Wie profitiert das breitere Schweizer KI-Ökosystem von der Nutzung einer Open-Source-Plattform wie dem Swiss AI Hub?
Unser **Ökosystem-Modell** basiert auf Kollaboration. Die Kernplattform ist Open-Source, was es Schweizer Organisationen ermöglicht, ihre Anstrengungen beim Aufbau und der Verbesserung der grundlegenden KI-Infrastruktur zu bündeln. Jeder profitiert von gemeinsamen Fortschritten, sodass einzelne Organisationen ihre Ressourcen auf die Erstellung einzigartiger KI-Anwendungen konzentrieren können, die auf ihre spezifischen Bedürfnisse zugeschnitten sind, was die gesamte KI-Landschaft der Schweiz stärkt. Lesen Sie über [The Ecosystem Model](/aihub-core/docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details Wir sind besorgt über die Komplexität der Einrichtung und Verwaltung einer selbst gehosteten KI-Plattform wie dieser. Ist der Swiss AI Hub schwierig zu betreiben?
Die Swiss AI Hub Community hat die Plattform für eine **vereinfachte Bereitstellung und Verwaltung** konzipiert. Die Installation erfolgt über einen einzigen Befehl, und kritische Infrastrukturherausforderungen wie Authentifizierung, Monitoring und Skalierungskonfiguration sind "out-of-the-box" gelöst. Dies reduziert die betriebliche Komplexität erheblich im Vergleich zum Aufbau einer KI-Infrastruktur von Grund auf oder zur Verwaltung komplexer Cloud-Anbieterdienste. Sehen Sie sich den [Quick Start](/aihub-core/docs/2_platform/1_quick_start/) an.
:::