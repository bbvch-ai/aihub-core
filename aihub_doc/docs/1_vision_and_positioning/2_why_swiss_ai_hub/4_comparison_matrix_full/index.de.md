---
title: Vollständige Wettbewerbsanalyse
source_sha: 80bb86cdffdb24721dacb82a64a580592cb768c7fd7c862ce08fcc4815a5d106
---

# Vollständige Wettbewerbsanalyse

Diese umfassende Analyse vergleicht den Swiss AI Hub mit seinen Wettbewerbern auf dem Markt, die in Plattformen,
Frameworks und Lösungen kategorisiert sind.

## Bibliotheken und Frameworks

Dies sind entwicklerorientierte Tools und Frameworks, die Bausteine für KI-Anwendungen bereitstellen. Sie bieten
Flexibilität und Kontrolle, erfordern jedoch einen erheblichen Entwicklungsaufwand, um vollständige, produktionsreife
Systeme zu erstellen.

| Framework        | Datenhoheit | Kalkulierbare Kosten | Vertrauen in Ergebnisse | Time-to-Value | Tool-Integration | Zugänglichkeit der Fähigkeiten | Skalierbarkeit | Herstellerunabhängigkeit | Einheitliche Governance | Produktionszuverlässigkeit | Visuelle Entwicklung | Keine Wartung |
| :--------------- | :---------: | :------------------: | :---------------------: | :-----------: | :--------------: | :----------------------------: | :------------: | :----------------------: | :---------------------: | :------------------------: | :------------------: | :-----------: |
| **Swiss AI Hub** |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ✅            |           ✅            |             ✅             |          ❌          |      ❌       |
| LangChain        |     ⚠️      |          ❌          |           ⚠️            |      ❌       |        ✅        |               ⚠️               |       ❌       |            ✅            |           ❌            |             ❌             |          ⚠️          |      ❌       |
| LangGraph        |     ⚠️      |          ⚠️          |           ✅            |      ❌       |        ⚠️        |               ❌               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |
| LlamaIndex       |     ⚠️      |          ❌          |           ⚠️            |      ⚠️       |        ✅        |               ⚠️               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |
| Semantic Kernel  |     ⚠️      |          ⚠️          |           ⚠️            |      ❌       |        ⚠️        |               ✅               |       ❌       |            ⚠️            |           ❌            |             ❌             |          ❌          |      ❌       |
| AutoGen          |     ⚠️      |          ⚠️          |           ⚠️            |      ⚠️       |        ⚠️        |               ✅               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |
| CrewAI           |     ✅      |          ⚠️          |           ⚠️            |      ⚠️       |        ⚠️        |               ⚠️               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |
| Haystack         |     ⚠️      |          ⚠️          |           ⚠️            |      ⚠️       |        ⚠️        |               ✅               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |
| DSPy             |     ⚠️      |          ❌          |           ⚠️            |      ❌       |        ❌        |               ❌               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |

### Details zu den Bibliotheken

::: details LangChain
LangChain ist eine leistungsstarke Bibliothek für die Entwicklung von LLM-Anwendungen, aber keine Plattform. Obwohl es
sich hervorragend eignet, Abstraktionen und Integrationen für die KI-Entwicklung bereitzustellen, überlässt es Ihnen
Bereitstellung, Überwachung, Authentifizierung, Kostenkontrolle und Benutzeroberflächen vollständig selbst. Sie können
Souveränität erreichen, indem Sie Ihren Code überall bereitstellen, müssen aber die gesamte Infrastruktur selbst
aufbauen. LangSmith fügt Observability hinzu, erfordert aber eine separate Einrichtung und ein Abonnement.

**Wählen Sie LangChain, wenn** Sie über starke Engineering-Teams verfügen, die maximale Flexibilität wünschen und bereit
sind, alle Infrastrukturkomponenten von Grund auf neu zu erstellen. Sie benötigen eine benutzerdefinierte KI-Logik, die
nicht in Standardmuster passt, oder Sie entwickeln ein spezialisiertes KI-Produkt, bei dem das Framework nur eine
Komponente ist.

**Wählen Sie Swiss AI Hub, wenn** Sie die Leistungsfähigkeit von Frameworks wie LangChain wünschen, aber mit einer
kompletten Plattform, die Bereitstellung, Authentifizierung, Überwachung, Benutzeroberflächen und Governance sofort
abdeckt. Sie erhalten die gleiche Entwicklungsflexibilität, jedoch ohne den gesamten Infrastrukturaufwand.
:::

::: details LangGraph
LangGraph zeichnet sich durch den Aufbau zustandsbehafteter, beobachtbarer Agenten-Workflows mit ausgeklügelter
Kontrollflusssteuerung aus. Als Python-Bibliothek bietet es hervorragende Abstraktionen für die Agentenentwicklung,
erfordert jedoch, dass Sie die gesamte Infrastruktur, Bereitstellung, Überwachung, Authentifizierung und
Benutzeroberflächen selbst aufbauen. Sie erhalten die Agentenlogik, nicht die Plattform, um sie auszuführen.

**Wählen Sie LangGraph, wenn** Sie ausgeklügelte Multi-Agenten-Workflows mit komplexem Zustandsmanagement benötigen und
über die Ressourcen verfügen, um eine komplette Plattform darum herum aufzubauen. Ihr Anwendungsfall erfordert
benutzerdefinierte Agentenarchitekturen, die nicht in Standardmuster passen.

**Wählen Sie Swiss AI Hub, wenn** Sie fortschrittliche Agentenfunktionen wünschen, aber auch sofort
Unternehmensfunktionen wie Authentifizierung, Überwachung, Kostenkontrolle und Benutzeroberflächen benötigen. Sie
erhalten ausgeklügelte Workflows sowie eine produktionsreife Plattform ohne Entwicklungsaufwand.
:::

::: details LlamaIndex
LlamaIndex zeichnet sich durch RAG und Datenaufnahme mit ausgeklügelten Dokumentverarbeitungs- und Abrufmuster aus. Als
Python-Bibliothek bietet es leistungsstarke Abstraktionen, aber keine Infrastruktur – Sie müssen Bereitstellung,
Authentifizierung, Überwachung und Benutzeroberflächen weiterhin selbst verwalten. Obwohl Sie Souveränität und
Observability durch den Aufbau darum herum erreichen können, sind dies keine integrierten Funktionen.

**Wählen Sie LlamaIndex, wenn** Sie ein spezialisiertes RAG-System mit einzigartigen Datenverarbeitungsanforderungen
aufbauen und über die Engineering-Kapazitäten verfügen, um die gesamte unterstützende Infrastruktur zu erstellen. Ihre
Dokumentverarbeitungsanforderungen sind stark angepasst.

**Wählen Sie Swiss AI Hub, wenn** Sie leistungsstarke RAG-Funktionen (basierend auf LlamaIndex) wünschen, jedoch mit
unternehmensreifer Bereitstellung, Authentifizierung, Datengovernance und Benutzeroberflächen. Sie erhalten die gleiche
RAG-Leistung mit vollständigen Plattformfunktionen von Tag eins an.
:::

::: details Semantic Kernel
Semantic Kernel ist Microsofts gut konzipiertes Orchestrierungs-Framework, das hervorragende Abstraktionen für die
KI-Entwicklung bietet. Als Bibliothek bietet es leistungsstarke Planungs- und Plugin-Fähigkeiten und lässt sich gut in
Azure-Dienste integrieren.

**Wählen Sie Semantic Kernel, wenn** Sie tief in das Microsoft-Ökosystem investiert sind, ausgeklügelte
KI-Planungsfunktionen benötigen und über die Ressourcen verfügen, um eine Produktionsinfrastruktur aufzubauen. Sie
wünschen Microsofts KI-Abstraktionen mit benutzerdefinierter Plattformentwicklung.

**Wählen Sie Swiss AI Hub, wenn** Sie Unternehmens-KI-Funktionen wünschen, ohne an Microsofts Ökosystem gebunden zu sein
oder die Infrastruktur selbst aufbauen zu müssen. Sie erhalten ähnliche Orchestrierungsleistung mit vollständiger
Datenhoheit, transparenten Kosten und einer sofort einsatzbereiten Plattform.
:::

::: details AutoGen
AutoGen zeichnet sich durch Multi-Agenten-Konversationsmuster aus und bietet hervorragende Abstraktionen für komplexe
Agenteninteraktionen. Als Python-Bibliothek überlässt es Bereitstellung, Überwachung, Authentifizierung und
Produktionsabläufe vollständig dem Entwickler. Obwohl Sie Datenhoheit und Integration durch den Aufbau darum herum
erreichen können, sind diese Funktionen nicht inhärent im Framework enthalten.

**Wählen Sie AutoGen, wenn** Sie spezialisierte Multi-Agenten-Konversationsmuster benötigen und das Engineering-Team
haben, um eine komplette Produktionsumgebung aufzubauen. Ihr Anwendungsfall konzentriert sich auf die
Agent-zu-Agent-Kommunikation mit benutzerdefinierten Interaktionsmustern.

**Wählen Sie Swiss AI Hub, wenn** Sie Multi-Agenten-Funktionen innerhalb einer kompletten Unternehmensplattform
wünschen, die Bereitstellung, Governance, Authentifizierung und Überwachung automatisch abwickelt. Sie erhalten
Agentenkollaboration plus die Infrastruktur, um sie zuverlässig in der Produktion zu betreiben.
:::

::: details CrewAI
CrewAI ist eine Multi-Agenten-Orchestrierungsbibliothek, die den Aufbau kollaborativer KI-Teams vereinfacht und sich
hervorragend zur Definition von Agentenrollen und Workflows eignet. Es ist Open Source und läuft überall dort, wo Sie es
bereitstellen.

**Wählen Sie CrewAI, wenn** Sie mit Multi-Agenten-Szenarien experimentieren möchten und über starke
Entwicklungsfähigkeiten verfügen, um die unterstützende Infrastruktur aufzubauen. Ihr Fokus liegt auf
Agenten-Kollaborationsmustern und nicht auf der Produktionsbereitstellung.

**Wählen Sie Swiss AI Hub, wenn** Sie Multi-Agenten-Orchestrierung innerhalb einer vollständigen, produktionsreifen
Plattform wünschen, die Bereitstellung, Authentifizierung, Überwachung und Governance umfasst. Sie erhalten
Agentenkollaboration plus Unternehmensfunktionen, ohne die Infrastruktur von Grund auf neu aufbauen zu müssen.
:::

::: details Haystack
Haystack ist ein hervorragendes Open-Source-Framework zum Aufbau von RAG-Pipelines und Suchsystemen. Es bietet
leistungsstarke Abstraktionen für die Dokumentenverarbeitung und den Abruf, die die Bausteine für KI-Anwendungen sind.

**Wählen Sie Haystack, wenn** Sie spezialisierte Such- und RAG-Funktionen mit tiefgreifender Anpassung benötigen und
über die Ressourcen verfügen, um die gesamte unterstützende Infrastruktur aufzubauen. Ihre Suchanforderungen sind hoch
spezialisiert oder forschungsorientiert.

**Wählen Sie Swiss AI Hub, wenn** Sie leistungsstarke Such- und RAG-Funktionen (einschließlich Haystack-kompatibler
Muster) innerhalb einer kompletten Plattform wünschen, die Bereitstellung, Authentifizierung, Governance und
Benutzeroberflächen sofort bietet. Sie erhalten Suchleistung plus Unternehmensreife.
:::

::: details DSPy
DSPy ist ein leistungsstarkes Framework zur programmatischen Optimierung von LLM-Anwendungen durch automatisiertes
Prompt Engineering. Es zeichnet sich durch systematische Evaluierung und Prompt-Optimierung aus, was es ideal für
Forschung und Prototypen macht.

**Wählen Sie DSPy, wenn** Sie KI-Forschung betreiben oder fortschrittliche Prompt-Optimierungstechniken benötigen und
über die Ressourcen verfügen, um Produktionsinfrastruktur aufzubauen. Ihr Hauptaugenmerk liegt auf experimentellen
KI-Techniken und nicht auf bereitgestellten Anwendungen.

**Wählen Sie Swiss AI Hub, wenn** Sie eine produktionsreife Plattform zum Aufbau von KI-Systemen mit umfassender
Überwachung und Governance wünschen. Sie erhalten eine Unternehmensinfrastruktur für die Bereitstellung zuverlässiger
KI-Anwendungen, wobei Optimierung und Entwicklung jedoch Programmierkenntnisse und keine automatisierten Tools
erfordern.
:::

## Schweizer/Europäische KI-Anbieter

Dies sind KI-Plattformen und -Anbieter mit Sitz in der Schweiz oder Europa, die sich auf Datenhoheit, regulatorische
Compliance und regionale Datenschutzanforderungen konzentrieren. Sie priorisieren die Speicherung von Daten innerhalb
europäischer Gerichtsbarkeiten und bieten gleichzeitig verschiedene KI-Funktionen an.

| Framework           | Datenhoheit | Kalkulierbare Kosten | Vertrauen in Ergebnisse | Time-to-Value | Tool-Integration | Zugänglichkeit der Fähigkeiten | Skalierbarkeit | Herstellerunabhängigkeit | Einheitliche Governance | Produktionszuverlässigkeit | Visuelle Entwicklung | Keine Wartung |
| :------------------ | :---------: | :------------------: | :---------------------: | :-----------: | :--------------: | :----------------------------: | :------------: | :----------------------: | :---------------------: | :------------------------: | :------------------: | :-----------: |
| **Swiss AI Hub**    |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ✅            |           ✅            |             ✅             |          ❌          |      ❌       |
| Alpine AI           |     ✅      |          ❌          |           ⚠️            |      ❌       |        ❌        |               ❌               |       ❌       |            ❌            |           ⚠️            |             ❌             |          ❌          |      ❌       |
| Abacus Deep         |     ✅      |          ⚠️          |           ✅            |      ✅       |        ✅        |               ✅               |       ⚠️       |            ❌            |           ✅            |             ✅             |          ⚠️          |      ⚠️       |
| BrandBot (Begasoft) |     ✅      |          ❌          |           ⚠️            |      ⚠️       |        ⚠️        |               ⚠️               |       ⚠️       |            ⚠️            |           ✅            |             ⚠️             |          ❌          |      ❌       |
| Envoya AI           |     ✅      |          ✅          |           ⚠️            |      ⚠️       |        ⚠️        |               ⚠️               |       ⚠️       |            ⚠️            |           ⚠️            |             ❌             |          ⚠️          |      ❌       |
| Aleph Alpha         |     ✅      |          ❌          |           ✅            |      ⚠️       |        ⚠️        |               ❌               |       ⚠️       |            ✅            |           ⚠️            |             ⚠️             |          ❌          |      ❌       |
| owwn.ai             |     ✅      |          ❌          |           ⚠️            |      ⚠️       |        ⚠️        |               ⚠️               |       ❌       |            ⚠️            |           ⚠️            |             ❌             |          ❌          |      ❌       |
| PREM                |     ✅      |          ❌          |           ⚠️            |      ❌       |        ⚠️        |               ❌               |       ❌       |            ✅            |           ❌            |             ❌             |          ❌          |      ❌       |
| Private AI Suite    |     ✅      |          ❌          |           ⚠️            |      ⚠️       |        ⚠️        |               ⚠️               |       ⚠️       |            ⚠️            |           ✅            |             ⚠️             |          ⚠️          |      ❌       |

### Details zu Schweizer/Europäischen Anbietern

::: details Alpine AI
Alpine AI (SwissGPT) ist eine Schweizer KI-Plattform, die speziell auf kritische und regulierte Sektoren mit starkem
Compliance-Fokus abzielt. Sie zeichnen sich durch Schweizer Datenhoheit und regulatorische Compliance aus.

**Wählen Sie Alpine AI, wenn** Sie sich in einem stark regulierten Sektor befinden, der Schweizer Compliance erfordert.

**Wählen Sie Swiss AI Hub, wenn** Sie Schweizer Souveränität mit vollständiger Transparenz über Plattformfunktionen,
-architektur und -kosten wünschen. Sie erhalten regulatorische Compliance mit voller Einsicht in die Funktionsweise der
Plattform, was fundierte technische und geschäftliche Entscheidungen ermöglicht.
:::

::: details Abacus Deep
Abacus Deep ist eine umfassende Schweizer ERP-Plattform mit KI-gestützten Modulen für Dokumentenmanagement und autonome
Buchhaltung. Exklusiv in Schweizer Rechenzentren mit ISO 27001:2022 Zertifizierung gehostet, zeichnet es sich durch
Schweizer Compliance und Sicherheit aus. Als integrierte ERP-Lösung führt es jedoch zu einer erheblichen
Anbieterbindung.

**Wählen Sie Abacus Deep, wenn** Sie ein Schweizer KMU sind, das ein vollständiges ERP-System benötigt und KI-Funktionen
in seine Geschäftsprozesse integrieren möchte. Sie suchen eine All-in-One-Geschäftsmanagementlösung und keine dedizierte
KI-Plattform.

**Wählen Sie Swiss AI Hub, wenn** Sie kundenspezifische KI-Anwendungen erstellen möchten, die sich in Ihr bestehendes
ERP-System (einschließlich Abacus) integrieren lassen, ohne an die Geschäftssoftware eines einzelnen Anbieters gebunden
zu sein. Sie erhalten KI-Plattformflexibilität bei gleichzeitiger Wahrung der Schweizer Compliance und Datenhoheit.
:::

::: details BrandBot (Begasoft)
BrandBot ist eine zu 100 % in der Schweiz gehostete KI-Plattform mit ISO-Compliance und OpenAI-kompatiblen APIs, die auf
Schweizer Unternehmen und die öffentliche Verwaltung abzielt. Sie bietet eine starke Schweizer Regulierungskonformität,
Audit-Logging und rollenbasierte Zugriffskontrollen.

**Wählen Sie BrandBot, wenn** Sie eine in der Schweiz gehostete KI-Plattform mit OpenAI-kompatiblen APIs benötigen und
Ihre Anforderungen relativ unkompliziert sind. Sie legen Wert auf Einfachheit und Schweizer Hosting gegenüber
erweiterten Plattformfunktionen.

**Wählen Sie Swiss AI Hub, wenn** Sie Schweizer Hosting plus eine umfassende, unternehmensgerechte Plattform mit
erweiterten Funktionen wie Workflow-Orchestrierung, Datenpipelines, Observability und erweiterbarer Architektur
wünschen. Sie erhalten Schweizer Souveränität mit Plattformvollständigkeit und Transparenz.
:::

::: details Envoya AI
Envoya AI ist eine Schweizer KI-Plattform, die umfassende Unternehmens-Tools und Schweizer Rechenzentrumshosting bietet.
Sie bietet DSG/DSGVO-Compliance, vorkonfigurierte KI-Agenten und flexible Skalierung. Als neuere Plattform fehlen ihr
jedoch möglicherweise Nachweise zur Produktionszuverlässigkeit und sie schafft eine gewisse Plattformabhängigkeit.
Obwohl sie sich hervorragend für Schweizer Unternehmen eignet, die kostengünstige KI mit Souveränität suchen, benötigt
sie möglicherweise Zeit zum Reifen.

**Wählen Sie Envoya AI, wenn** Sie kostengünstige Schweizer KI mit einfachen Pauschalpreisen wünschen und Ihre
Bedürfnisse zu ihren vorkonfigurierten Agenten passen.

**Wählen Sie Swiss AI Hub, wenn** Sie Schweizer Souveränität, transparente Kosten und vollständige Kontrolle über Ihre
KI-Plattform benötigen. Sie erhalten Infrastruktur mit vollständigen Anpassungsmöglichkeiten und
Herstellerunabhängigkeit durch Open-Source-Architektur.
:::

::: details Aleph Alpha
Aleph Alpha ist ein europäisches KI-Unternehmen, das die PhariaAI sovereign AI suite für Regierungen und Unternehmen
anbietet. Sie betonen "erklärbare KI" mit ihrer AtMan (Attention Manipulation) Transparenztechnologie und bieten
domänenspezifische Lösungen. Obwohl sie sich durch europäische Souveränität und Compliance auszeichnen, fehlen ihnen
transparente Preise und sie erfordern erhebliche technische Expertise. Ihr Versprechen der "Herstellerunabhängigkeit"
und die deutsche souveräne Infrastruktur machen sie attraktiv für regulierte Branchen, aber sie sind eher ein
KI-Modellanbieter als eine komplette Plattform.

**Wählen Sie Aleph Alpha, wenn** Sie eine Regierung oder ein stark reguliertes Unternehmen sind, das europäische
KI-Modelle mit Erklärungsfunktionen benötigt, und Sie über die technische Expertise verfügen, deren Modelle in Ihre
eigene Infrastruktur zu integrieren. Die Einhaltung deutscher/EU-Vorschriften ist Ihr Hauptanliegen.

**Wählen Sie Swiss AI Hub, wenn** Sie europäische Souveränität mit Schweizer Datenschutz wünschen, aber auch eine
komplette, sofort einsatzbereite Plattform und nicht nur KI-Modelle benötigen. Sie erhalten Souveränität plus
Unternehmensfunktionen wie Authentifizierung, Überwachung und Governance, ohne tiefe KI-Expertise zu erfordern.
:::

::: details owwn.ai
owwn.ai ist ein Schweizer KI-Lösungsanbieter, der anpassbare KI-Systeme mit starken Datenhoheitsgarantien anbietet. Sie
speichern Daten in Schweizer Rechenzentren, unterstützen mehrere LLM-Anbieter und integrieren sich in bestehende
Unternehmenssysteme. Obwohl sie Souveränität ohne zusätzliche Lizenzkosten bieten, sind sie primär ein
beratungsbasierter Dienst und keine Self-Service-Plattform. Sie zeichnen sich durch Schweizer Compliance aus, könnten
jedoch die Skalierbarkeit und Plattformvollständigkeit vermissen lassen, die für große Unternehmen erforderlich ist.

**Wählen Sie owwn.ai, wenn** Sie stark angepasste KI-Lösungen mit Schweizer Hosting benötigen und einen
beratungsgesteuerten Ansatz bevorzugen. Ihre Anforderungen sind sehr spezifisch und Sie legen Wert auf personalisierten
Service gegenüber Self-Service-Funktionen.

**Wählen Sie Swiss AI Hub, wenn** Sie Schweizer Souveränität mit einer Self-Service-, skalierbaren Plattform wünschen,
die Ihr Team unabhängig bereitstellen und verwalten kann. Sie erhalten die gleiche Schweizer Compliance mit größerer
Kontrolle, Transparenz und Plattformvollständigkeit für eine unternehmensweite Einführung.
:::

::: details PREM
PREM ist eine Plattform für angewandte KI-Forschung, die sich auf souveräne, private KI-Modelle mit ihrem
TrustML™-Verschlüsselungsframework konzentriert. Sie bieten autonomes Fine-Tuning und kosteneffiziente Inferenz, die
sowohl Cloud- als auch lokale Bereitstellung unterstützen. Obwohl sie sich durch datenschutzfreundliche KI und
Kostenreduzierung auszeichnen, erfordern sie erhebliche technische Expertise und sind eher forschungsorientiert als
produktionsreif. Ihre spezialisierten Reasoning-Modelle und Open-Source-Komponenten bieten Herstellerunabhängigkeit,
jedoch auf Kosten der Komplexität.

**Wählen Sie PREM, wenn** Sie KI-Forschung betreiben, modernste datenschutzfreundliche Techniken benötigen und über
tiefgreifende technische Expertise verfügen, um komplexe, experimentelle Systeme zu handhaben. Ihr Hauptaugenmerk liegt
auf fortschrittlicher KI-Forschung und nicht auf der Produktionsbereitstellung.

**Wählen Sie Swiss AI Hub, wenn** Sie Datenschutz und Souveränität mit einer produktionsreifen Plattform wünschen, die
keine spezialisierte KI-Forschungsexpertise erfordert. Sie erhalten Datenschutz und Herstellerunabhängigkeit mit
Unternehmensfunktionen, Benutzeroberflächen und operativer Einfachheit.
:::

::: details Private AI Suite
Private AI Suite ist eine umfassende Schweizer KI-Plattform mit modularen datenschutzorientierten Komponenten und
"Swiss-grade privacy"-Garantien. Sie bietet Schweizer Regulierungskonformität, modulare Architektur und bedient
Regierungs- und Unternehmenskunden.

**Wählen Sie Private AI Suite, wenn** Sie ein großes Unternehmen oder eine Regierungsorganisation mit beträchtlichem
Budget sind und umfassende Datenschutzgarantien benötigen. Sie schätzen ihren modularen Ansatz und können die
Preisgestaltung auf Unternehmensebene und die Herstellerbindung rechtfertigen.

**Wählen Sie Swiss AI Hub, wenn** Sie Schweizer Datenschutz und Souveränität mit kalkulierbaren Kosten und vollständiger
Herstellerunabhängigkeit wünschen. Sie erhalten umfassende KI-Funktionen mit transparenten Preisen,
Open-Source-Architektur und der Flexibilität, in jeder Größenordnung ohne Herstellerbindung bereitzustellen.
:::

## Managed Cloud-Plattformen

Dies sind umfassende, vollständig verwaltete Cloud-Dienste großer Technologieanbieter, die Infrastruktur, Skalierung und
Betrieb übernehmen. Sie bieten Komfort und unternehmensgerechte Zuverlässigkeit, erfordern jedoch in der Regel eine
Anbieterbindung und schränken die Optionen zur Datenhoheit ein.

| Framework           | Datenhoheit | Kalkulierbare Kosten | Vertrauen in Ergebnisse | Time-to-Value | Tool-Integration | Zugänglichkeit der Fähigkeiten | Skalierbarkeit | Herstellerunabhängigkeit | Einheitliche Governance | Produktionszuverlässigkeit | Visuelle Entwicklung | Keine Wartung |
| :------------------ | :---------: | :------------------: | :---------------------: | :-----------: | :--------------: | :----------------------------: | :------------: | :----------------------: | :---------------------: | :------------------------: | :------------------: | :-----------: |
| **Swiss AI Hub**    |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ✅            |           ✅            |             ✅             |          ❌          |      ❌       |
| Azure AI Foundry    |     ⚠️      |          ⚠️          |           ⚠️            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ❌            |           ✅            |             ✅             |          ✅          |      ✅       |
| Microsoft Copilot   |     ❌      |          ⚠️          |           ❌            |      ✅       |        ✅        |               ✅               |       ✅       |            ❌            |           ⚠️            |             ✅             |          ❌          |      ✅       |
| Google Vertex AI    |     ⚠️      |          ⚠️          |           ⚠️            |      ✅       |        ✅        |               ⚠️               |       ✅       |            ❌            |           ✅            |             ✅             |          ⚠️          |      ✅       |
| AWS Bedrock         |     ⚠️      |          ⚠️          |           ❌            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ❌            |           ✅            |             ✅             |          ❌          |      ✅       |
| IBM watsonx         |     ⚠️      |          ❌          |           ✅            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ❌            |           ✅            |             ✅             |          ⚠️          |      ❌       |
| Oracle AI           |     ⚠️      |          ⚠️          |           ✅            |      ✅       |        ✅        |               ⚠️               |       ✅       |            ❌            |           ⚠️            |             ✅             |          ❌          |      ✅       |
| SAP Business AI     |     ⚠️      |          ❌          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ❌            |           ✅            |             ✅             |          ✅          |      ❌       |
| Salesforce Einstein |     ❌      |          ❌          |           ✅            |      ✅       |        ✅        |               ✅               |       ✅       |            ❌            |           ✅            |             ✅             |          ✅          |      ✅       |

### Details zu Cloud-Plattformen

::: details Azure AI Foundry
Azure AI Foundry ist Microsofts umfassende Unternehmens-KI-Plattform, die eine verwaltete Infrastruktur mit
hervorragender Integration in das Microsoft-Ökosystem bietet. Obwohl sie visuelle Entwicklungstools bereitstellt und
alle betrieblichen Komplexitäten handhabt, sind Sie an Microsofts Ökosystem mit deren Preismodell und begrenzter
Einsicht in KI-Entscheidungen gebunden. Daten können in Schweizer Azure-Regionen gespeichert werden, bleiben aber unter
Microsofts Kontrolle und Governance.

**Wählen Sie Azure AI Foundry, wenn** Sie stark in das Microsoft-Ökosystem investiert sind, keine
Infrastrukturverwaltung benötigen und mit der Herstellerbindung und dem Preismodell von Microsoft einverstanden sind.
Ihr Team bevorzugt visuelle Entwicklungstools gegenüber codebasierten Ansätzen.

**Wählen Sie Swiss AI Hub, wenn** Sie Unternehmens-KI-Funktionen ohne Herstellerbindung wünschen, mit vollständiger
Kontrolle über Ihre Daten und Infrastruktur. Sie erhalten ähnliche Unternehmensfunktionen mit voller Souveränität,
transparenten Kosten und der Möglichkeit, überall, einschließlich On-Premise, bereitzustellen.
:::

::: details Microsoft Copilot
Microsoft Copilot bettet KI direkt in Office-Anwendungen ein und bietet sofortige Produktivitätssteigerungen ohne
jegliche Entwicklung. Es ist jedoch ein geschlossenes Produkt, keine Plattform. Sie können keine benutzerdefinierten
Agenten erstellen, nicht steuern, wo Daten verarbeitet werden, oder sehen, wie Entscheidungen getroffen werden. Perfekt
für Büroproduktivität, ungeeignet für den Aufbau eigener KI-Anwendungen.

**Wählen Sie Microsoft Copilot, wenn** Sie sofortige Produktivitätssteigerungen in Office-Anwendungen ohne
Entwicklungsaufwand wünschen und damit einverstanden sind, dass Microsoft Ihre Daten über deren Systeme verarbeitet.

**Wählen Sie Swiss AI Hub, wenn** Sie benutzerdefinierte KI-Anwendungen erstellen möchten, die sich in Ihre
Geschäftsprozesse und Daten integrieren lassen, mit vollständiger Kontrolle darüber, wo die Verarbeitung stattfindet.
Sie erhalten Produktivitätssteigerungen sowie die Möglichkeit, spezialisierte KI-Lösungen für Ihr Unternehmen zu
erstellen.
:::

::: details Google Vertex AI
Google Vertex AI ist eine umfassende, verwaltete KI-Plattform, die die Infrastrukturkomplexität für Sie handhabt. Obwohl
sie unternehmensgerechte Zuverlässigkeit und nahtlose Skalierung innerhalb der Google Cloud bietet, tauschen Sie
Kontrolle gegen Bequemlichkeit. Daten verbleiben in der Google-Infrastruktur (obwohl regionenwählbar), Kosten können mit
komplexen Preisstufen unvorhersehbar sein, und Sie sind an deren Ökosystem gebunden.

**Wählen Sie Google Vertex AI, wenn** Sie sich voll und ganz der Google Cloud verschrieben haben, komplexe KI-Workloads
haben, die von Googles ML-Expertise profitieren, und operative Einfachheit wichtiger ist als Datenhoheit oder
Kostenprognostizierbarkeit.

**Wählen Sie Swiss AI Hub, wenn** Sie umfassende KI-Funktionen mit kalkulierbaren Kosten, vollständiger Datenhoheit und
der Flexibilität wünschen, auf jeder Infrastruktur bereitzustellen. Sie erhalten unternehmensgerechte Funktionen ohne
Herstellerbindung oder unvorhersehbare Preisgestaltung.
:::

::: details AWS Bedrock
AWS Bedrock ist eine verwaltete Plattform zum Bereitstellen von Modellen, die über APIs Zugang zu Basismodellen bietet.
Obwohl es die Modellinfrastruktur hervorragend handhabt und sich nahtlos in AWS-Dienste integriert, ist es keine
vollständige KI-Anwendungsplattform. Sie müssen weiterhin die gesamte Anwendungslogik, Benutzeroberflächen und
Datenpipelines selbst erstellen. Daten verbleiben in der AWS-Infrastruktur (obwohl Sie Regionen wählen können), und Sie
sind an das AWS-Ökosystem und Preismodell gebunden.

**Wählen Sie AWS Bedrock, wenn** Sie sich voll und ganz AWS verschrieben haben, Zugriff auf mehrere Basismodelle
benötigen und über die Ressourcen verfügen, um komplette Anwendungen um Modell-APIs herum zu erstellen. Sie priorisieren
die AWS-Integration gegenüber der Plattformvollständigkeit.

**Wählen Sie Swiss AI Hub, wenn** Sie eine komplette KI-Plattform mit Zugang zu Basismodellen, Anwendungslogik,
Benutzeroberflächen und Datenpipelines wünschen. Sie erhalten umfassende Funktionen mit Datenhoheit und der
Flexibilität, überall bereitzustellen.
:::

::: details IBM watsonx
IBM watsonx ist eine umfassende KI- und Datenplattform mit einem Hybrid-Cloud-Ansatz und starkem Fokus auf KI-Ethik. Sie
unterstützt die Bereitstellung über mehrere Clouds hinweg und betont die verantwortungsvolle KI-Entwicklung. Obwohl sie
unternehmensgerechte Zuverlässigkeit und branchenspezifische Lösungen bietet, weist sie die typische IBM-Komplexität auf
und es fehlen transparente Preise. Die Plattform bietet gute Integrationsfähigkeiten, schafft aber durch ihr umfassendes
Ökosystem eine potenzielle Anbieterbindung.

**Wählen Sie IBM watsonx, wenn** Sie ein Unternehmenskunde sind, der mit IBMs Komplexität und Preismodell vertraut ist,
branchenspezifische KI-Lösungen benötigt und IBMs jahrzehntelange Unternehmenserfahrung der Einfachheit vorzieht.

**Wählen Sie Swiss AI Hub, wenn** Sie umfassende KI-Funktionen ohne Anbieterkomplexität wünschen, mit transparenten
Preisen und vollständiger Kontrolle über Ihre Plattform. Sie erhalten Unternehmensfunktionen mit Einfachheit,
Souveränität und klarer Kostenstruktur.
:::

::: details Oracle AI
Oracle AI bietet umfassende KI-Dienste über Oracle Cloud Infrastructure, einschließlich generativer KI, Sprach-, Sprech-
und Bildverarbeitungsfunktionen. Es bietet unternehmensgerechte Sicherheit und anpassbare Modelle, ist aber nur in der
Cloud verfügbar mit starkem Potenzial für Anbieterbindung. Obwohl es eine zuverlässige Infrastruktur und über 20 Jahre
Erfahrung in der Datenwissenschaft bietet, fehlen Optionen zur Datenhoheit und es erfordert eine Bindung an Oracles
Ökosystem.

**Wählen Sie Oracle AI, wenn** Sie ein bestehender Oracle-Kunde mit erheblichen Investitionen in die
Oracle-Infrastruktur sind und KI-Funktionen wünschen, die tief in Ihre Oracle-Systeme integriert sind. Sie legen Wert
auf Oracles Unternehmenszuverlässigkeit über Souveränität.

**Wählen Sie Swiss AI Hub, wenn** Sie Unternehmens-KI-Funktionen wünschen, ohne an Oracles Ökosystem gebunden zu sein,
mit vollständiger Datenhoheit und Bereitstellungsflexibilität. Sie erhalten umfassende KI-Funktionen mit der Freiheit,
sich in jedes System zu integrieren.
:::

::: details SAP Business AI
SAP Business AI bietet den Joule KI-Assistenten mit über 240 KI-Szenarien und Integration über 13 SAP-Lösungen hinweg.
Es bietet umfassende Unternehmens-KI-Funktionen mit starker Governance und Mehrsprachigkeitsunterstützung. Es ist jedoch
tief in das SAP-Ökosystem integriert, was eine Anbieterbindung schafft, und es fehlen transparente Preise. Obwohl es
hervorragend für SAP-Kunden ist, erfordert es erhebliche Investitionen in die SAP-Infrastruktur und ist möglicherweise
nicht kosteneffektiv für Nicht-SAP-Umgebungen.

**Wählen Sie SAP Business AI, wenn** Sie stark in das SAP-Ökosystem investiert sind, KI tief in SAP-Geschäftsprozesse
integrieren müssen und mit SAPs Preisgestaltung und Infrastrukturanforderungen einverstanden sind.

**Wählen Sie Swiss AI Hub, wenn** Sie KI in Ihre Geschäftsprozesse (einschließlich SAP-Systeme) integrieren möchten,
ohne an das Ökosystem eines einzelnen Anbieters gebunden zu sein. Sie erhalten Business AI-Funktionen mit Flexibilität,
Souveränität und transparenten Kosten.
:::

::: details Salesforce Einstein
Salesforce Einstein bietet nativ in die Salesforce CRM-Plattform eingebettete KI mit dem Einstein Trust Layer für den
Datenschutz. Es bietet umfassende KI-Agenten, Workflow-Automatisierung und branchenspezifische Lösungen. Obwohl es sich
bei CRM-integrierter KI auszeichnet und ethische KI-Funktionen bietet, ist es auf das Salesforce-Ökosystem beschränkt
und es fehlen Optionen zur Datenhoheit. Perfekt für Salesforce-Kunden, aber ungeeignet für Organisationen, die
plattformunabhängige KI-Lösungen suchen.

**Wählen Sie Salesforce Einstein, wenn** Sie ein Salesforce-Kunde sind, der KI tief in CRM-Workflows integrieren möchte,
ohne zusätzliche Plattformkomplexität. Ihre KI-Anforderungen sind primär CRM-zentriert.

**Wählen Sie Swiss AI Hub, wenn** Sie KI-Funktionen wünschen, die über CRM hinaus alle Geschäftsprozesse abdecken, mit
Datenhoheit und Plattformunabhängigkeit. Sie können sich in Salesforce integrieren, während Sie KI-Lösungen für Ihr
gesamtes Unternehmen entwickeln.
:::

## Visuelle Entwicklungsplattformen

Dies sind Plattformen, die Drag-and-Drop-, No-Code-/Low-Code-Ansätze zum Erstellen von KI-Anwendungen betonen. Sie
priorisieren die Zugänglichkeit für nicht-technische Benutzer, können aber Flexibilität und Unternehmensfunktionen
zugunsten der Benutzerfreundlichkeit opfern.

| Framework        | Datenhoheit | Kalkulierbare Kosten | Vertrauen in Ergebnisse | Time-to-Value | Tool-Integration | Zugänglichkeit der Fähigkeiten | Skalierbarkeit | Herstellerunabhängigkeit | Einheitliche Governance | Produktionszuverlässigkeit | Visuelle Entwicklung | Keine Wartung |
| :--------------- | :---------: | :------------------: | :---------------------: | :-----------: | :--------------: | :----------------------------: | :------------: | :----------------------: | :---------------------: | :------------------------: | :------------------: | :-----------: |
| **Swiss AI Hub** |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ✅            |           ✅            |             ✅             |          ❌          |      ❌       |
| Dify             |     ✅      |          ✅          |           ⚠️            |      ✅       |        ⚠️        |               ✅               |       ⚠️       |            ✅            |           ⚠️            |             ⚠️             |          ✅          |      ✅       |
| Flowise          |     ✅      |          ⚠️          |           ❌            |      ✅       |        ⚠️        |               ✅               |       ❌       |            ✅            |           ❌            |             ❌             |          ✅          |      ❌       |
| LangFlow         |     ⚠️      |          ⚠️          |           ⚠️            |      ✅       |        ⚠️        |               ✅               |       ❌       |            ✅            |           ❌            |             ❌             |          ✅          |      ❌       |

### Details zu visuellen Plattformen

::: details Dify
Dify ist eine Open-Source-Plattform für die Entwicklung von KI-Anwendungen mittels visueller Drag-and-Drop-Workflows.
Sie ermöglicht nicht-technischen Teammitgliedern, KI-Anwendungen zu erstellen, indem sie Knoten (wie das Aufrufen von
KI-Modellen, das Suchen in Datenbanken oder das Ausführen von Logik) auf einer visuellen Leinwand verbinden. Sie
zeichnet sich durch schnelles Prototyping aus und macht die KI-Entwicklung für Produktmanager und Fachexperten
zugänglich.

**Wählen Sie Dify, wenn** Sie schnelles Prototyping mit visuellen Workflows wünschen, nicht-technische Teammitglieder
KI-Anwendungen erstellen sollen und Ihre Anwendungsfälle gut in Drag-and-Drop-Paradigmen passen. Sie priorisieren
Entwicklungsgeschwindigkeit und Zugänglichkeit gegenüber tiefgreifender Anpassung.

**Wählen Sie Swiss AI Hub, wenn** Sie unternehmensgerechte Governance und Observability mit codebasierter Entwicklung
für komplexe KI-Systeme benötigen. Sie erhalten eine komplette Plattform zum Erstellen auditierbarer, anpassbarer
KI-Anwendungen mit transparenter Überwachung, aber die Entwicklung erfordert Programmierung und keine visuellen Tools.
:::

::: details Flowise
Flowise zeichnet sich dadurch aus, dass es KI durch visuelle Drag-and-Drop-Flow-Erstellung zugänglich macht. Es ist
selbst-hostbar und Open Source, was Souveränität und Unabhängigkeit bietet. Es ist jedoch primär ein Entwicklungstool
und keine Produktionsplattform. Es fehlen Unternehmensfunktionen wie eine ordnungsgemäße Authentifizierung,
Skalierungsmechanismen, Governance-Kontrollen und produktionsreife Zuverlässigkeit. Am besten geeignet für schnelles
Prototyping und Entwicklung, nicht für Unternehmensbereitstellungen.

**Wählen Sie Flowise, wenn** Sie KI-Workflows prototypisieren, eine einfache visuelle Benutzeroberfläche wünschen und
keine unternehmensgerechten Funktionen benötigen. Ihr Anwendungsfall ist experimentell oder lehrreich und nicht
produktionsorientiert.

**Wählen Sie Swiss AI Hub, wenn** Sie eine produktionsreife Plattform mit Authentifizierung, Governance, Skalierung und
Zuverlässigkeit wünschen und mit codebasierter Entwicklung vertraut sind. Sie erhalten Unternehmensreife mit
vollständiger Plattformkontrolle, benötigen jedoch Programmierkenntnisse anstelle von visuellen Tools.
:::

::: details LangFlow
LangFlow ist eine visuelle Oberfläche für LangChain, die die Prototypenentwicklung durch
Drag-and-Drop-Workflow-Erstellung beschleunigt. Obwohl es sich hervorragend eignet, KI für Nicht-Entwickler zugänglich
zu machen, ist es ein Entwicklungstool und keine Produktionsplattform. Es fehlen integrierte Authentifizierung,
Überwachung, Kostenverfolgung und Bereitstellungsinfrastruktur – Sie müssen immer noch herausfinden, wie Sie Ihre Flows
in der Produktion ausführen, skalieren und sichern können.

**Wählen Sie LangFlow, wenn** Sie LangChain-basierte Workflows schnell mit einer visuellen Benutzeroberfläche
prototypisieren möchten und über die Ressourcen verfügen, um Produktionsinfrastruktur um Ihre Prototypen herum
aufzubauen. Ihr Fokus liegt auf schneller Experimentierfreude.

**Wählen Sie Swiss AI Hub, wenn** Sie LangChain-kompatible Workflows innerhalb einer kompletten Produktionsplattform
erstellen möchten, die Authentifizierung, Überwachung, Bereitstellung und Skalierung automatisch handhabt. Sie erhalten
Produktionsreife mit codebasierter Entwicklung anstelle von visuellen Prototyping-Tools.
:::

## Automatisierungsplattformen mit KI

Dies sind Workflow-Automatisierungsplattformen, die KI-Fähigkeiten als zusätzliche Funktionen integriert haben. Sie
zeichnen sich durch die Verbindung von Systemen und die Automatisierung von Geschäftsprozessen aus, wobei KI als
unterstützende Funktion und nicht als ihr primärer Fokus dient.

| Framework        | Datenhoheit | Kalkulierbare Kosten | Vertrauen in Ergebnisse | Time-to-Value | Tool-Integration | Zugänglichkeit der Fähigkeiten | Skalierbarkeit | Herstellerunabhängigkeit | Einheitliche Governance | Produktionszuverlässigkeit | Visuelle Entwicklung | Keine Wartung |
| :--------------- | :---------: | :------------------: | :---------------------: | :-----------: | :--------------: | :----------------------------: | :------------: | :----------------------: | :---------------------: | :------------------------: | :------------------: | :-----------: |
| **Swiss AI Hub** |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ✅            |           ✅            |             ✅             |          ❌          |      ❌       |
| n8n              |     ✅      |          ✅          |           ❌            |      ✅       |        ✅        |               ✅               |       ⚠️       |            ✅            |           ❌            |             ⚠️             |          ✅          |      ⚠️       |
| Zapier AI        |     ❌      |          ⚠️          |           ❌            |      ✅       |        ✅        |               ✅               |       ⚠️       |            ❌            |           ⚠️            |             ✅             |          ✅          |      ✅       |
| Make             |     ⚠️      |          ⚠️          |           ❌            |      ✅       |        ✅        |               ✅               |       ⚠️       |            ❌            |           ⚠️            |             ✅             |          ✅          |      ✅       |

### Details zu Automatisierungsplattformen

::: details n8n
n8n ist eine hervorragende Workflow-Automatisierungsplattform, die KI-Fähigkeiten über Nodes hinzufügt. Obwohl es sich
bei der visuellen Workflow-Erstellung auszeichnet und Hunderte von Integrationen bietet, fehlt ihm die tiefe
KI-Infrastruktur einer dedizierten Plattform. Es gibt keine integrierte Observability für KI-Entscheidungen, kein
einheitliches LLM-Gateway und begrenzte Governance-Funktionen für Unternehmen. Es ist automatisierungszentriert mit
hinzugefügter KI, nicht KI-nativ.

**Wählen Sie n8n, wenn** Sie umfassende Workflow-Automatisierung mit einigen KI-Fähigkeiten benötigen, viele
Systemintegrationen verwalten müssen und KI eher eine unterstützende Funktion als Ihre Kernanforderung ist. Sie legen
Wert auf breite Konnektivität gegenüber KI-Tiefe.

**Wählen Sie Swiss AI Hub, wenn** KI im Mittelpunkt Ihrer Workflows steht und Sie tiefe KI-Observability, einheitliche
Modellverwaltung und Unternehmens-Governance benötigen. Sie erhalten Workflow-Automatisierung plus umfassende
KI-Infrastruktur, die für KI-zentrierte Anwendungen entwickelt wurde.
:::

::: details Zapier AI
Zapier AI erweitert eine Workflow-Automatisierungsplattform um KI-Funktionen, anstatt eine KI-Infrastruktur
bereitzustellen. Obwohl es sich hervorragend zum Verbinden von Tools und zur Ermöglichung nicht-technischer Benutzer zum
Erstellen von Automatisierungen eignet, arbeitet es als Black-Box-Cloud-Dienst ohne Einblick in KI-Entscheidungsfindung,
Datenhoheitsoptionen oder Bereitstellungsflexibilität.

**Wählen Sie Zapier AI, wenn** Sie einfache KI-erweiterte Automatisierungen zwischen SaaS-Tools benötigen, keine Wartung
wünschen und mit Cloud-only-Bereitstellung und Black-Box-KI-Operationen einverstanden sind. Ihre Anforderungen sind
unkompliziert und die Compliance-Anforderungen minimal.

**Wählen Sie Swiss AI Hub, wenn** Sie transparente KI-Operationen mit vollständiger Einblick in die
Entscheidungsfindung, Datenhoheit und Bereitstellungskontrolle benötigen. Sie erhalten leistungsstarke
Automatisierungsfunktionen mit vollständiger Transparenz, Governance und der Möglichkeit, überall bereitzustellen.
:::

::: details Make (formerly Integromat)
Make ist eine visuelle Automatisierungsplattform, die KI-Funktionen als Module in Workflows integriert hat. Obwohl es
sich hervorragend für die No-Code-Automatisierung mit Tausenden von Integrationen eignet, behandelt es KI als
Black-Box-Komponenten ohne Einblick in Argumentation oder Entscheidungen. Als proprietäre SaaS-Plattform bietet es
Komfort, aber es fehlen Datenhoheit, Herstellerunabhängigkeit und die tiefe KI-Observability, die Unternehmen für
Vertrauen benötigen.

**Wählen Sie Make, wenn** Sie umfangreiche No-Code-Integrationen mit einigen KI-Funktionen benötigen, Komfort über
Kontrolle priorisieren und mit proprietären SaaS-Einschränkungen einverstanden sind. Ihre KI-Anforderungen sind einfach
und Transparenz ist nicht entscheidend.

**Wählen Sie Swiss AI Hub, wenn** Sie umfassende KI-Funktionen mit vollständiger Observability, Datenhoheit und
Herstellerunabhängigkeit benötigen. Sie erhalten leistungsstarke Automatisierung plus transparente KI-Operationen, denen
Unternehmen vertrauen und die sie prüfen können.
:::

## Geschäftsprozessplattformen

Dies sind unternehmensgerechte Plattformen, die für die Verwaltung, Automatisierung und Optimierung komplexer
Geschäftsprozesse entwickelt wurden. Sie konzentrieren sich auf Workflow-Orchestrierung, Fallmanagement und Process
Mining, wobei KI-Funktionen integriert sind, um das traditionelle Geschäftsprozessmanagement zu verbessern.

| Framework           | Datenhoheit | Kalkulierbare Kosten | Vertrauen in Ergebnisse | Time-to-Value | Tool-Integration | Zugänglichkeit der Fähigkeiten | Skalierbarkeit | Herstellerunabhängigkeit | Einheitliche Governance | Produktionszuverlässigkeit | Visuelle Entwicklung | Keine Wartung |
| :------------------ | :---------: | :------------------: | :---------------------: | :-----------: | :--------------: | :----------------------------: | :------------: | :----------------------: | :---------------------: | :------------------------: | :------------------: | :-----------: |
| **Swiss AI Hub**    |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ✅               |       ✅       |            ✅            |           ✅            |             ✅             |          ❌          |      ❌       |
| Camunda             |     ✅      |          ⚠️          |           ✅            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ✅            |           ✅            |             ✅             |          ✅          |      ❌       |
| Automation Anywhere |     ✅      |          ❌          |           ✅            |      ❌       |        ✅        |               ❌               |       ✅       |            ❌            |           ✅            |             ✅             |          ✅          |      ❌       |
| Pega                |     ✅      |          ⚠️          |           ✅            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ❌            |           ✅            |             ✅             |          ✅          |      ❌       |
| Appian              |     ✅      |          ⚠️          |           ✅            |      ✅       |        ✅        |               ✅               |       ✅       |            ❌            |           ✅            |             ✅             |          ✅          |      ❌       |
| Blue Prism          |     ✅      |          ⚠️          |           ✅            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ⚠️            |           ✅            |             ✅             |          ✅          |      ❌       |
| Celonis             |     ⚠️      |          ⚠️          |           ✅            |      ⚠️       |        ✅        |               ❌               |       ✅       |            ❌            |           ⚠️            |             ✅             |          ⚠️          |      ❌       |
| Flowable            |     ✅      |          ✅          |           ✅            |      ⚠️       |        ✅        |               ⚠️               |       ✅       |            ✅            |           ✅            |             ✅             |          ✅          |      ❌       |

### Details zu Geschäftsprozessplattformen

::: details Camunda
Camunda ist eine Prozess-Orchestrierungsplattform, die KI-Agentenfunktionen integriert hat, während sie ihren
BPMN-basierten Ansatz beibehält. Sie bietet hervorragende Prozesstransparenz, Open-Standards-Compliance und
unternehmensbewährte Skalierbarkeit.

**Wählen Sie Camunda, wenn** Sie komplexe Geschäftsprozesse haben, die eine BPMN-Modellierung erfordern,
unternehmensgerechte Prozess-Orchestrierung benötigen und über Teams mit BPMN-Expertise verfügen. Ihr Hauptaugenmerk
liegt auf Prozessmanagement mit KI als unterstützende Komponente.

**Wählen Sie Swiss AI Hub, wenn** Sie KI-gesteuerte Prozessautomatisierung durch codebasierte Entwicklung mit
integrierten KI-Funktionen wünschen. Sie erhalten leistungsstarke Prozess-Orchestrierung, die speziell für KI-Workflows
entwickelt wurde, obwohl Sie Programmierkenntnisse anstelle von visuellen Modellierungstools benötigen.
:::

::: details Automation Anywhere
Automation Anywhere ist ein führender RPA-Plattformanbieter für Unternehmen mit agentischer Prozessautomatisierung. Es
bietet umfassende Governance, Kompatibilität mit Unternehmensanwendungen und Transparenz der Process Reasoning Engine.
Es erfordert jedoch RPA-Expertise, schafft Plattformbindung und benötigt erheblichen IT-Management-Aufwand. Obwohl es
sich im Unternehmensmaßstab bewährt hat, kann es für Organisationen, die einfachere KI-Lösungen suchen, übermäßig
komplex sein.

**Wählen Sie Automation Anywhere, wenn** Sie ein großes Unternehmen mit erheblichen RPA-Investitionen sind,
traditionelle Automatisierung massiv skalieren müssen und über Teams mit tiefer RPA-Expertise verfügen. Ihre
Automatisierungsstrategie ist RPA-first mit KI-Integration.

**Wählen Sie Swiss AI Hub, wenn** Sie KI-gesteuerte Automatisierung ohne RPA-Komplexität wünschen, mit transparenter
Architektur und Herstellerunabhängigkeit. Sie erhalten unternehmensgerechte Skalierbarkeit, die für moderne KI-Workflows
entwickelt wurde, ohne den Overhead traditioneller RPA-Plattformen.
:::

::: details Pega
Pega ist eine Low-Code-Plattform, die sich auf "Predictable AI" mit umfassenden agentischen Workflows und Fallmanagement
spezialisiert hat. Sie bietet unternehmensgerechte Governance, Skalierbarkeit und starke Prozesstransparenz. Sie schafft
jedoch eine erhebliche Plattformbindung, hat komplexe Unternehmenspreise und erfordert plattformspezifische Expertise.
Obwohl sie sich hervorragend für große Unternehmen mit komplexen Fallmanagementanforderungen eignet, kann sie für
Organisationen, die einfachere KI-Automatisierungslösungen suchen, überdimensioniert sein.

**Wählen Sie Pega, wenn** Sie ein großes Unternehmen mit komplexen Fallmanagementanforderungen, einem erheblichen Budget
für Plattformlizenzen und Teams sind, die Pega-spezifische Expertise entwickeln können. Ihre Prozesse sind hochkomplex
und rechtfertigen die Plattforminvestition.

**Wählen Sie Swiss AI Hub, wenn** Sie leistungsstarke KI- und Prozessfunktionen ohne Herstellerbindung wünschen, mit
transparenten Preisen und Plattformunabhängigkeit. Sie erhalten unternehmensgerechte Funktionen mit der Flexibilität,
sich ohne proprietäre Einschränkungen anzupassen und zu erweitern.
:::

::: details Appian
Appian ist eine Low-Code-Automatisierungsplattform mit privater KI-Integration und umfassenden Data Fabric-Funktionen.
Sie bietet Unternehmens-Governance, schnelle Entwicklungsfunktionen und starke Sicherheitsmerkmale. Obwohl sie gute
Skalierbarkeit und Prozesstransparenz bietet, schafft sie Plattformabhängigkeit und erfordert fortlaufendes
Plattformmanagement. Die Plattform zeichnet sich durch Unternehmensprozessautomatisierung aus, es fehlen jedoch
Herstellerunabhängigkeit und sie kann für kleinere Organisationen kostspielig sein.

**Wählen Sie Appian, wenn** Sie schnelle Low-Code-Entwicklung für Unternehmensprozesse benötigen, Budget für
Plattformlizenzen haben und mit Plattformabhängigkeit einverstanden sind. Ihr Fokus liegt auf schneller
Anwendungsentwicklung und nicht auf KI-Innovation.

**Wählen Sie Swiss AI Hub, wenn** Sie Unternehmensprozessautomatisierung mit KI-first-Design, vollständiger
Herstellerunabhängigkeit und transparenten Kosten wünschen. Sie erhalten schnelle Entwicklungsfunktionen plus die
Flexibilität, ohne Plattformbeschränkungen zu innovieren und zu erweitern.
:::

::: details Blue Prism
Blue Prism ist eine ausgereifte Unternehmens-RPA-Plattform, die sich zu einer Integration von KI und intelligenter
Automatisierung entwickelt hat. Sie bietet starke Governance, unternehmensbewährte Skalierbarkeit und umfassende
Prozessautomatisierungsfunktionen. Obwohl sie sich bei der strukturierten Prozessautomatisierung auszeichnet, erfordert
sie spezialisierte RPA-Expertise und erheblichen IT-Managementaufwand. Die Plattform schafft Herstellerbindung durch
plattformspezifische Automatisierung und kann für Organisationen, die einfachere KI-Lösungen suchen, komplex sein.

**Wählen Sie Blue Prism, wenn** Sie erhebliche RPA-Investitionen haben, hoch strukturierte Prozesse automatisieren
müssen und über Teams mit spezialisierter RPA-Expertise verfügen. Ihre Automatisierungsbedürfnisse sind primär
traditionelles RPA mit einer gewissen KI-Erweiterung.

**Wählen Sie Swiss AI Hub, wenn** Sie intelligente Automatisierung ohne RPA-Komplexität wünschen, mit KI-nativem Design
durch codebasierte Entwicklung. Sie erhalten leistungsstarke Automatisierungsfunktionen, die für KI-Workflows entwickelt
wurden, ohne spezialisiertes RPA-Wissen zu erfordern, obwohl Sie Programmierkenntnisse benötigen.
:::

::: details Celonis
Celonis ist eine Prozess-Intelligenz-Plattform, die sich auf KI-gestütztes Process Mining und Optimierung spezialisiert
hat. Sie liefert datengestützte Erkenntnisse mit unternehmensbewährter Skalierbarkeit. Sie erfordert jedoch
spezialisierte Process Mining-Expertise, schafft Plattformabhängigkeit und konzentriert sich primär auf die
Prozessanalyse statt auf die Automatisierung. Obwohl sie sich hervorragend für die Prozessoptimierung eignet, ist sie
keine allgemeine KI-Plattform und kann erhebliche zusätzliche Tools für komplette KI-Lösungen erfordern.

**Wählen Sie Celonis, wenn** Ihr primäres Bedürfnis Process Mining und Optimierung ist, Sie über spezialisierte
Prozessintelligenz-Expertise verfügen und sich auf das Verständnis bestehender Prozesse konzentrieren, anstatt neue
KI-Anwendungen zu erstellen.

**Wählen Sie Swiss AI Hub, wenn** Sie umfassende KI-Funktionen wünschen, die Prozessoptimierung sowie die Möglichkeit
zum Erstellen und Bereitstellen von KI-Anwendungen umfassen. Sie erhalten Prozessintelligenz als Teil einer kompletten
KI-Plattform und nicht als spezialisiertes Standalone-Tool.
:::

::: details Flowable
Flowable ist eine Open-Source-Geschäftsprozessmanagement-Plattform mit KI-Agentenintegration und starker
Prozess-Governance. Sie bietet Open-Standards-Compliance, unternehmensbewährte Akzeptanz und Herstellerunabhängigkeit.
Sie erfordert jedoch BPM-Expertise und fortlaufendes Prozessmanagement ohne integrierte KI-Entwicklungstools. Obwohl sie
sich hervorragend für prozesszentrierte KI-Integration eignet, kann sie erhebliche zusätzliche Tools für komplette
KI-Lösungen erfordern.

**Wählen Sie Flowable, wenn** Sie BPM-Expertise haben, Open-Source-Prozessmanagement benötigen und benutzerdefinierte
KI-Integrationen um etablierte BPM-Muster herum aufbauen möchten. Ihr Hauptaugenmerk liegt auf dem traditionellen
Geschäftsprozessmanagement.

**Wählen Sie Swiss AI Hub, wenn** Sie Prozessmanagement wünschen, das von Grund auf für KI-Workflows konzipiert ist, mit
integrierten KI-Entwicklungstools und Unternehmensschnittstellen. Sie erhalten die Vorteile von Open-Source mit
umfassenden KI-Funktionen, wobei die Entwicklung jedoch Programmierkenntnisse erfordert.
:::
