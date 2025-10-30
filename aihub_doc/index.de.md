---
# https://vitepress.dev/reference/default-theme-home-page
layout: home
source_sha: a33772a629de050f4d642ec80a9bf14d4f0e501653ecaad1b2e7b9cec6bdccb2

hero:
  name: Swiss AI Hub
  text: Die offene KI-Plattform, die Sie besitzen und kontrollieren
  tagline: Komplette Infrastruktur für Produktions-KI. Bereitstellung in Ihrem Rechenzentrum. Mit Vertrauen entwickeln. Ihre Daten bleiben in der Schweiz.
  actions:
    - theme: brand
      text: Schnellstart
      link: /de/docs/2_platform/1_quick_start/
    - theme: alt
      text: Plattform-Übersicht
      link: /de/docs/2_platform/2_architecture/1_core_components/
    - theme: alt
      text: Warum Swiss AI Hub
      link: /de/docs/1_vision_and_positioning/1_introduction

features:
  - title: KI in 30 Minuten bereitstellen
    details: Ein einziger Befehl startet alles. LLM-Gateway, Vektordatenbanken, Chat-Oberfläche, Authentifizierung, Monitoring. Vorgefertigte Agenten funktionieren sofort. Keine Cloud-Konten, keine komplexe Einrichtung.
  - title: Ihre Daten bleiben Ihre
    details: Betreiben Sie alles On-Premise oder in Schweizer Rechenzentren. Lokale LLMs bedeuten, dass sensible Daten Ihr Netzwerk niemals verlassen. Sie kontrollieren, wo jedes Byte verarbeitet und gespeichert wird.
  - title: Sehen Sie genau, was die KI tut
    details: Jede Entscheidung ist nachvollziehbar. Jeder Workflow-Schritt ist sichtbar. Jede Kostenstelle wird verfolgt. Wenn die KI eine Antwort gibt, können Sie sehen, warum. Vertrauen durch Transparenz, nicht durch Versprechen.
  - title: Entwickeln Sie ohne Infrastruktur-Kopfschmerzen
    details: Authentifizierung, Bereitstellung, Überwachung, Skalierung sind bereits gelöst. Schreiben Sie die Geschäftslogik Ihres Agenten, die Plattform erledigt alles andere. Konzentrieren Sie sich auf das, was Sie einzigartig macht.
  - title: Funktioniert mit dem, was Sie haben
    details: OpenAI-kompatible API verbindet bestehende Tools. Teams- und Slack-Bots erreichen Benutzer dort, wo sie arbeiten. Integration mit SharePoint, FTP und Ihren Systemen über Standardprotokolle.
  - title: Wachsen Sie mit dem Ökosystem
    details: Jede Schweizer Organisation, die die Plattform nutzt, macht sie stärker. Teilen Sie gemeinsame Agenten, halten Sie strategische privat. Kollaborieren Sie bei der Infrastruktur, konkurrieren Sie bei der Innovation.
---

<div style="height: 500px"></div>

## FAQ

::: details Wie kann unsere Schweizer Organisation KI bereitstellen und dabei alle Daten On-Premise halten?
Der Swiss AI Hub ist eine **Open-Source KI-Plattform**, die *Sie* bereitstellen und kontrollieren. Sie wurde speziell
für die **On-Premise-Installation** in Ihrem eigenen Schweizer Rechenzentrum entwickelt. Dies bedeutet, dass Sie die
gesamte KI-Infrastruktur – einschliesslich Sprachmodell-Gateways und Wissensdatenbanken – auf Ihren Servern betreiben
können, was vollständige Kontrolle und Datenisolation gewährleistet. Weitere Details finden Sie in unseren
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie können wir KI nutzen und gleichzeitig die Schweizer Datenschutzgesetze wie das FADP (revDSG) einhalten?
Die Gewährleistung der **Schweizer Datenhoheit** ist ein Kernprinzip der Swiss AI Hub Community. Da *Sie* die Plattform
bereitstellen, wählen Sie, *wo* sie läuft – entweder auf Ihren eigenen Servern in der Schweiz oder in vertrauenswürdigen
Schweizer Rechenzentren. Durch die Verwendung lokaler Large Language Models (LLMs) bleibt die Verarbeitung sensibler
Daten vollständig unter Ihrer Kontrolle, was Ihnen hilft, die **FADP (revDSG) Anforderungen** zu erfüllen. Lesen Sie
mehr über unser Engagement in
[Der Schweizer Weg: Datenschutz, Souveränität und Transparenz](/de/docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details Was ist eine vertrauenswürdige, Open-Source KI-Plattform-Alternative zu grossen Cloud-Anbietern wie Azure AI oder Google Vertex AI?
Der Swiss AI Hub bietet eine **Open-Source-Alternative**, die von einer Gemeinschaft entwickelt wurde, die sich auf die
Benutzerkontrolle konzentriert. Die Kerninfrastruktur der Plattform ist unter Apache 2.0 lizenziert, was bedeutet, dass
*Sie* Ihre Bereitstellung besitzen. Dies ermöglicht es Ihnen, **Vendor Lock-in** zu vermeiden und befreit Sie von
spezifischen Ökosystemen und unvorhersehbaren Preisstrukturen, die bei grossen Cloud-Anbietern üblich sind. Sehen Sie,
wie wir uns in der [Vergleichsmatrix](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/)
vergleichen.
:::

::: details Wie können wir sicherstellen, dass KI-Entscheidungen in unserem Schweizer Unternehmen nachvollziehbar und auditierbar sind?
Die Swiss AI Hub Community priorisiert **Transparenz für Vertrauen**. Unsere Plattform bietet umfassende
Observability-Funktionen. Jeder Schritt, den ein KI-Agent unternimmt, ist sichtbar, Entscheidungen werden mit Kontext
protokolliert und Kosten werden verfolgt. Tools wie Phoenix ermöglichen die Nachverfolgung jeder Interaktion, sodass Sie
immer verstehen können, *warum* eine KI eine bestimmte Antwort gegeben hat, was für **Compliance und Auditing**
entscheidend ist. Entdecken Sie diese Funktionen unter [Auditing & Observability](/de/docs/2_platform/12_auditing/).
:::

::: details Gibt es einen vorgefertigten KI-Infrastruktur-Stack (Auth, Monitoring, Vektor-DBs), den wir selbst bereitstellen können?
Ja, der Swiss AI Hub bietet einen **vollständigen, vorintegrierten KI-Infrastruktur-Stack**, den *Sie* bereitstellen. Er
bündelt wesentliche Komponenten wie Authentifizierung, Monitoring, verschiedene Datenbanken (einschliesslich
Vektordatenbanken für KI), Datenverarbeitungspipelines und Benutzeroberflächen direkt out-of-the-box. Dies löst viele
gängige **Produktions-KI-Herausforderungen** vom ersten Tag an. Erfahren Sie mehr darüber in
[Der "Day 2" Vorteil](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details Was ist der schnellste Weg, eine sichere, unternehmenstaugliche KI-Plattform in der Schweiz einzurichten?
Sie können die gesamte Swiss AI Hub Plattform in etwa **30 Minuten mit einem einzigen Befehl** bereitstellen. Als
Open-Source-Plattform, die Sie selbst installieren, enthält sie vorgefertigte Agenten und Schnittstellen, die sofort
einsatzbereit sind und eine schnelle Wertschöpfung ohne komplexe Cloud-Konfigurationen ermöglichen. Beginnen Sie mit dem
[Schnellstart-Leitfaden](/de/docs/2_platform/1_quick_start/).
:::

::: details Wie können unsere Mitarbeiter sicher auf unternehmensspezifische KI-Hilfe direkt in Microsoft Teams oder Slack zugreifen?
Die Swiss AI Hub Plattform enthält **integrierte Integrationen für Microsoft Teams und Slack**. Dies ermöglicht Ihren
Mitarbeitern, sicher mit KI-Agenten zu interagieren, die Zugriff auf relevantes Unternehmenswissen haben, direkt in den
Kollaborationstools, die sie täglich nutzen, und verbessert so den Workflow. Details finden Sie unter
[Slack & Teams Integrationen](/de/docs/2_platform/15_slack_teams_integrations/).
:::

::: details Wie kann unsere Organisation den Zugriff und die Nutzung verschiedener KI-Modelle (z.B. GPT-4, Gemini, lokale Modelle) zentral verwalten?
Der Swiss AI Hub enthält einen **integrierten LLM Proxy (LiteLLM)**, der als einheitliches Gateway zu all Ihren
konfigurierten KI-Modellen fungiert. Sie können den Modellzugriff zentral verwalten, Anfragen basierend auf Richtlinien
routen, Kosten über verschiedene Anbieter hinweg verfolgen und sogar Failover-Mechanismen einrichten. Weitere
Informationen finden Sie unter [Sprachmodelle](/de/docs/2_platform/13_language_models/).
:::

::: details Wie können wir die Betriebskosten, die mit der Nutzung von KI-Modellen verbunden sind, effektiv kontrollieren und vorhersagen?
Unsere Community hat den Swiss AI Hub mit **transparenter Kostenkontrolle** im Sinn entwickelt. Der integrierte LLM
Proxy verfolgt die Token-Nutzung für jede Interaktion, pro Benutzer oder Agent. Sie können die KI-Ausgaben in
Echtzeit-Dashboards überwachen und Budgets konfigurieren, um unerwartete Kosten zu vermeiden. Erfahren Sie mehr über
[Kostenkontrolle](/de/docs/2_platform/14_cost_control/).
:::

::: details Unser Schweizer Unternehmen hat strenge Datenschutzvorschriften, die die Nutzung öffentlicher KI-Clouds verhindern. Welche sichere KI-Lösung können wir nutzen?
Der Swiss AI Hub ist dafür ideal. Als Open-Source-Plattform, die *Sie* bereitstellen, können Sie sie **vollständig
On-Premise** installieren und **lokale, selbst gehostete LLMs** verwenden. Dies stellt sicher, dass absolut keine Daten
(Prompts, Antworten, Dokumente) jemals Ihr sicheres Netzwerk verlassen. Überprüfen Sie unsere umfassenden
[Sicherheitsfunktionen](/de/docs/2_platform/18_security/).
:::

::: details Wir haben KI-Prototypen, die Frameworks wie LangChain verwenden, finden aber die zuverlässige Bereitstellung in der Produktion schwierig. Wie kann der Swiss AI Hub helfen?
Der Swiss AI Hub bietet die notwendige **produktionsreife Infrastruktur**, die Entwicklungs-Frameworks oft fehlt.
Während LangChain hilft, die KI-Logik aufzubauen, liefert unsere Plattform die wesentlichen umgebenden Komponenten:
robuste Bereitstellungsmechanismen, Unternehmensauthentifizierung, Skalierung, Monitoring und Benutzeroberflächen, die
für einen **zuverlässigen Unternehmenseinsatz** benötigt werden. Siehe
[Unsere Lösung](/de/docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details Wie können wir KI-Agenten sicher Fragen basierend auf unseren internen Unternehmensdokumenten (wie PDFs oder Word-Dateien) beantworten lassen?
Der Swiss AI Hub enthält ein sicheres **Retrieval-Augmented Generation (RAG) System**. Sie konfigurieren automatisierte
[Datenpipelines](/de/docs/2_platform/6_pipelines/), um Dokumente aus Ihren Quellen (wie SharePoint) aufzunehmen. Diese
Pipelines verarbeiten die Dokumente sicher und indizieren sie in einer Vektordatenbank, *die Sie besitzen und
kontrollieren*, wodurch Agenten sicher auf Unternehmenswissen zugreifen können.
:::

::: details Verschiedene Teams in unserer Organisation verwenden unterschiedliche KI-Tools, wodurch Silos entstehen. Wie können wir einen einheitlichen, gesteuerten KI-Ansatz schaffen?
Der Swiss AI Hub kann als Ihre **zentrale, einheitliche KI-Plattform** dienen. Er bietet eine gemeinsame Infrastruktur,
auf der alle Teams aufbauen können, gewährleistet konsistente Governance- und Sicherheitsrichtlinien, bietet
einheitliches Monitoring und umfasst eine [OpenAI-kompatible API](/de/docs/2_platform/16_api/1_openai_compatible_api/),
die die Integration mit vielen bestehenden Tools ermöglicht und so zur **Reduzierung der Fragmentierung** beiträgt.
:::

::: details Was ist ein effizienter und skalierbarer Weg, die Aufnahme und Vektor-Einbettung Tausender Unternehmensdokumente für KI zu handhaben?
Der Swiss AI Hub nutzt **Datenpipelines**, die mit dem robusten Orchestrator Dagster erstellt wurden. Diese Pipelines
automatisieren den gesamten Workflow: Verbindung zu Ihren Datenquellen, intelligentes Parsen verschiedener Dateiformate,
Erstellung semantischer Chunks, Generierung von Vektoreinbettungen und Indizierung dieser in Ihrem Vektorspeicher (wie
Milvus). Details finden Sie im [Pipelines-Abschnitt](/de/docs/2_platform/6_pipelines/).
:::

::: details Können wir eine komplette KI-Plattform vollständig offline in einem Air-Gapped-Netzwerk in der Schweiz bereitstellen und betreiben?
Ja. Wenn Sie den Swiss AI Hub **On-Premise** bereitstellen und ihn so konfigurieren, dass er nur **selbst gehostete
Large Language Models** (LLMs) verwendet, kann die gesamte Plattform ohne externe Internetverbindung betrieben werden.
Dies macht sie für **Air-Gapped-Umgebungen** mit höchsten Sicherheitsanforderungen geeignet. Siehe
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass die KI-Agenten vertrauenswürdige Antworten liefern und nicht einfach "halluzinieren" oder Dinge erfinden?
Vertrauen ist von größter Bedeutung. Swiss AI Hub **Agenten** sind darauf ausgelegt, explizite, definierte Workflows zu
befolgen. Sie verwenden hauptsächlich **Retrieval-Augmented Generation (RAG)**, was bedeutet, dass ihre Antworten auf
Informationen basieren, die aus *Ihren* verifizierten Unternehmensdokumenten stammen. Agenten **zitieren auch ihre
Quellen**, und integrierte "Guardrails" prüfen, ob die abgerufenen Informationen ausreichen, um **zuverlässige,
faktenbasierte Antworten** zu gewährleisten. Erfahren Sie mehr über [Agenten](/de/docs/2_platform/5_agents/).
:::

::: details Ist es für KI-Agenten auf dieser Plattform möglich, bei komplexen Aufgaben menschliche Experten um Hilfe oder Genehmigung zu bitten?
Ja, unsere Plattform unterstützt **Human-in-the-Loop (HITL)** und **Bot-in-the-Loop (BITL)** Workflows. Ein KI-Agent
kann so konzipiert werden, dass er seinen Prozess an einem bestimmten Schritt pausiert, eine Anfrage für Eingabe oder
Genehmigung an einen bestimmten menschlichen Experten sendet (zum Beispiel über eine Slack-Nachricht) und dann seine
Arbeit nahtlos fortsetzt, sobald der Mensch antwortet. Entdecken Sie
[Agenten-Grundlagen](/de/docs/3_sdk/2_building_agents/1_agent_fundamentals/), die diese Muster ermöglichen.
:::

::: details Wie verbindet und integriert sich der Swiss AI Hub mit unserer bestehenden Unternehmenssoftware wie SharePoint oder internen Datenbanken?
Die Plattform bietet **flexible Integrationsoptionen**. KI-Agenten können direkte API-Aufrufe an externe Systeme
tätigen; externe Systeme können Agenten über die
[Agent Interaction API](/de/docs/2_platform/16_api/2_agent_interaction_api/) der Plattform auslösen; automatisierte
Datenpipelines können Wissen aus Quellen wie SharePoint synchronisieren; und Standardprotokolle werden für
benutzerdefinierte Verbindungen unterstützt. Siehe
[Externe Integrationen](/de/docs/2_platform/20_external_integrations/).
:::

::: details Welchen Nutzen hat die Verwendung einer Open-Source-Plattform wie dem Swiss AI Hub für die breitere Schweizer KI-Community?
Unser **Ökosystemmodell** basiert auf Zusammenarbeit. Die Kernplattform ist Open-Source, was es Schweizer Organisationen
ermöglicht, Anstrengungen beim Aufbau und der Verbesserung der fundamentalen KI-Infrastruktur zu bündeln. Alle
profitieren von gemeinsamen Fortschritten, wodurch sich einzelne Organisationen darauf konzentrieren können,
einzigartige KI-Anwendungen für ihre spezifischen Bedürfnisse zu erstellen und so die gesamten KI-Fähigkeiten der
Schweiz zu stärken. Lesen Sie mehr über
[Das Ökosystemmodell](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details Wir sind besorgt über die Komplexität der Einrichtung und Verwaltung einer selbst gehosteten KI-Plattform. Ist der Swiss AI Hub schwierig zu bedienen?
Die Swiss AI Hub Community hat die Plattform für **vereinfachte Bereitstellung und Verwaltung** konzipiert. Die
Installation erfolgt mit einem einzigen Befehl, und kritische Infrastrukturherausforderungen wie Authentifizierung,
Monitoring und Skalierungskonfiguration sind out-of-the-box gelöst. Dies reduziert die betriebliche Komplexität
erheblich im Vergleich zum Aufbau einer KI-Infrastruktur von Grund auf oder der Verwaltung komplizierter
Cloud-Anbieterdienste. Überprüfen Sie den [Schnellstart](/de/docs/2_platform/1_quick_start/).
:::
