---
title: Container
description: C4 Level 2 – Erstanbieter-Anwendungscontainer plus die zentrale Infrastruktur, über die sie verbunden sind, nach Schichten organisiert.
source_sha: 25bc3b6212add3b6d51075f90b8da20ed87c39bc9e9d006a02b1c86dd5902082
---

# Container

Die Container-Ansicht zoomt in die Swiss AI Hub-Box aus dem [Systemkontext](../1_system_context/) hinein und zeigt, was
sich darin befindet. In der C4-Terminologie ist ein *Container* eine separat deploybare, unabhängig lauffähige Einheit –
ein Anwendungsprozess, eine Datenbank, ein Message Broker – nicht unbedingt ein Docker-Container (obwohl sie hier
meistens eins zu eins abgebildet werden).

Swiss AI Hub betreibt etwa 33 Container in Produktion. Alle auf einem Diagramm darzustellen wäre unlesbar, daher ist
diese Seite in zwei Ebenen organisiert: eine **Übersicht** der Teile, über die ein Entwickler täglich nachdenkt, gefolgt
von **fokussierten Schichtenansichten**, die jeweils in eine funktionale Schicht der Plattform hineinzoomen. Wählen Sie
die Ansicht, die Ihrer Frage entspricht.

::: tip
Klicken Sie auf ein beliebiges Diagramm, um den interaktiven Viewer zu öffnen – Sie können schwenken, zoomen,
Beziehungen verfolgen und zwischen Ansichten wechseln.
:::

## Übersicht

Diese Übersichtsansicht zeigt die neun Erstanbieter-Anwendungscontainer – die Pakete, die wir erstellen – plus den
NATS-Ereignisbus, der sie verbindet. Sie lässt die unterstützende Infrastruktur (Datenbanken, Gateways, Observability)
bewusst weg, damit die Anwendungstopologie hervorsticht: wer mit wem spricht und wie die Ereignis-Spine die
Backend-Services miteinander verbindet.

Wenn Sie neu auf der Plattform sind, beginnen Sie hier. Es ist das mentale Modell, an dem sich alles andere aufhängen
lässt.

<likec4-view view-id="containers_overview" style="display:block;height:600px"></likec4-view>

## Anwendungsschicht

Die Erstanbieter-Pakete plus OpenWebUI – alles mit kundenspezifischer Anwendungslogik. Dies ist die Schicht, in der die
meisten Mitwirkenden arbeiten. Die Ansicht konzentriert sich ausschliesslich darauf, wie Anwendungscontainer sich
gegenseitig erreichen; die Infrastruktur, von der sie alle abhängen (Datenbanken, LLM-Gateway, Identität), befindet sich
in den darunterliegenden Schichten, um dieses Diagramm lesbar zu halten.

Beachten Sie, dass die Agent Runtime hier als einzelne logische Box erscheint, aber in Produktion als ein Container *pro
Agentenklasse* deployed wird. Die Process Engine ist überhaupt kein Container – sie läuft eingebettet im API Gateway.

<likec4-view view-id="tier_application" style="display:block;height:560px"></likec4-view>

## LLM / KI-Inferenzschicht

Jeder Modellaufruf auf der Plattform – Chat, Embeddings, Reranking, Sprachverarbeitung, OCR – läuft durch das
**LiteLLM-Gateway**. Dieser einzelne Engpass macht die Plattform modellunabhängig: Der Wechsel von Swiss LLM Cloud zu
OpenAI zu einem lokalen GPU-Modell ist eine Konfigurationsänderung in LiteLLM, keine Codeänderung an anderer Stelle.
Presidio sitzt im Pfad, um PII zu redigieren, bevor Anfragen externe Anbieter erreichen, und MinerU, vLLM und Speaches
bieten lokales Parsing, GPU-Inferenz bzw. Sprachverarbeitung.

<likec4-view view-id="tier_llm" style="display:block;height:480px"></likec4-view>

## Datenschicht

Die zustandsbehafteten Speicher der Plattform, jeder für eine bestimmte Aufgabe ausgewählt: PostgreSQL für relationale
Daten, FerretDB für Dokumente, Valkey für den ephemeren Agentenstatus, Neo4j für grafbasierte Speicherung, Milvus für
Vektoren, ClickHouse für Analysen und SeaweedFS für S3-kompatiblen Objektspeicher. Die Ansicht zeigt auch ihre internen
Abhängigkeiten – Milvus und SeaweedFS verwenden beide etcd für Metadaten, FerretDB läuft auf einem eigenen
unterstützenden Postgres, und ClickHouse lagert auf S3 aus – weshalb "die Datenbankschicht" stärker miteinander
verbunden ist, als es zunächst scheint.

<likec4-view view-id="tier_data" style="display:block;height:520px"></likec4-view>

## Ereignisschicht

NATS / JetStream ist das Rückgrat der Plattform – die einzelne Box, auf der nahezu jeder Anwendungscontainer
veröffentlicht oder von der er abonniert. Das Swiss AI Agent Protocol läuft darüber und unterscheidet dauerhafte
**Kontrollereignisse** (Workflow-Status, auf JetStream) von ephemeren **Anzeigeereignissen** (Observability, auf NATS
Core). Diese Trennung ermöglicht es der Chat-UI, die Argumentation eines Agenten in Echtzeit zu visualisieren, ohne die
tatsächliche Ausführung des Agenten zu beeinträchtigen. Das Protokoll selbst ist im
[Swiss AI Agent Protocol](../3_swiss_ai_agent_protocol/) dokumentiert.

<likec4-view view-id="tier_eventing" style="display:block;height:480px"></likec4-view>

## Identitäts- und Edge-Schicht

Alles an der Netzwerkgrenze. Traefik ist der einzige Ingress-Punkt, der TLS terminiert und jedes `*.${DOMAIN}`-Subdomain
an den richtigen Service routet. Keycloak ist der Identitätsbroker, der Kunden-Identitätsanbieter föderiert und die
OIDC-Tokens und Realm-Rollen der Plattform ausstellt. Eine Reihe von oauth2-proxy-Instanzen bildet ein einheitliches
OIDC-Gate vor den Operator-UIs (Dagster, Backup, Attu, SeaweedFS Filer), und pgbouncer poolt Datenbankverbindungen für
Dagster. Die Anwendungscontainer, die diese voranstellen, werden in ihren eigenen Schichten gezeigt – diese Ansicht
handelt von der Edge-Maschinerie selbst.

<likec4-view view-id="tier_identity_edge" style="display:block;height:440px"></likec4-view>

## Observability-Schicht

Der OTEL Collector aggregiert OpenTelemetry-Traces und -Logs von jedem Anwendungscontainer und leitet sie an Langfuse
weiter, das AI-spezifische Observability hinzufügt – vollständige Prompt-/Response-Erfassung, Kostenverfolgung pro Trace
und RAG-Retrieval-Tracing. Standardmässig bleibt alles innerhalb des Deployments; der Collector kann auch so
konfiguriert werden, dass er in einen kundenverwalteten Sink (SigNoz, Grafana Cloud, Honeycomb) exportiert. Langfuses
eigene Datenabhängigkeiten (ClickHouse, Postgres, Valkey, SeaweedFS) gehören zur Datenschicht.

<likec4-view view-id="tier_observability" style="display:block;height:440px"></likec4-view>

## Hilfsschicht

Hilfsservices, die die Anwendungsschicht unterstützen, ohne zu ihrem Kern zu gehören: SearXNG für die Websuche, Jupyter
als Code-Ausführungs-Sandbox, Playwright für die Browser-Automatisierung und Attu als Milvus-Admin-Konsole für
Operatoren. Diese werden hauptsächlich von OpenWebUI (als Agenten-Tools) und von Operatoren genutzt.

<likec4-view view-id="tier_utility" style="display:block;height:420px"></likec4-view>

## Paketzentrierte Ansichten

Die oben genannten Schichtenansichten teilen die Plattform horizontal – nach funktionaler Ebene. Die
[Paketzentrierten Ansichten](../5_package_views/) teilen sie anders: ein Diagramm pro Erstanbieter-Paket, zentriert auf
dieses Paket mit all seinen Nachbarn, für Entwickler, die innerhalb eines bestimmten Pakets arbeiten werden.
