```yaml
# https://vitepress.dev/reference/default-theme-home-page
layout: home
source_sha: "5c4d1bf457b2bda776a564a150c7d4662bf3eeed11901c2b82451f49d0559f28"

hero:
  name: Swiss AI Hub
  text: Die offene KI-Plattform, die Sie besitzen und kontrollieren
  tagline: Komplette Infrastruktur für KI in der Produktion. Deployen Sie in Ihrem Rechenzentrum. Bauen Sie mit Vertrauen. Bewahren Sie Ihre Daten in der Schweiz auf.
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
    details: Erstklassige Open-Source-Tools (LiteLLM, Milvus, LlamaIndex) integriert und einsatzbereit. Wenn sie sich weiterentwickeln, profitieren Sie davon. Kein Vendor Lock-in, keine Lizenzgebühren, keine Plattformbeschränkungen. Setzen Sie auf das Ökosystem, nicht auf einen einzelnen Anbieter.
  - title: Besitzen Sie die Plattform, mieten Sie sie nicht
    details: Komplette Infrastruktur, die Sie deployen und kontrollieren. Keine SaaS-Abonnements, keine Code-Bibliothek. Authentifizierung, Monitoring, Datenbanken, UIs – alles inklusive. Vollständigkeit auf Azure AI-Niveau mit Besitz auf LangChain-Niveau.
  - title: 30 Minuten bis zur Produktions-KI
    details: Ein einziger Befehl deployt alles. LLM-Gateway, Vektorsuche, Chat-Interface, Authentifizierung, Monitoring. Vorkonfigurierte Agents funktionieren sofort. Keine Cloud-Provisionierung, kein komplexes Setup, keine Infrastruktur-Entwicklung.
  - title: Eine GPU, keine Cloud-Abhängigkeit
    details: Betreiben Sie die gesamte Plattform – Chat, Embeddings, Reranking, OCR, Speech – auf einer einzelnen NVIDIA RTX 6000 Pro. Keine API-Schlüssel, kein ausgehender Datenverkehr, keine Cloud-Rechnungen. Volle KI-Fähigkeit in einem Air-Gapped-Rack. Wenn Cloud-Zugang verfügbar ist, skaliert Sie die Swiss LLM Cloud ohne Code-Änderungen weiter.
  - title: Transparente, keine Black-Box-KI
    details: Jeder Agent folgt expliziten Workflows. Jede Entscheidung ist nachvollziehbar und auditierbar. Jede Kosten werden verfolgt. Sehen Sie genau, warum die KI eine bestimmte Antwort gegeben hat. Vertrauen durch Transparenz, nicht durch Versprechungen. Gebaut für Schweizer Standards.
  - title: Kollektive Stärke durch Zusammenarbeit
    details: Schweizer Organisationen teilen Infrastruktur, konkurrieren um Innovation. Bringen Sie Verbesserungen ein, profitieren Sie von denen anderer. Bauen Sie gemeinsam, was keine einzelne Organisation sich leisten könnte. Der Schweizer KI-Vorteil.
---

<div style="height: 500px"></div>

## FAQ

::: details Wie kann unsere Schweizer Organisation KI deployen und gleichzeitig alle Daten On-Premise behalten?
Der Swiss AI Hub ist eine **Open-Source-KI-Plattform**, die *Sie* deployen und kontrollieren. Sie ist speziell für die
**On-Premise-Installation** in Ihrem eigenen Schweizer Rechenzentrum konzipiert. Das bedeutet, Sie können die gesamte KI-Infrastruktur –
einschliesslich Sprachmodell-Gateways und Wissensdatenbanken – auf Ihren Servern betreiben und so vollständige Kontrolle und Datenisolation gewährleisten.
Weitere Details finden Sie in unseren [Deployment-Optionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie können wir KI nutzen und dabei die Schweizer Datenschutzgesetze wie FADP (revDSG) einhalten?
Die Sicherstellung der **Schweizer Datenhoheit** ist ein Kernprinzip der Swiss AI Hub Community. Da *Sie* die
Plattform deployen, wählen Sie *wo* sie läuft – entweder auf Ihren eigenen Servern in der Schweiz oder in vertrauenswürdigen Schweizer Rechenzentren.
Durch die Verwendung lokaler Large Language Models (LLMs) bleibt die Verarbeitung sensibler Daten vollständig unter Ihrer Kontrolle,
was Ihnen hilft, die **FADP (revDSG) Anforderungen** zu erfüllen. Lesen Sie mehr über unser Engagement in
[Der Schweizer Weg: Datenschutz, Souveränität und Transparenz](/de/docs/1_vision_and_positioning/1_introduction/3_the_swiss_way/).
:::

::: details Was ist eine vertrauenswürdige Open-Source-KI-Plattform als Alternative zu grossen Cloud-Anbietern wie Azure AI oder Google Vertex AI?
Der Swiss AI Hub bietet eine **Open-Source-Alternative**, die von einer Community entwickelt wurde, die sich auf Benutzerkontrolle konzentriert.
Die Kerninfrastruktur der Plattform ist unter Apache 2.0 lizenziert, was bedeutet, dass *Sie* Ihre Bereitstellung besitzen.
Dies ermöglicht Ihnen, **Vendor Lock-in** zu vermeiden und gibt Ihnen Freiheit von spezifischen Ökosystemen und unvorhersehbaren Preisstrukturen,
die bei grossen Cloud-Anbietern üblich sind. Sehen Sie, wie wir uns in der [Vergleichsmatrix](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/1_comparison_matrix_light/) vergleichen.
:::

::: details Wie können wir sicherstellen, dass KI-Entscheidungen in unserem Schweizer Unternehmen nachvollziehbar und auditierbar sind?
Die Swiss AI Hub Community priorisiert **Transparenz für Vertrauen**. Unsere Plattform bietet umfassende Observability-Features.
Jeder Schritt, den ein KI-Agent unternimmt, ist sichtbar, Entscheidungen werden mit Kontext protokolliert und Kosten werden verfolgt.
Tools wie Langfuse ermöglichen die Nachverfolgung jeder Interaktion, sodass Sie immer verstehen können,
*warum* eine KI eine bestimmte Antwort gegeben hat, was für **Compliance und Auditing** entscheidend ist.
Entdecken Sie diese Funktionen unter [Auditierung & Observability](/de/docs/2_platform/12_auditing/).
:::

::: details Gibt es einen fertigen KI-Infrastruktur-Stack (Auth, Monitoring, Vektor-DBs), den wir selbst deployen können?
Ja, der Swiss AI Hub bietet einen **vollständigen, vorintegrierten KI-Infrastruktur-Stack**, den *Sie* deployen.
Er bündelt wesentliche Komponenten wie Authentifizierung, Monitoring, verschiedene Datenbanken (einschliesslich Vektordatenbanken für KI),
Datenverarbeitungs-Pipelines und Benutzeroberflächen sofort einsatzbereit. Dies löst viele gängige
**Herausforderungen in der Produktions-KI** vom ersten Tag an. Erfahren Sie mehr darüber in
[Der "Day 2"-Vorteil](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/2_the_day_2_advantage/).
:::

::: details Was ist der schnellste Weg, eine sichere, unternehmenstaugliche KI-Plattform in der Schweiz einzurichten?
Sie können die gesamte Swiss AI Hub Plattform in etwa **30 Minuten mit einem einzigen Befehl** deployen.
Als Open-Source-Plattform, die Sie selbst installieren, enthält sie vorgefertigte Agents und Interfaces,
die sofort funktionieren und einen schnellen Time-to-Value ohne komplexe Cloud-Konfigurationen bieten.
Beginnen Sie mit der [Schnellstart-Anleitung](/de/docs/2_platform/1_quick_start/).
:::

::: details Wie können unsere Mitarbeiter sicher auf unternehmensspezifische KI-Hilfe direkt in Microsoft Teams oder Slack zugreifen?
Die Swiss AI Hub Plattform umfasst **eingebaute Integrationen für Microsoft Teams und Slack**. Dies ermöglicht Ihren Mitarbeitern,
sicher mit KI-Agents zu interagieren, die Zugriff auf relevantes Unternehmenswissen haben,
direkt in den Kollaborationstools, die sie täglich verwenden, wodurch der Workflow verbessert wird. Details finden Sie unter
[Slack & Teams-Integrationen](/de/docs/2_platform/17_slack_teams_integrations/).
:::

::: details Wie kann unsere Organisation den Zugriff und die Nutzung verschiedener KI-Modelle (z.B. GPT-4, Gemini, lokale Modelle) zentral verwalten?
Der Swiss AI Hub enthält einen **integrierten LLM-Proxy (LiteLLM)**, der als vereinheitlichtes Gateway zu all Ihren konfigurierten KI-Modellen fungiert.
Sie können den Modellzugriff zentral verwalten, Anfragen basierend auf Richtlinien weiterleiten, Kosten über verschiedene Anbieter hinweg verfolgen
und sogar Failover-Mechanismen einrichten. Weitere Informationen finden Sie unter
[Sprachmodelle](/de/docs/2_platform/13_language_models/).
:::

::: details Wie können wir die Betriebskosten, die mit der Nutzung von KI-Modellen verbunden sind, effektiv kontrollieren und vorhersagen?
Unsere Community hat den Swiss AI Hub mit Blick auf **transparente Kostenkontrolle** entwickelt.
Der integrierte LLM-Proxy verfolgt die Token-Nutzung für jede Interaktion, pro Benutzer oder Agent.
Sie können die KI-Ausgaben in Echtzeit-Dashboards überwachen und Budgets konfigurieren, um unerwartete Kosten zu vermeiden.
Erfahren Sie mehr über [Kostenkontrolle](/de/docs/2_platform/14_cost_control/).
:::

::: details Unser Schweizer Unternehmen hat strenge Datenschutzregeln, die die Nutzung öffentlicher KI-Clouds verhindern. Welche sichere KI-Lösung können wir verwenden?
Der Swiss AI Hub ist ideal dafür. Als Open-Source-Plattform, die *Sie* deployen, können Sie sie **vollständig On-Premise** installieren und
**lokale, selbst gehostete LLMs** verwenden. Dies stellt sicher, dass absolut keine Daten (Prompts, Antworten, Dokumente)
jemals Ihren sicheren Netzwerkperimeter verlassen. Überprüfen Sie unsere umfassenden [Sicherheitsfunktionen](/de/docs/2_platform/20_security/).
:::

::: details Wir haben KI-Prototypen, die Frameworks wie LangChain verwenden, finden es aber schwierig, sie zuverlässig in der Produktion zu deployen. Wie kann der Swiss AI Hub helfen?
Der Swiss AI Hub bietet die notwendige **produktionsreife Infrastruktur**, die Entwicklungsframeworks oft fehlt.
Während LangChain hilft, die KI-Logik aufzubauen, liefert unsere Plattform die wesentlichen umgebenden Komponenten:
robuste Deployment-Mechanismen, Enterprise-Authentifizierung, Skalierung, Monitoring und Benutzeroberflächen,
die für einen **zuverlässigen Unternehmenseinsatz** erforderlich sind. Sehen Sie
[Unsere Lösung](/de/docs/1_vision_and_positioning/1_introduction/2_our_solution/).
:::

::: details Wie können wir KI-Agents sicher Fragen auf der Grundlage unserer internen Unternehmensdokumente (wie PDFs oder Word-Dateien) beantworten lassen?
Der Swiss AI Hub umfasst ein sicheres **Retrieval-Augmented Generation (RAG)-System**. Sie konfigurieren automatisierte
[Daten-Pipelines](/de/docs/2_platform/6_pipelines/), um Dokumente aus Ihren Quellen (z.B. SharePoint) aufzunehmen.
Diese Pipelines verarbeiten die Dokumente sicher und indizieren sie in einer Vektordatenbank,
*die Sie besitzen und kontrollieren*, wodurch Agents sicher auf Unternehmenswissen zugreifen können.
:::

::: details Verschiedene Teams in unserer Organisation verwenden diverse KI-Tools, wodurch Silos entstehen. Wie können wir einen einheitlichen, gesteuerten KI-Ansatz schaffen?
Der Swiss AI Hub kann als Ihre **zentrale, vereinheitlichte KI-Plattform** dienen.
Er bietet eine gemeinsame Infrastruktur, auf der alle Teams aufbauen können, stellt konsistente Governance- und Sicherheitsrichtlinien sicher,
bietet einheitliches Monitoring und umfasst eine [OpenAI-kompatible API](/de/docs/2_platform/18_api/1_openai_compatible_api/),
die die Integration mit vielen bestehenden Tools ermöglicht und so zur **Reduzierung der Fragmentierung** beiträgt.
:::

::: details Was ist ein effizienter und skalierbarer Weg, die Aufnahme und Vektor-Embeddings von Tausenden von Unternehmensdokumenten für KI zu handhaben?
Der Swiss AI Hub verwendet **Daten-Pipelines**, die mit dem robusten Orchestrator Dagster erstellt wurden.
Diese Pipelines automatisieren den gesamten Workflow: Verbindung zu Ihren Datenquellen, intelligentes Parsen verschiedener Dateiformate,
Erstellung semantischer Chunks, Generierung von Vektor-Embeddings und deren Indizierung in Ihrem Vektorspeicher (wie Milvus).
Details finden Sie im [Pipelines-Abschnitt](/de/docs/2_platform/6_pipelines/).
:::

::: details Können wir eine komplette KI-Plattform vollständig offline in einem Air-Gapped-Netzwerk innerhalb der Schweiz deployen und betreiben?
Ja. Wenn Sie den Swiss AI Hub **On-Premise** deployen und ihn so konfigurieren, dass er nur
**selbst gehostete Large Language Models** (LLMs) verwendet, kann die gesamte Plattform ohne externe Internetverbindung betrieben werden.
Dies macht sie geeignet für **Air-Gapped-Umgebungen** mit höchsten Sicherheitsanforderungen. Siehe
[Deployment-Optionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).
:::

::: details Wie stellen wir sicher, dass die KI-Agents vertrauenswürdige Antworten liefern und nicht einfach "halluzinieren" oder sich Dinge ausdenken?
Vertrauen ist von größter Bedeutung. Swiss AI Hub **Agents** sind so konzipiert, dass sie expliziten, definierten Workflows folgen.
Sie verwenden primär **Retrieval-Augmented Generation (RAG)**, was bedeutet, dass ihre Antworten auf Informationen basieren,
die aus *Ihren* verifizierten Unternehmensdokumenten abgerufen werden. Agents **zitieren auch ihre Quellen**, und eingebaute "Guardrails" prüfen,
ob die abgerufenen Informationen ausreichen, um **zuverlässige, faktenbasierte Antworten** zu gewährleisten.
Erfahren Sie mehr über [Agents](/de/docs/2_platform/5_agents/).
:::

::: details Ist es möglich, dass KI-Agents auf dieser Plattform bei komplexen Aufgaben menschliche Experten um Hilfe oder Genehmigung bitten?
Ja, unsere Plattform unterstützt **Human-in-the-Loop (HITL)** und **Bot-in-the-Loop (BITL)** Workflows.
Ein KI-Agent kann so konzipiert werden, dass er seinen Prozess an einem bestimmten Schritt pausiert,
eine Anfrage zur Eingabe oder Genehmigung an einen benannten menschlichen Experten sendet (zum Beispiel über eine Slack-Nachricht)
und dann seine Arbeit nahtlos fortsetzt, sobald der Mensch antwortet. Erkunden Sie
[Agent-Grundlagen](/de/docs/3_sdk/2_building_agents/1_agent_fundamentals/), die diese Muster ermöglichen.
:::

::: details Wie verbindet und integriert sich der Swiss AI Hub mit unserer bestehenden Unternehmenssoftware wie SharePoint oder internen Datenbanken?
Die Plattform bietet **flexible Integrationsmöglichkeiten**. KI-Agents können direkte API-Aufrufe an externe Systeme tätigen;
externe Systeme können Agents über die [Agenten-Interaktions-API](/de/docs/2_platform/18_api/2_agent_interaction_api/) der Plattform triggern;
automatisierte Daten-Pipelines können Wissen aus Quellen wie SharePoint synchronisieren;
und Standardprotokolle werden für benutzerdefinierte Verbindungen unterstützt. Siehe
[Externe Integrationen](/de/docs/2_platform/22_external_integrations/).
:::

::: details Wie profitiert die breitere Schweizer KI-Community von der Nutzung einer Open-Source-Plattform wie dem Swiss AI Hub?
Unser **Ökosystem-Modell** basiert auf Zusammenarbeit. Die Kernplattform ist Open-Source,
was es Schweizer Organisationen ermöglicht, ihre Anstrengungen beim Aufbau und der Verbesserung der grundlegenden KI-Infrastruktur zu bündeln.
Jeder profitiert von gemeinsamen Fortschritten, wodurch einzelne Organisationen ihre Ressourcen auf die Erstellung einzigartiger KI-Anwendungen
konzentrieren können, die auf ihre spezifischen Bedürfnisse zugeschnitten sind, und so die gesamten KI-Fähigkeiten der Schweiz stärken.
Lesen Sie mehr über [Das Ökosystem-Modell](/de/docs/1_vision_and_positioning/2_why_swiss_ai_hub/3_the_ecosystem_model/).
:::

::: details Wir sind besorgt über die Komplexität der Einrichtung und Verwaltung einer selbst gehosteten KI-Plattform. Ist der Swiss AI Hub schwierig zu bedienen?
Die Swiss AI Hub Community hat die Plattform für **vereinfachte Bereitstellung und Verwaltung** konzipiert.
Die Installation erfolgt mit einem einzigen Befehl, und kritische Infrastrukturherausforderungen wie Authentifizierung,
Monitoring und Skalierungskonfiguration werden sofort gelöst. Dies reduziert die betriebliche Komplexität im Vergleich
zum Aufbau einer KI-Infrastruktur von Grund auf oder der Verwaltung komplexer Cloud-Anbieterdienste erheblich.
Überprüfen Sie den [Schnellstart](/de/docs/2_platform/1_quick_start/).
:::
```
