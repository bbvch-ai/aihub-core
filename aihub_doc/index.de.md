```yaml
# https://vitepress.dev/reference/default-theme-home-page
layout: home
title: Swiss AI-Hub
source_sha: "c7663d4459db0b5d3a2f3a031cf6a0fb06ddf0312fa92be834c8fd5a663aa626"

hero:
  name: Schweizer AI Hub
  text: Die offene KI-Plattform, die Sie besitzen und kontrollieren
  tagline: Komplette Infrastruktur für produktive KI. Deployment in Ihrem Rechenzentrum. Vertrauensvoll entwickeln. Ihre Daten in der Schweiz behalten.
  actions:
    - theme: alt
      text: Unsere Vision
      link: /de/docs/1_vision_and_positioning/1_introduction/
    - theme: alt
      text: Warum Swiss AI Hub
      link: /de/docs/1_vision_and_positioning/1_introduction
    - theme: brand
      text: Plattformübersicht
      link: /de/docs/2_platform/2_architecture/1_core_components/

features:
  - title: Die Open-Source-KI-Wette
    details: Die besten Open-Source-Tools (LiteLLM, Milvus, LlamaIndex) sind integriert und einsatzbereit. Wenn sie sich weiterentwickeln, profitieren Sie davon. Kein Vendor Lock-in, keine Lizenzgebühren, keine Plattformbeschränkungen. Setzen Sie auf das Ökosystem, nicht auf einen einzelnen Anbieter.
  - title: Die Plattform besitzen, nicht mieten
    details: Eine komplette Infrastruktur, die Sie deployen und kontrollieren. Keine SaaS-Abonnements, keine Code-Bibliothek. Authentifizierung, Monitoring, Datenbanken, UIs – alles inklusive. Azure AI-Niveau an Vollständigkeit mit LangChain-Niveau an Besitz.
  - title: In 30 Minuten zur produktiven KI
    details: Ein einziger Befehl deployt alles. LLM-Gateway, Vektorsuche, Chat-Interface, Authentifizierung, Monitoring. Vorgefertigte Agents funktionieren sofort. Keine Cloud-Bereitstellung, keine komplexe Einrichtung, kein Infrastruktur-Engineering.
  - title: Strategische Unabhängigkeit von Big Tech
    details: Überall einsetzbar – On-Premise, Schweizer Rechenzentren, Ihre Cloud. Nutzen Sie lokale Modelle oder Cloud-APIs. Wechseln Sie Anbieter ohne Codeänderungen. Ihre Daten, Ihre Infrastruktur, Ihre Kontrolle. Echte Souveränität.
  - title: Transparente, keine Black-Box-KI
    details: Jeder Agent folgt expliziten Workflows. Jede Entscheidung ist nachvollziehbar und auditierbar. Jede Kostenstelle wird verfolgt. Sehen Sie genau, warum die KI eine Antwort gegeben hat. Vertrauen durch Transparenz, nicht durch Versprechen. Gebaut für Schweizer Standards.
  - title: Kollektive Stärke durch Zusammenarbeit
    details: Schweizer Organisationen teilen sich Infrastruktur, konkurrieren bei Innovationen. Tragen Sie zu Verbesserungen bei, profitieren Sie von anderen. Bauen Sie gemeinsam, was keine einzelne Organisation allein finanzieren könnte. Der Schweizer KI-Vorteil.
```

<div style="height: 500px"></div>

## FAQ

::: details Wie kann unsere Schweizer Organisation KI deployen und gleichzeitig alle Daten On-Premise behalten?
Der Swiss AI Hub ist eine **Open-Source-KI-Plattform**, die *Sie* deployen und kontrollieren. Sie wurde speziell für die
**On-Premise-Installation** in Ihrem eigenen Schweizer Rechenzentrum entwickelt. Das bedeutet, dass Sie die gesamte
KI-Infrastruktur – einschließlich Sprachmodell-Gateways und Wissensdatenbanken – auf Ihren Servern betreiben können, was
eine vollständige Kontrolle und Datenisolation gewährleistet. Weitere Details finden Sie in unseren
[Deployment-Optionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie können wir KI nutzen und Schweizer Datenschutzgesetze wie FADP (revDSG) einhalten?
Die Gewährleistung der **Schweizer Datensouveränität** ist ein Kernprinzip der Swiss AI Hub Community. Da *Sie* die
Plattform deployen, wählen Sie *wo* sie läuft – entweder auf Ihren eigenen Servern in der Schweiz oder in
vertrauenswürdigen Schweizer Rechenzentren. Durch die Verwendung lokaler Large Language Models (LLMs) bleibt die
Verarbeitung sensibler Daten vollständig unter Ihrer Kontrolle, was Ihnen hilft, die **FADP (revDSG) Anforderungen** zu
erfüllen. Lesen Sie mehr über unser Engagement in
[Der Schweizer Weg: Datenschutz, Souveränität und Transparenz](/de/docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details Was ist eine vertrauenswürdige Open-Source-KI-Plattform als Alternative zu großen Cloud-Anbietern wie Azure AI oder Google Vertex AI?
Der Swiss AI Hub bietet eine **Open-Source-Alternative**, die von einer Community entwickelt wurde, die sich auf die
Kontrolle durch den Benutzer konzentriert. Die Kerninfrastruktur der Plattform ist unter Apache 2.0 lizenziert, was
bedeutet, dass *Sie* Ihr Deployment besitzen. Dies ermöglicht es Ihnen, **Vendor Lock-in** zu vermeiden und befreit Sie
von spezifischen Ökosystemen und unvorhersehbaren Preisstrukturen, die bei großen Cloud-Anbietern üblich sind. Sehen
Sie, wie wir im [Vergleichsmatrix](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/)
abschneiden.
:::

::: details Wie stellen wir sicher, dass KI-Entscheidungen in unserem Schweizer Unternehmen nachvollziehbar und auditierbar sind?
Die Swiss AI Hub Community priorisiert **Transparenz für Vertrauen**. Unsere Plattform bietet umfassende
Observability-Funktionen. Jeder Schritt, den ein KI-Agent unternimmt, ist sichtbar, Entscheidungen werden mit Kontext
protokolliert und Kosten werden verfolgt. Tools wie Phoenix ermöglichen die Nachverfolgung jeder Interaktion, sodass Sie
jederzeit verstehen können, *warum* eine KI eine bestimmte Antwort gegeben hat, was für **Compliance und Auditing**
entscheidend ist. Erfahren Sie mehr über diese Funktionen unter
[Auditing & Observability](/de/docs/2_platform/12_auditing/).
:::

::: details Gibt es einen fertigen KI-Infrastruktur-Stack (Auth, Monitoring, Vektor-DBs), den wir selbst deployen können?
Ja, der Swiss AI Hub bietet einen **kompletten, vorintegrierten KI-Infrastruktur-Stack**, den *Sie* deployen. Er bündelt
wesentliche Komponenten wie Authentifizierung, Monitoring, verschiedene Datenbanken (einschließlich Vektor-Datenbanken
für KI), Datenverarbeitungs-Pipelines und Benutzeroberflächen direkt out-of-the-box. Dies löst viele gängige
**Produktions-KI-Herausforderungen** vom ersten Tag an. Erfahren Sie mehr darüber im
[„Day 2“-Vorteil](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details Was ist der schnellste Weg, eine sichere, unternehmensfähige KI-Plattform in der Schweiz einzurichten?
Sie können die gesamte Swiss AI Hub Plattform in etwa **30 Minuten mit einem einzigen Befehl** deployen. Als
Open-Source-Plattform, die Sie selbst installieren, enthält sie vorgefertigte Agents und Interfaces, die sofort
einsatzbereit sind und eine schnelle Wertschöpfung ohne komplexe Cloud-Konfigurationen ermöglichen. Beginnen Sie mit dem
[Schnellstart-Handbuch](/de/docs/2_platform/1_quick_start/).
:::

::: details Wie können unsere Mitarbeitenden sicher auf unternehmensspezifische KI-Hilfe direkt in Microsoft Teams oder Slack zugreifen?
Die Swiss AI Hub Plattform umfasst **integrierte Integrationen für Microsoft Teams und Slack**. Dies ermöglicht Ihren
Mitarbeitenden, sicher mit KI-Agents zu interagieren, die Zugang zu relevantem Unternehmenswissen haben, direkt in den
Kollaborationstools, die sie täglich verwenden, und verbessert so den Workflow. Details finden Sie unter
[Slack- & Teams-Integrationen](/de/docs/2_platform/17_slack_teams_integrations/).
:::

::: details Wie kann unsere Organisation den Zugriff und die Nutzung verschiedener KI-Modelle (z. B. GPT-4, Gemini, lokale Modelle) zentral verwalten?
Der Swiss AI Hub enthält einen **integrierten LLM Proxy (LiteLLM)**, der als vereinheitlichtes Gateway zu all Ihren
konfigurierten KI-Modellen fungiert. Sie können den Modellzugriff zentral verwalten, Anfragen basierend auf Policies
weiterleiten, Kosten über verschiedene Anbieter hinweg verfolgen und sogar Failover-Mechanismen einrichten. Weitere
Informationen finden Sie unter [Sprachmodelle](/de/docs/2_platform/13_language_models/).
:::

::: details Wie können wir die Betriebskosten im Zusammenhang mit der Nutzung von KI-Modellen effektiv kontrollieren und vorhersagen?
Unsere Community hat den Swiss AI Hub mit **transparenter Kostenkontrolle** im Hinterkopf entwickelt. Der integrierte
LLM Proxy verfolgt die Token-Nutzung für jede Interaktion, pro Benutzer oder Agent. Sie können die KI-Ausgaben in
Echtzeit-Dashboards überwachen und Budgets konfigurieren, um unerwartete Kosten zu vermeiden. Erfahren Sie mehr über
[Kostenkontrolle](/de/docs/2_platform/14_cost_control/).
:::

::: details Unser Schweizer Unternehmen hat strenge Datenschutzregeln, die die Nutzung öffentlicher KI-Clouds verhindern. Welche sichere KI-Lösung können wir verwenden?
Der Swiss AI Hub ist dafür ideal. Als Open-Source-Plattform, die *Sie* deployen, können Sie sie **vollständig
On-Premise** installieren und **lokale, selbst gehostete LLMs** verwenden. Dies stellt sicher, dass absolut keine Daten
(Prompts, Antworten, Dokumente) jemals Ihre sichere Netzwerkgrenze verlassen. Überprüfen Sie unsere umfassenden
[Sicherheitsfunktionen](/de/docs/2_platform/20_security/).
:::

::: details Wir haben KI-Prototypen, die Frameworks wie LangChain verwenden, finden es aber schwierig, diese zuverlässig in der Produktion zu deployen. Wie kann der Swiss AI Hub helfen?
Der Swiss AI Hub bietet die notwendige **produktionsreife Infrastruktur**, die Entwicklungsframeworks oft fehlt. Während
LangChain hilft, die KI-Logik zu erstellen, liefert unsere Plattform die wesentlichen umgebenden Komponenten: robuste
Deployment-Mechanismen, Unternehmensauthentifizierung, Skalierung, Monitoring und Benutzeroberflächen, die für den
**zuverlässigen Unternehmenseinsatz** erforderlich sind. Sehen Sie
[Unsere Lösung](/de/docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details Wie können wir KI-Agents sicher Fragen basierend auf unseren internen Unternehmensdokumenten (wie PDFs oder Word-Dateien) beantworten lassen?
Der Swiss AI Hub enthält ein sicheres **Retrieval-Augmented Generation (RAG) System**. Sie konfigurieren automatisierte
[Daten-Pipelines](/de/docs/2_platform/6_pipelines/), um Dokumente aus Ihren Quellen (wie SharePoint) zu ingestieren.
Diese Pipelines verarbeiten die Dokumente sicher und indizieren sie in einer Vektor-Datenbank, *die Sie besitzen und
kontrollieren*, wodurch Agents sicher auf Unternehmenswissen zugreifen können.
:::

::: details Verschiedene Teams in unserer Organisation verwenden diverse KI-Tools, was zu Silos führt. Wie können wir einen einheitlichen, gesteuerten KI-Ansatz schaffen?
Der Swiss AI Hub kann als Ihre **zentrale, vereinheitlichte KI-Plattform** dienen. Er bietet eine gemeinsame
Infrastruktur, auf der alle Teams aufbauen können, gewährleistet konsistente Governance- und Sicherheitsrichtlinien,
bietet einheitliches Monitoring und umfasst eine
[OpenAI-kompatible API](/de/docs/2_platform/18_api/1_openai_compatible_api/), die die Integration mit vielen bestehenden
Tools ermöglicht und dazu beiträgt, **Fragmentierung zu reduzieren**.
:::

::: details Was ist eine effiziente und skalierbare Methode, um die Aufnahme und Vektor-Einbettung von Tausenden von Unternehmensdokumenten für KI zu handhaben?
Der Swiss AI Hub nutzt **Daten-Pipelines**, die mit dem robusten Orchestrator Dagster erstellt wurden. Diese Pipelines
automatisieren den gesamten Workflow: Verbindung zu Ihren Datenquellen, intelligentes Parsen verschiedener Dateiformate,
Erstellung semantischer Chunks, Generierung von Vektor-Einbettungen und deren Indizierung in Ihrem Vektor-Speicher (wie
Milvus). Details finden Sie im [Pipelines-Abschnitt](/de/docs/2_platform/6_pipelines/).
:::

::: details Können wir eine komplette KI-Plattform vollständig offline in einem Air-Gapped-Netzwerk innerhalb der Schweiz deployen und betreiben?
Ja. Wenn Sie den Swiss AI Hub **On-Premise** deployen und ihn so konfigurieren, dass er nur **selbst gehostete Large
Language Models** (LLMs) verwendet, kann die gesamte Plattform ohne externe Internetverbindung betrieben werden. Dies
macht sie für **Air-Gapped-Umgebungen** mit höchsten Sicherheitsanforderungen geeignet. Siehe
[Deployment-Optionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass die KI-Agents vertrauenswürdige Antworten liefern und nicht einfach "halluzinieren" oder sich Dinge ausdenken?
Vertrauen ist entscheidend. Swiss AI Hub **Agents** sind darauf ausgelegt, expliziten, definierten Workflows zu folgen.
Sie verwenden hauptsächlich **Retrieval-Augmented Generation (RAG)**, was bedeutet, dass ihre Antworten auf
Informationen basieren, die aus *Ihren* verifizierten Unternehmensdokumenten abgerufen wurden. Agents **zitieren auch
ihre Quellen**, und eingebaute „Guardrails“ prüfen, ob die abgerufenen Informationen ausreichen, um **zuverlässige,
faktenbasierte Antworten** zu gewährleisten. Erfahren Sie mehr über [Agents](/de/docs/2_platform/5_agents/).
:::

::: details Ist es für KI-Agents auf dieser Plattform möglich, bei komplexen Aufgaben Hilfe oder Genehmigung von menschlichen Experten anzufordern?
Ja, unsere Plattform unterstützt **Human-in-the-Loop (HITL)** und **Bot-in-the-Loop (BITL)** Workflows. Ein KI-Agent
kann so konzipiert werden, dass er seinen Prozess an einem bestimmten Schritt pausiert, eine Anfrage für Input oder
Genehmigung an einen bestimmten menschlichen Experten sendet (zum Beispiel über eine Slack-Nachricht) und dann seine
Arbeit nahtlos fortsetzt, sobald der Mensch antwortet. Entdecken Sie die
[Agenten-Grundlagen](/de/docs/3_sdk/2_building_agents/1_agent_fundamentals/), die diese Muster ermöglichen.
:::

::: details Wie verbindet und integriert sich der Swiss AI Hub mit unserer bestehenden Unternehmenssoftware wie SharePoint oder internen Datenbanken?
Die Plattform bietet **flexible Integrationsoptionen**. KI-Agents können direkte API-Aufrufe an externe Systeme machen;
externe Systeme können Agents über die [Agent Interaction API](/de/docs/2_platform/18_api/2_agent_interaction_api/) der
Plattform triggern; automatisierte Daten-Pipelines können Wissen aus Quellen wie SharePoint synchronisieren; und
Standardprotokolle werden für benutzerdefinierte Verbindungen unterstützt. Siehe
[Externe Integrationen](/de/docs/2_platform/22_external_integrations/).
:::

::: details Wie profitiert die breitere Schweizer KI-Community von der Nutzung einer Open-Source-Plattform wie dem Swiss AI Hub?
Unser **Ökosystem-Modell** basiert auf Zusammenarbeit. Die Kernplattform ist Open-Source, was Schweizer Organisationen
ermöglicht, ihre Anstrengungen beim Aufbau und der Verbesserung der fundamentalen KI-Infrastruktur zu bündeln. Jeder
profitiert von gemeinsamen Fortschritten, wodurch einzelne Organisationen ihre Ressourcen auf die Erstellung
einzigartiger KI-Anwendungen konzentrieren können, die auf ihre spezifischen Bedürfnisse zugeschnitten sind, und so die
gesamten KI-Fähigkeiten der Schweiz stärken. Lesen Sie mehr über
[Das Ökosystem-Modell](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details Wir sind besorgt über die Komplexität der Einrichtung und Verwaltung einer selbst gehosteten KI-Plattform. Ist der Swiss AI Hub schwierig zu bedienen?
Die Swiss AI Hub Community hat die Plattform für **vereinfachtes Deployment und Management** entwickelt. Die
Installation erfolgt mit einem einzigen Befehl, und kritische Infrastrukturherausforderungen wie Authentifizierung,
Monitoring und Skalierungskonfiguration werden out-of-the-box gelöst. Dies reduziert die betriebliche Komplexität im
Vergleich zum Aufbau einer KI-Infrastruktur von Grund auf oder der Verwaltung komplexer Cloud-Anbieterdienste erheblich.
Überprüfen Sie den [Schnellstart](/de/docs/2_platform/1_quick_start/).
:::

```
```
