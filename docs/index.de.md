---
# https://vitepress.dev/reference/default-theme-home-page
layout: home
source_sha: ce2d82fcfea5955b1aeb6f0b3bd5d6b03774074c365006dde1e0a84890659fe5

hero:
  name: Swiss AI Hub
  text: Die offene KI-Plattform, die Sie besitzen und kontrollieren
  tagline: Komplette Infrastruktur für produktive KI. Deployment in Ihrem Rechenzentrum. Mit Vertrauen entwickeln. Ihre Daten in der Schweiz behalten.
  actions:
    - theme: alt
      text: Unsere Vision
      link: /de/docs/1_vision_and_positioning/1_introduction/
    - theme: alt
      text: Warum Swiss AI Hub
      link: /de/docs/1_vision_and_positioning/1_introduction
    - theme: brand
      text: Plattformübersicht
      link: /de/docs/2_platform/2_architecture/

features:
  - title: Die Open-Source-KI-Wette
    details: Best-in-Class Open-Source-Tools (LiteLLM, Milvus, LlamaIndex) integriert und bereit. Wenn sie sich weiterentwickeln, profitieren Sie. Kein Vendor Lock-in, keine Lizenzgebühren, keine Plattformbeschränkungen. Setzen Sie auf das Ökosystem, nicht auf einen einzelnen Anbieter.
  - title: Die Plattform besitzen, nicht mieten
    details: Komplette Infrastruktur, die Sie deployen und kontrollieren. Keine SaaS-Abonnements, keine Code-Bibliothek. Authentifizierung, Monitoring, Datenbanken, UIs – alles inklusive. Azure AI-Niveau an Vollständigkeit mit LangChain-Niveau an Besitz.
  - title: 30 Minuten bis zur produktiven KI
    details: Ein Befehl deployt alles. LLM Gateway, Vektorsuche, Chat-Interface, Authentifizierung, Monitoring. Vorgefertigte Agents funktionieren sofort. Keine Cloud-Bereitstellung, keine komplexe Einrichtung, keine Infrastruktur-Entwicklung.
  - title: Eine GPU, keine Cloud-Abhängigkeit
    details: Betreiben Sie die gesamte Plattform – Chat, Embeddings, Reranking, OCR, Speech – auf einer einzigen NVIDIA RTX 6000 Pro. Keine API-Keys, kein Egress-Traffic, keine Cloud-Rechnungen. Volle KI-Fähigkeit in einem Air-Gapped-Rack. Wenn Cloud-Zugriff verfügbar ist, skaliert Sie die Swiss LLM Cloud ohne Code-Änderungen weiter.
  - title: Transparente, nicht Black-Box-KI
    details: Jeder Agent folgt expliziten Workflows. Jede Entscheidung ist nachvollziehbar und auditierbar. Jede Kostenstelle wird verfolgt. Sehen Sie genau, warum die KI eine Antwort gegeben hat. Vertrauen durch Transparenz, nicht durch Versprechen. Gebaut für Schweizer Standards.
  - title: Kollektive Stärke durch Zusammenarbeit
    details: Schweizer Organisationen teilen Infrastruktur und konkurrieren bei Innovationen. Tragen Sie zu Verbesserungen bei, profitieren Sie von denen anderer. Bauen Sie gemeinsam, was keine einzelne Organisation allein leisten könnte. Der Schweizer KI-Vorteil.
---

<div style="height: 500px"></div>

## FAQ

::: details Wie kann unsere Schweizer Organisation KI deployen und dabei alle Daten On-Premise halten?
Der Swiss AI Hub ist eine **Open-Source-KI-Plattform**, die *Sie* deployen und kontrollieren. Er wurde speziell für die
**On-Premise-Installation** in Ihrem eigenen Schweizer Rechenzentrum entwickelt. Das bedeutet, dass Sie die gesamte
KI-Infrastruktur – einschliesslich Sprachmodell-Gateways und Wissensdatenbanken – auf Ihren Servern betreiben können,
was vollständige Kontrolle und Datenisolation gewährleistet. Weitere Details finden Sie in unseren
[Deployment-Optionen](docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie können wir KI nutzen und dabei die Schweizer Datenschutzgesetze wie FADP (revDSG) einhalten?
Die Gewährleistung der **Schweizer Datenhoheit** ist ein Kernprinzip der Swiss AI Hub Community. Da *Sie* die Plattform
deployen, wählen Sie *wo* sie läuft – entweder auf Ihren eigenen Servern in der Schweiz oder in vertrauenswürdigen
Schweizer Rechenzentren. Durch die Verwendung lokaler Large Language Models (LLMs) bleibt die Verarbeitung sensibler
Daten vollständig unter Ihrer Kontrolle, was Ihnen hilft, die **FADP (revDSG) Anforderungen** zu erfüllen. Lesen Sie
mehr über unser Engagement in
[Der Schweizer Weg: Datenschutz, Souveränität und Transparenz](docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details Was ist eine vertrauenswürdige, quelloffene KI-Plattformalternative zu grossen Cloud-Anbietern wie Azure AI oder Google Vertex AI?
Der Swiss AI Hub bietet eine von einer auf Nutzerkontrolle fokussierten Community entwickelte
**Open-Source-Alternative**. Die Plattform-Laufzeit ist unter Apache 2.0 lizenziert (die UI und Backup-Orchestrierung
unter AGPL-3.0; eine vollständige Aufschlüsselung pro Paket finden Sie unter
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md)), was bedeutet, dass *Sie* Ihr Deployment
besitzen. Dies ermöglicht Ihnen, **Vendor Lock-in** zu vermeiden, und befreit Sie von spezifischen Ökosystemen und
unvorhersehbaren Preisstrukturen, die bei grossen Cloud-Anbietern üblich sind. Sehen Sie, wie wir uns vergleichen in der
[Vergleichsmatrix](docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/).
:::

::: details Wie können wir sicherstellen, dass KI-Entscheidungen in unserem Schweizer Unternehmen nachvollziehbar und auditierbar sind?
Die Swiss AI Hub Community priorisiert **Transparenz für Vertrauen**. Unsere Plattform bietet umfassende
Observability-Funktionen. Jeder Schritt, den ein KI-Agent unternimmt, ist sichtbar, Entscheidungen werden mit Kontext
protokolliert und Kosten verfolgt. Tools wie Langfuse ermöglichen das Tracing jeder Interaktion, sodass Sie stets
verstehen können, *warum* eine KI eine bestimmte Antwort gegeben hat, was für **Compliance und Auditing** entscheidend
ist. Erkunden Sie diese Funktionen unter [Auditing & Observability](docs/2_platform/12_auditing/).
:::

::: details Gibt es einen vorgefertigten KI-Infrastruktur-Stack (Auth, Monitoring, Vector-DBs), den wir selbst deployen können?
Ja, der Swiss AI Hub bietet einen **vollständigen, vorintegrierten KI-Infrastruktur-Stack**, den *Sie* deployen. Er
bündelt wesentliche Komponenten wie Authentifizierung, Monitoring, verschiedene Datenbanken (einschliesslich
Vektordatenbanken für KI), Datenverarbeitungspipelines und Benutzeroberflächen direkt out-of-the-box. Dies löst viele
gängige **Produktions-KI-Herausforderungen** von Tag eins an. Erfahren Sie mehr dazu im
[Der 'Day 2'-Vorteil](docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details Was ist der schnellste Weg, um eine sichere, unternehmensreife KI-Plattform in der Schweiz einzurichten?
Sie können die gesamte Swiss AI Hub Plattform in etwa **30 Minuten mit einem einzigen Befehl** deployen. Als
Open-Source-Plattform, die Sie selbst installieren, enthält sie vorgefertigte Agents und Schnittstellen, die sofort
funktionieren und eine schnelle Wertschöpfung ohne komplexe Cloud-Konfigurationen bieten. Beginnen Sie mit dem
[Quick Start Guide](docs/2_platform/1_quick_start/).
:::

::: details Wie können unsere Mitarbeitenden sicher auf unternehmensspezifische KI-Hilfe direkt in Microsoft Teams oder Slack zugreifen?
Die Swiss AI Hub Plattform umfasst **eingebaute Integrationen für Microsoft Teams und Slack**. Dies ermöglicht Ihren
Mitarbeitenden, sicher mit KI-Agents zu interagieren, die Zugriff auf relevantes Unternehmenswissen haben, direkt in den
Kollaborationstools, die sie täglich nutzen, wodurch der Workflow verbessert wird. Weitere Details finden Sie unter
[Slack & Teams Integrationen](docs/2_platform/17_slack_teams_integrations/).
:::

::: details Wie kann unsere Organisation den Zugriff und die Nutzung verschiedener KI-Modelle (z.B. GPT-4, Gemini, lokale Modelle) zentral verwalten?
Der Swiss AI Hub enthält einen **integrierten LLM Proxy (LiteLLM)**, der als vereinheitlichtes Gateway zu all Ihren
konfigurierten KI-Modellen fungiert. Sie können den Modellzugriff zentral verwalten, Anfragen basierend auf Richtlinien
routen, Kosten über verschiedene Anbieter hinweg verfolgen und sogar Failover-Mechanismen einrichten. Weitere
Informationen finden Sie unter [Sprachmodelle](docs/2_platform/13_language_models/).
:::

::: details Wie können wir die Betriebskosten, die mit der Nutzung von KI-Modellen verbunden sind, effektiv kontrollieren und vorhersagen?
Unsere Community hat den Swiss AI Hub mit Blick auf **transparente Kostenkontrolle** entwickelt. Der integrierte LLM
Proxy verfolgt die Token-Nutzung für jede Interaktion, pro Benutzer oder Agent. Sie können die KI-Ausgaben in
Echtzeit-Dashboards überwachen und Budgets konfigurieren, um unerwartete Kosten zu vermeiden. Erfahren Sie mehr über
[Kostenkontrolle](docs/2_platform/14_cost_control/).
:::

::: details Unser Schweizer Unternehmen hat strenge Datenschutzregeln, die die Nutzung öffentlicher KI-Clouds verhindern. Welche sichere KI-Lösung können wir nutzen?
Der Swiss AI Hub ist hierfür ideal. Als Open-Source-Plattform, die *Sie* deployen, können Sie sie **vollständig
On-Premise** installieren und **lokale, selbst gehostete LLMs** verwenden. Dies stellt sicher, dass absolut keine Daten
(Prompts, Antworten, Dokumente) jemals Ihr sicheres Netzwerk verlassen. Prüfen Sie unsere umfassenden
[Sicherheitsfunktionen](docs/2_platform/20_security/).
:::

::: details Wir haben KI-Prototypen, die Frameworks wie LangChain verwenden, finden es aber schwierig, diese zuverlässig in der Produktion zu deployen. Wie kann der Swiss AI Hub helfen?
Der Swiss AI Hub bietet die notwendige **produktionsreife Infrastruktur**, die Entwicklungs-Frameworks oft fehlt.
Während LangChain beim Aufbau der KI-Logik hilft, liefert unsere Plattform die wesentlichen umgebenden Komponenten:
robuste Deployment-Mechanismen, Unternehmensauthentifizierung, Skalierung, Monitoring und Benutzeroberflächen, die für
einen **zuverlässigen Unternehmenseinsatz** benötigt werden. Siehe
[Unsere Lösung](docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details Wie können wir KI-Agents sicher Fragen basierend auf unseren internen Unternehmensdokumenten (wie PDFs oder Word-Dateien) beantworten lassen?
Der Swiss AI Hub umfasst ein sicheres **Retrieval-Augmented Generation (RAG)-System**. Sie konfigurieren automatisierte
[Data Pipelines](docs/2_platform/6_pipelines/), um Dokumente aus Ihren Quellen (wie SharePoint) zu ingestieren. Diese
Pipelines verarbeiten die Dokumente sicher und indizieren sie in einer Vektordatenbank, *die Sie besitzen und
kontrollieren*, sodass Agents sicher auf Unternehmenswissen zugreifen können.
:::

::: details Verschiedene Teams in unserer Organisation verwenden unterschiedliche KI-Tools und schaffen so Silos. Wie können wir einen vereinheitlichten, gesteuerten KI-Ansatz schaffen?
Der Swiss AI Hub kann als Ihre **zentrale, vereinheitlichte KI-Plattform** dienen. Er bietet eine gemeinsame
Infrastruktur, auf der alle Teams aufbauen können, gewährleistet konsistente Governance- und Sicherheitsrichtlinien,
bietet einheitliches Monitoring und enthält eine
[OpenAI-Kompatible API](docs/2_platform/18_api/1_openai_compatible_api/), die die Integration mit vielen bestehenden
Tools ermöglicht und so zur **Reduzierung der Fragmentierung** beiträgt.
:::

::: details Was ist ein effizienter und skalierbarer Weg, um die Ingestion und Vektor-Embeddings von Tausenden von Unternehmensdokumenten für KI zu handhaben?
Der Swiss AI Hub nutzt **Data Pipelines**, die mit dem robusten Orchestrator Dagster erstellt wurden. Diese Pipelines
automatisieren den gesamten Workflow: Verbinden mit Ihren Datenquellen, intelligentes Parsen verschiedener Dateiformate,
Erstellen semantischer Chunks, Generieren von Vektor-Embeddings und Indizieren dieser in Ihrem Vektor-Store (wie
Milvus). Details finden Sie im [Pipelines-Abschnitt](docs/2_platform/6_pipelines/).
:::

::: details Können wir eine komplette KI-Plattform vollständig offline in einem Air-Gapped-Netzwerk in der Schweiz deployen und betreiben?
Ja. Wenn Sie den Swiss AI Hub **On-Premise** deployen und ihn so konfigurieren, dass er ausschliesslich **selbst
gehostete Large Language Models** (LLMs) verwendet, kann die gesamte Plattform ohne externe Internetverbindung betrieben
werden. Dies macht sie geeignet für **Air-Gapped-Umgebungen** mit den höchsten Sicherheitsanforderungen. Siehe
[Deployment-Optionen](docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass die KI-Agents vertrauenswürdige Antworten liefern und nicht einfach "halluzinieren" oder sich Dinge ausdenken?
Vertrauen ist von grösster Bedeutung. Swiss AI Hub **Agents** sind darauf ausgelegt, explizite, definierte Workflows zu
befolgen. Sie nutzen hauptsächlich **Retrieval-Augmented Generation (RAG)**, was bedeutet, dass ihre Antworten auf
Informationen basieren, die aus *Ihren* verifizierten Unternehmensdokumenten abgerufen wurden. Agents **zitieren auch
ihre Quellen**, und integrierte "Guardrails" prüfen, ob die abgerufenen Informationen ausreichen, um **zuverlässige,
faktenbasierte Antworten** zu gewährleisten. Erfahren Sie mehr über [Agents](docs/2_platform/5_agents/).
:::

::: details Ist es möglich, dass KI-Agents auf dieser Plattform während komplexer Aufgaben menschliche Experten um Hilfe oder Genehmigung bitten?
Ja, unsere Plattform unterstützt **Human-in-the-Loop (HITL)** und **Bot-in-the-Loop (BITL)** Workflows. Ein KI-Agent
kann so konzipiert werden, dass er seinen Prozess an einem bestimmten Schritt pausiert, eine Anfrage für Eingabe oder
Genehmigung an einen bestimmten menschlichen Experten sendet (zum Beispiel über eine Slack-Nachricht) und dann seine
Arbeit nahtlos fortsetzt, sobald der Mensch antwortet. Entdecken Sie die
[Agent Fundamentals](docs/3_sdk/2_building_agents/1_agent_fundamentals/), die diese Muster ermöglichen.
:::

::: details Wie verbindet und integriert sich der Swiss AI Hub mit unserer bestehenden Unternehmenssoftware wie SharePoint oder internen Datenbanken?
Die Plattform bietet **flexible Integrationsoptionen**. KI-Agents können direkte API-Aufrufe an externe Systeme tätigen;
externe Systeme können Agents über die [Agent Interaction API](docs/2_platform/18_api/2_agent_interaction_api/) der
Plattform triggern; automatisierte Data Pipelines können Wissen aus Quellen wie SharePoint synchronisieren; und
Standardprotokolle werden für benutzerdefinierte Verbindungen unterstützt. Siehe
[Externe Integrationen](docs/2_platform/22_external_integrations/).
:::

::: details Wie profitiert die breitere Schweizer KI-Community von der Nutzung einer Open-Source-Plattform wie dem Swiss AI Hub?
Unser **Ökosystemmodell** basiert auf Zusammenarbeit. Die Kernplattform ist Open-Source und ermöglicht es Schweizer
Organisationen, ihre Anstrengungen beim Aufbau und der Verbesserung der grundlegenden KI-Infrastruktur zu bündeln. Alle
profitieren von gemeinsamen Fortschritten, wodurch einzelne Organisationen ihre Ressourcen auf die Erstellung
einzigartiger KI-Anwendungen konzentrieren können, die ihren spezifischen Bedürfnissen entsprechen und die gesamten
KI-Fähigkeiten der Schweiz stärken. Lesen Sie mehr über
[Das Ökosystemmodell](docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details Wir sind besorgt über die Komplexität der Einrichtung und Verwaltung einer selbst gehosteten KI-Plattform. Ist der Swiss AI Hub schwierig zu bedienen?
Die Swiss AI Hub Community hat die Plattform für **vereinfachtes Deployment und Management** konzipiert. Die
Installation erfolgt mit einem einzigen Befehl, und kritische Infrastrukturherausforderungen wie Authentifizierung,
Monitoring und Skalierungskonfiguration werden out-of-the-box gelöst. Dies reduziert die operative Komplexität erheblich
im Vergleich zum Aufbau einer KI-Infrastruktur von Grund auf oder der Verwaltung komplexer Cloud-Anbieterdienste. Prüfen
Sie den [Quick Start](docs/2_platform/1_quick_start/).
:::
