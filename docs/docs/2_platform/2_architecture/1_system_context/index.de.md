---
title: Systemkontext
description: C4 Level 1 – Personen und externe Systeme, die mit dem Swiss AI Hub interagieren.
source_sha: 3530f5f6cf1f6175f785b664d7a166fc81f653ec13c361b772a1f36acd8d0d8e
---

# Systemkontext

Die Systemkontext-Ansicht beantwortet die weiteste Frage: Wer interagiert mit dem Swiss AI Hub, und mit welchen externen
Systemen integriert er sich? Es ist C4 Level 1 – die Plattform erscheint als einzelne Box, ohne interne Details. Der
Zweck ist es, eine klare Grenze zu ziehen: Jeder und alles, was mit der Plattform *kommuniziert*, erscheint hier; alles,
was sich *innerhalb* befindet, wird auf die [Container](../2_containers/) Ansicht verschoben.

Stellen Sie es sich als zwei Ringe um das zentrale System vor. Oben sind die **Personen**, die die Plattform nutzen,
jede in einer eigenen Rolle mit einer eigenen Oberfläche. Am Rande sind die **externen Systemkategorien**, mit denen die
Plattform integriert wird – und eine Kernidee des Swiss AI Hub ist, dass dies *steckbare Fähigkeiten* sind, keine festen
Anbieterentscheidungen. Die Plattform wird vorkonfiguriert mit sinnvollen Standardeinstellungen ausgeliefert, aber sie
föderiert, routet oder adaptiert sich an jede konforme Implementierung, die ein Kunde mitbringt.

<likec4-view view-id="index" style="display:block;height:600px"></likec4-view>

## Akteure

- **Enterprise User** — Jedes Mandantenmitglied. Umfasst sowohl reguläre Benutzer als auch Mandantenadministratoren, die
  dieselbe Oberfläche (Admin UI + OpenWebUI + Main API) nutzen, wobei die Sichtbarkeit von Funktionen durch
  mandantenbezogene Rollen gesteuert wird.
- **System Administrator** — Plattformadministrator über alle Mandanten hinweg. Besitzt die `AIHubSysAdmin` Realm-Rolle;
  nutzt die separate Sysadmin-Ebene (`sysadmin.${DOMAIN}`), um Mandanten, Benutzer-Mandanten-Zuordnungen und
  plattformweite Konfiguration zu verwalten.
- **Collaboration Channel User** — Teilmenge der Mandantenbenutzer, die mit Swiss AI Hub Agents über
  Kollaborationskanäle (Slack, Teams, Webex, E-Mail) interagieren, anstatt über die dedizierte Web-UI.
- **Platform Operator** — Plattform DevOps / SRE Ingenieur. Besitzt die `AIHubDeveloper` Realm-Rolle; nutzt
  Observability- und operative Oberflächen (Dagster, Langfuse, Attu, Backup, SeaweedFS Filer).

## Externe Integrationen

Jede externe Box repräsentiert eine *steckbare Integrationsfähigkeit*, nicht einen spezifischen Anbieter. Die Plattform
wird vorkonfiguriert für die aufgeführten Beispiele ausgeliefert, unterstützt aber jede konforme Implementierung über
ihr jeweiliges Gateway / ihren Adapter:

- **Identity Provider** — Föderiert in unser Keycloak Realm über OIDC/SAML. Beispiele: Entra ID, Okta, lokale LDAP/AD,
  Google, GitHub.
- **LLM Provider** — Pro Deployment im internen LiteLLM-Gateway konfiguriert. Alle Mandanten in einem Deployment teilen
  sich dieselbe Modell-Roster. Beispiele: Swiss LLM Cloud, OpenAI, Anthropic, Azure OpenAI, Gemini.
- **Document Source** — Synchronisiert über Rclone (70+ unterstützte Backends) oder direkte Integration. Beispiele:
  SharePoint (direktes MS Graph), OneDrive, Google Drive, Azure Blob, S3, Dropbox.
- **Collaboration Platform** — Geroutet über das Microsoft Agents SDK. Beispiele: Slack, Microsoft Teams, Webex, E-Mail.
- **Observability Sink** — Vom Kunden verwalteter Trace-/Log-Empfänger über OTEL-Exporter. Beispiele: SigNoz, Grafana
  Cloud, Honeycomb.
- **Notification Target** — Einseitiges Alarmziel über Apprise (80+ unterstützte Ziele). Beispiele: Slack-Kanäle,
  Discord-Webhooks, E-Mail, PagerDuty.
- **External MCP Tools** — Vom Kunden exponierte MCP-Server, die von Agents als Tools genutzt werden. Beispiele:
  domänenspezifische APIs, interne CRMs, Ticketing-Systeme.

Für tiefergehende Integrationsmechanismen siehe die [Container-Ansicht](../2_containers/), wo jede externe Kategorie
spezifischen Containern zugeordnet ist, die sie überbrücken.
