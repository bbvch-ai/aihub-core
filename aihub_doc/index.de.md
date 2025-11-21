---
# https://vitepress.dev/reference/default-theme-home-page
layout: home
source_sha: 7be608b155702ad69c57a6996e2ff5ad88994162ea3beefd4e63aaa570c47acb

hero:
  name: Swiss AI Hub
  text: Die offene KI-Plattform, die Sie besitzen und kontrollieren
  tagline: Komplette Infrastruktur für Produktions-KI. Bereitstellung in Ihrem Rechenzentrum. Vertrauensvoll entwickeln. Ihre Daten bleiben in der Schweiz.
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
  - title: KI in 30 Minuten bereitstellen
    details: Ein einziger Befehl startet alles. LLM-Gateway, Vektordatenbanken, Chat-Interface, Authentifizierung, Monitoring. Vorgefertigte Agents funktionieren sofort. Keine Cloud-Konten, keine komplexe Einrichtung.
  - title: Ihre Daten bleiben Ihre
    details: Betreiben Sie alles On-Premise oder in Schweizer Rechenzentren. Lokale LLMs bedeuten, dass sensible Daten Ihr Netzwerk niemals verlassen. Sie kontrollieren, wo jedes Byte verarbeitet und gespeichert wird.
  - title: Sehen Sie genau, was die KI tut
    details: Jede Entscheidung ist nachvollziehbar. Jeder Workflow-Schritt ist sichtbar. Jede Kostenposition wird verfolgt. Wenn KI eine Antwort gibt, können Sie sehen, warum. Vertrauen durch Transparenz, nicht durch Versprechen.
  - title: Entwickeln ohne Infrastruktur-Probleme
    details: Authentifizierung, Deployment, Monitoring, Skalierung sind bereits gelöst. Schreiben Sie die Geschäftslogik Ihres Agents, die Plattform kümmert sich um den Rest. Konzentrieren Sie sich auf das, was Sie einzigartig macht.
  - title: Funktioniert mit dem, was Sie haben
    details: Die OpenAI-kompatible API verbindet bestehende Tools. Teams- und Slack-Bots erreichen Nutzer dort, wo sie arbeiten. Integration mit SharePoint, FTP und Ihren Systemen über Standardprotokolle.
  - title: Wachsen Sie mit dem Ökosystem
    details: Jede Schweizer Organisation, die die Plattform nutzt, macht sie stärker. Teilen Sie gemeinsame Agents, behalten Sie strategische privat. Kooperieren Sie bei der Infrastruktur, konkurrieren Sie bei der Innovation.
---

<div style="height: 500px"></div>

## FAQ

::: details Wie kann unsere Schweizer Organisation KI einsetzen und dabei alle Daten On-Premise halten?
Der Swiss AI Hub ist eine **Open-Source-KI-Plattform**, die *Sie* bereitstellen und kontrollieren. Sie wurde speziell
für die **On-Premise-Installation** in Ihrem eigenen Schweizer Rechenzentrum entwickelt. Das bedeutet, dass Sie die
gesamte KI-Infrastruktur – einschließlich Sprachmodell-Gateways und Wissensdatenbanken – auf Ihren Servern betreiben
können, um vollständige Kontrolle und Datenisolation zu gewährleisten. Weitere Details finden Sie in unseren
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie können wir KI nutzen und dabei die Schweizer Datenschutzgesetze wie FADP (revDSG) einhalten?
Die Gewährleistung der **Schweizer Datenhoheit** ist ein Kernprinzip der Swiss AI Hub Community. Da *Sie* die Plattform
bereitstellen, bestimmen Sie *wo* sie läuft – entweder auf Ihren eigenen Servern in der Schweiz oder in
vertrauenswürdigen Schweizer Rechenzentren. Durch die Verwendung lokaler Large Language Models (LLMs) bleibt die
Verarbeitung sensibler Daten vollständig unter Ihrer Kontrolle, was Ihnen hilft, die **FADP (revDSG) Anforderungen** zu
erfüllen. Lesen Sie mehr über unser Engagement in
[Der Schweizer Weg: Datenschutz, Souveränität und Transparenz](/de/docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details Was ist eine vertrauenswürdige Open-Source-KI-Plattform als Alternative zu großen Cloud-Anbietern wie Azure AI oder Google Vertex AI?
Der Swiss AI Hub bietet eine **Open-Source-Alternative**, die von einer Community entwickelt wurde, die sich auf die
Benutzerkontrolle konzentriert. Die Kerninfrastruktur der Plattform ist unter Apache 2.0 lizenziert, was bedeutet, dass
*Sie* Ihr Deployment besitzen. Dies hilft Ihnen, einen **Vendor Lock-in** zu vermeiden und befreit Sie von spezifischen
Ökosystemen und unvorhersehbaren Preisstrukturen, die bei großen Cloud-Anbietern üblich sind. Sehen Sie, wie wir uns in
der [Vergleichsmatrix](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/) vergleichen.
:::

::: details Wie können wir sicherstellen, dass KI-Entscheidungen in unserem Schweizer Unternehmen nachvollziehbar und auditierbar sind?
Die Swiss AI Hub Community priorisiert **Transparenz für Vertrauen**. Unsere Plattform bietet umfangreiche
Observability-Funktionen. Jeder Schritt, den ein KI-Agent unternimmt, ist sichtbar, Entscheidungen werden mit Kontext
protokolliert und Kosten werden verfolgt. Tools wie Phoenix ermöglichen die Nachverfolgung jeder Interaktion, sodass Sie
immer verstehen können, *warum* eine KI eine bestimmte Antwort gegeben hat, was für **Compliance und Auditing**
entscheidend ist. Entdecken Sie diese Funktionen unter [Auditing & Observability](/de/docs/2_platform/12_auditing/).
:::

::: details Gibt es einen fertigen KI-Infrastruktur-Stack (Auth, Monitoring, Vektor-DBs), den wir selbst deployen können?
Ja, der Swiss AI Hub bietet einen **kompletten, vorintegrierten KI-Infrastruktur-Stack**, den *Sie* deployen. Er bündelt
wesentliche Komponenten wie Authentifizierung, Monitoring, verschiedene Datenbanken (einschließlich Vektordatenbanken
für KI), Datenverarbeitungspipelines und Benutzeroberflächen sofort einsatzbereit. Dies löst viele gängige
**Herausforderungen in der Produktions-KI** von Anfang an. Erfahren Sie mehr darüber in
[Der „Day 2“-Vorteil](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details Was ist der schnellste Weg, eine sichere, unternehmensfähige KI-Plattform in der Schweiz einzurichten?
Sie können die gesamte Swiss AI Hub Plattform in etwa **30 Minuten mit einem einzigen Befehl** deployen. Als
Open-Source-Plattform, die Sie selbst installieren, enthält sie vorgefertigte Agents und Schnittstellen, die sofort
einsatzbereit sind und eine schnelle Wertschöpfung ohne komplexe Cloud-Konfigurationen ermöglichen. Beginnen Sie mit dem
[Schnellstart-Leitfaden](/de/docs/2_platform/1_quick_start/).
:::

::: details Wie können unsere Mitarbeiter sicher auf unternehmensspezifische KI-Hilfe direkt in Microsoft Teams oder Slack zugreifen?
Die Swiss AI Hub Plattform umfasst **integrierte Integrationen für Microsoft Teams und Slack**. Dies ermöglicht Ihren
Mitarbeitern, sicher mit KI-Agents zu interagieren, die Zugriff auf relevantes Unternehmenswissen haben, direkt in den
Kollaborationstools, die sie täglich nutzen, wodurch der Workflow verbessert wird. Details finden Sie unter
[Slack & Teams Integrationen](/de/docs/2_platform/16_slack_teams_integrations/).
:::

::: details Wie kann unsere Organisation den Zugriff und die Nutzung verschiedener KI-Modelle (z.B. GPT-4, Gemini, lokale Modelle) zentral verwalten?
Der Swiss AI Hub beinhaltet einen **integrierten LLM Proxy (LiteLLM)**, der als vereinheitlichtes Gateway zu all Ihren
konfigurierten KI-Modellen fungiert. Sie können den Modellzugriff zentral verwalten, Anfragen basierend auf Richtlinien
routen, Kosten über verschiedene Anbieter hinweg verfolgen und sogar Failover-Mechanismen einrichten. Weitere
Informationen finden Sie unter [Sprachmodelle](/de/docs/2_platform/13_language_models/).
:::

::: details Wie können wir die Betriebskosten für die Nutzung von KI-Modellen effektiv kontrollieren und vorhersagen?
Unsere Community hat den Swiss AI Hub mit dem Ziel der **transparenten Kostenkontrolle** entwickelt. Der integrierte LLM
Proxy verfolgt die Token-Nutzung für jede Interaktion, pro Benutzer oder Agent. Sie können die KI-Ausgaben in
Echtzeit-Dashboards überwachen und Budgets konfigurieren, um unerwartete Kosten zu vermeiden. Erfahren Sie mehr über
[Kostenkontrolle](/de/docs/2_platform/14_cost_control/).
:::

::: details Unser Schweizer Unternehmen hat strenge Datenschutzregeln, die die Nutzung öffentlicher KI-Clouds verhindern. Welche sichere KI-Lösung können wir verwenden?
Der Swiss AI Hub ist hierfür ideal. Als Open-Source-Plattform, die *Sie* bereitstellen, können Sie sie **vollständig
On-Premise** installieren und **lokale, selbst gehostete LLMs** verwenden. Dies stellt sicher, dass absolut keine Daten
(Prompts, Antworten, Dokumente) jemals Ihre sichere Netzwerkperimeter verlassen. Überprüfen Sie unsere umfassenden
[Sicherheitsfunktionen](/de/docs/2_platform/19_security/).
:::

::: details Wir haben KI-Prototypen, die Frameworks wie LangChain verwenden, finden es aber schwierig, diese zuverlässig in der Produktion bereitzustellen. Wie kann der Swiss AI Hub helfen?
Der Swiss AI Hub bietet die notwendige **produktionsreife Infrastruktur**, die Entwicklungs-Frameworks oft fehlt.
Während LangChain bei der Erstellung der KI-Logik hilft, liefert unsere Plattform die wesentlichen umliegenden
Komponenten: robuste Deployment-Mechanismen, Unternehmensauthentifizierung, Skalierung, Monitoring und
Benutzeroberflächen, die für einen **zuverlässigen Unternehmenseinsatz** erforderlich sind. Siehe
[Unsere Lösung](/de/docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details Wie können wir KI-Agents sicher Fragen basierend auf unseren internen Unternehmensdokumenten (wie PDFs oder Word-Dateien) beantworten lassen?
Der Swiss AI Hub umfasst ein sicheres **Retrieval-Augmented Generation (RAG)-System**. Sie konfigurieren automatisierte
[Datenpipelines](/de/docs/2_platform/6_pipelines/), um Dokumente aus Ihren Quellen (z.B. SharePoint) aufzunehmen. Diese
Pipelines verarbeiten die Dokumente sicher und indizieren sie in einer Vektordatenbank, *die Sie besitzen und
kontrollieren*, wodurch Agents sicher auf Unternehmenswissen zugreifen können.
:::

::: details Verschiedene Teams in unserer Organisation verwenden unterschiedliche KI-Tools und schaffen dadurch Silos. Wie können wir einen einheitlichen, gesteuerten KI-Ansatz schaffen?
Der Swiss AI Hub kann als Ihre **zentrale, vereinheitlichte KI-Plattform** dienen. Er bietet eine gemeinsame
Infrastruktur, auf der alle Teams aufbauen können, gewährleistet konsistente Governance- und Sicherheitsrichtlinien,
bietet einheitliches Monitoring und enthält eine
[OpenAI-kompatible API](/de/docs/2_platform/17_api/1_openai_compatible_api/), die die Integration mit vielen bestehenden
Tools ermöglicht und so zur **Reduzierung der Fragmentierung** beiträgt.
:::

::: details Was ist eine effiziente und skalierbare Methode zur Handhabung der Aufnahme und Vektor-Einbettung Tausender von Unternehmensdokumenten für KI?
Der Swiss AI Hub nutzt **Datenpipelines**, die mit dem robusten Orchestrator Dagster erstellt wurden. Diese Pipelines
automatisieren den gesamten Workflow: Verbindung zu Ihren Datenquellen, intelligentes Parsen verschiedener Dateiformate,
Erstellung semantischer Chunks, Generierung von Vektor-Embeddings und deren Indizierung in Ihrem Vektorspeicher (wie
Milvus). Details finden Sie im [Abschnitt Pipelines](/de/docs/2_platform/6_pipelines/).
:::

::: details Können wir eine komplette KI-Plattform vollständig offline in einem Air-Gapped-Netzwerk innerhalb der Schweiz bereitstellen und betreiben?
Ja. Wenn Sie den Swiss AI Hub **On-Premise** deployen und so konfigurieren, dass er nur **selbst gehostete Large
Language Models** (LLMs) verwendet, kann die gesamte Plattform ohne externe Internetverbindung betrieben werden. Dies
macht sie für **Air-Gapped-Umgebungen** mit höchsten Sicherheitsanforderungen geeignet. Siehe
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass die KI-Agents vertrauenswürdige Antworten liefern und nicht nur „halluzinieren“ oder sich etwas ausdenken?
Vertrauen ist entscheidend. Swiss AI Hub **Agents** sind so konzipiert, dass sie expliziten, definierten Workflows
folgen. Sie verwenden primär **Retrieval-Augmented Generation (RAG)**, was bedeutet, dass ihre Antworten auf
Informationen basieren, die aus *Ihren* verifizierten Unternehmensdokumenten stammen. Agents **zitieren** auch **ihre
Quellen**, und integrierte „Guardrails“ prüfen, ob die abgerufenen Informationen ausreichen, um **zuverlässige,
faktenbasierte Antworten** zu gewährleisten. Erfahren Sie mehr über [Agents](/de/docs/2_platform/5_agents/).
:::

::: details Ist es möglich, dass KI-Agents auf dieser Plattform bei komplexen Aufgaben menschliche Experten um Hilfe oder Genehmigung bitten?
Ja, unsere Plattform unterstützt **Human-in-the-Loop (HITL)**- und **Bot-in-the-Loop (BITL)**-Workflows. Ein KI-Agent
kann so konzipiert werden, dass er seinen Prozess an einem bestimmten Schritt pausiert, eine Anfrage für Eingabe oder
Genehmigung an einen bestimmten menschlichen Experten sendet (zum Beispiel über eine Slack-Nachricht) und dann seine
Arbeit nahtlos fortsetzt, sobald der Mensch antwortet. Entdecken Sie die
[Agent-Grundlagen](/de/docs/3_sdk/2_building_agents/1_agent_fundamentals/), die diese Muster ermöglichen.
:::

::: details Wie verbindet sich und integriert sich der Swiss AI Hub mit unserer bestehenden Unternehmenssoftware wie SharePoint oder internen Datenbanken?
Die Plattform bietet **flexible Integrationsoptionen**. KI-Agents können direkte API-Aufrufe an externe Systeme tätigen;
externe Systeme können Agents über die [Agent Interaction API](/de/docs/2_platform/17_api/2_agent_interaction_api/) der
Plattform triggern; automatisierte Datenpipelines können Wissen aus Quellen wie SharePoint synchronisieren; und
Standardprotokolle werden für benutzerdefinierte Verbindungen unterstützt. Siehe
[Externe Integrationen](/de/docs/2_platform/21_external_integrations/).
:::

::: details Wie profitiert die breitere Schweizer KI-Community von der Nutzung einer Open-Source-Plattform wie dem Swiss AI Hub?
Unser **Ökosystem-Modell** basiert auf Zusammenarbeit. Die Kernplattform ist Open-Source, was Schweizer Organisationen
ermöglicht, ihre Anstrengungen beim Aufbau und der Verbesserung der grundlegenden KI-Infrastruktur zu bündeln. Alle
profitieren von gemeinsamen Fortschritten, wodurch sich einzelne Organisationen auf die Erstellung einzigartiger, ihren
Bedürfnissen entsprechender KI-Anwendungen konzentrieren können, was die gesamten KI-Fähigkeiten der Schweiz stärkt.
Lesen Sie über [Das Ökosystem-Modell](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details Wir sind besorgt über die Komplexität der Einrichtung und Verwaltung einer selbst gehosteten KI-Plattform. Ist der Swiss AI Hub schwierig zu bedienen?
Die Swiss AI Hub Community hat die Plattform für eine **vereinfachte Bereitstellung und Verwaltung** konzipiert. Die
Installation erfolgt mit einem einzigen Befehl, und kritische Infrastrukturherausforderungen wie Authentifizierung,
Monitoring und Skalierungskonfiguration sind sofort gelöst. Dies reduziert die operative Komplexität erheblich im
Vergleich zum Aufbau einer KI-Infrastruktur von Grund auf oder der Verwaltung komplexer Cloud-Anbieterdienste.
Überprüfen Sie den [Schnellstart](/de/docs/2_platform/1_quick_start/).
:::
