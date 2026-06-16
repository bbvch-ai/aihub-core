---
title: Keycloak-Konfiguration
description: Überblick über den aihub-Realm — Clients, Scopes, Rollen, Tenant-Gruppen, Identity Brokering und wie die Konfiguration laufende Instanzen erreicht
---

# Keycloak-Konfiguration

Keycloak ist die Identity-and-Access-Management-Komponente der Plattform. Die gesamte Konfiguration ist Code: Drei
Jinja2-Templates unter `infra/deployment/templates/configs/` werden pro Deployment-Stage nach `infra/configs/keycloak/`
gerendert und in den Keycloak-Container gemountet.

| Datei                                 | Inhalt                                                      | Anwendung                                                   |
| ------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| `keycloak-realm.json.j2`              | Der `aihub`-Realm: Clients, Scopes, Rollen, Flows, …        | Nur beim ersten Container-Start (`--import-realm`)          |
| `keycloak-identity-providers.json.j2` | Externe IdPs (Azure AD) und ihre Mapper                     | Bei jedem Container-Start (`partialImport`, überschreibend) |
| `keycloak-entrypoint.sh.j2`           | Env-Var-Substitution, Import-Orchestrierung, kcadm-Abgleich | Bei jedem Container-Start                                   |

## Der `aihub`-Realm

Der Realm definiert das Login-Verhalten der Plattform: Benutzer melden sich mit ihrer E-Mail-Adresse an
(`registrationEmailAsUsername`), Selbstregistrierung ist deaktiviert (Benutzer kommen vom Identity Provider oder werden
von Admins angelegt), Brute-Force-Schutz und "Remember me" sind aktiv, und das eigene `aihub`-Login-Theme wird
verwendet. TLS ist für externe Anfragen auf allen Stages ausser `dev` erforderlich. Der Realm bindet einen eigenen
Browser-Flow (`browser-aihub`, siehe [Langfuse-Sysadmin-Gate](1_langfuse_sysadmin_gate/)).

## Realm-Rollen

Es gibt nur zwei Realm-Rollen — alles Feingranulare wird über Tenant-bezogene Rollen *innerhalb* der Plattform
verwaltet, nicht in Keycloak:

| Rolle           | Wirkung                                                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AIHubAccess`   | Voraussetzung für jeden Login. Benutzer ohne diese Rolle werden bei der Post-Login-Prüfung des IdP abgewiesen.                                         |
| `AIHubSysAdmin` | Plattform-Administrator: schützt die OAuth2-Proxy-Admin-Tools (Dagster, Attu, SeaweedFS, Backup) sowie Langfuse und kennzeichnet Superuser in der API. |

## Tenant-Gruppen

Tenant-Zugehörigkeit wird als Keycloak-Gruppen unter `/tenants/<tenant-id>` modelliert. Die Startup-Tenant-Gruppe wird
beim Realm-Import angelegt und als Default-Gruppe gesetzt, sodass jeder neue Benutzer automatisch Mitglied wird. Der
Client-Scope `tenants` stellt die Gruppenpfade als Token-Claim bereit, über den die API die Tenants eines Benutzers
auflöst (siehe ADR `2026_02_20_keycloak_tenant_assignment_via_groups`).

## Clients

| Client                                                     | Typ                 | Verwendet von                                                                                                             |
| ---------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `aihub-frontend`                                           | Public, PKCE        | Haupt-Web-UI **und** Sysadmin-Web-UI (gleiches Realm-Cookie → gemeinsames SSO)                                            |
| `openwebui`                                                | Confidential        | Open-WebUI-Chat-Oberfläche (OIDC-Login, erhält den `roles`-Claim)                                                         |
| `oauth2-proxy-dagster` / `-datalake` / `-attu` / `-backup` | Confidential        | Die OAuth2-Proxy-Sidecars vor den Admin-UIs; Zugriff über den `roles`-Claim (`AIHubSysAdmin`) beschränkt                  |
| `langfuse`                                                 | Confidential, PKCE  | Natives Langfuse-Keycloak-SSO; trägt den Marker-Scope `langfuse-sysadmin-gate`                                            |
| `aihub-api-service`                                        | Nur Service-Account | Das API-Backend; besitzt `realm-management`-Rollen (`manage-users`, `view-groups`, …) für die Benutzer-/Gruppenverwaltung |

## Client-Scopes

Neben den Standard-Scopes `openid` / `profile` / `email` definiert der Realm:

| Scope                    | Mapper                              | Zweck                                                                 |
| ------------------------ | ----------------------------------- | --------------------------------------------------------------------- |
| `roles`                  | Realm-Rollen-Mapper → `roles`-Claim | Macht Realm-Rollen für Clients sichtbar (Frontend, OAuth2-Proxies, …) |
| `tenants`                | Gruppen-Mapper → `tenants`-Claim    | Tenant-Auflösung aus den `/tenants/...`-Gruppenpfaden                 |
| `langfuse-sysadmin-gate` | *keiner* (Marker-Scope)             | Aktiviert das Langfuse-Deny-Gate in den Authentifizierungs-Flows      |

## Identity Brokering (Azure AD)

Der Realm agiert als Identity Broker (siehe ADR `2026_02_28_keycloak_as_identity_broker`): Der Provider `azure-ad`
authentifiziert Benutzer gegen Microsoft Entra ID (PKCE, `syncMode: FORCE`). Seine Mapper übernehmen E-Mail, Vor-/
Nachname und Benutzername aus dem Azure-Token; zwei Rollen-Mapper übersetzen die Azure-App-Rollen-Claims `AIHubAccess`
und `AIHubSysAdmin` in die gleichnamigen Realm-Rollen. Wegen des FORCE-Sync-Modus werden die Rollen **bei jedem
Broker-Login neu synchronisiert** — wird eine App-Rolle in Azure entfernt, verliert der Benutzer die Realm-Rolle beim
nächsten Login (und umgekehrt); manuell zugewiesene Realm-Rollen überleben bei Broker-Benutzern nicht. Der
Post-Login-Flow des Providers weist jeden Benutzer ab, dessen Token `AIHubAccess` fehlt.

## Angelegte Benutzer

Der Realm-Import erstellt einen Superuser (Zugangsdaten und Rollen aus den `SUPERUSER_*`-Umgebungsvariablen —
standardmässig mit `AIHubAccess` und `AIHubSysAdmin`) sowie den Service-Account-Benutzer für `aihub-api-service`.

## Authentifizierungs-Flows

Zwei eigene Mechanismen erweitern die eingebauten Flows:

- **`Post Broker Login - AIHubAccess Check`** — läuft nach jedem Azure-AD-Login und weist Benutzer ohne die Realm-Rolle
  `AIHubAccess` ab.
- **`browser-aihub` + das Langfuse-Sysadmin-Gate** — der Browser-Flow des Realms mit einer bedingten
  Zugriffsverweigerung, die Langfuse-Logins auf `AIHubSysAdmin` beschränkt. Mechanismus, Gründe für die Replikation des
  eingebauten Browser-Flows und die strukturellen Fallstricke sind in
  [Langfuse-Sysadmin-Gate](1_langfuse_sysadmin_gate/) dokumentiert.

## Wie die Konfiguration laufende Instanzen erreicht

Das Entrypoint-Skript ersetzt Umgebungsvariablen in den JSON-Templates (reines Bash-`envsubst`; das Keycloak-Image
bringt kein Template-Tooling mit) und wendet danach drei Schichten mit unterschiedlichen Lebenszyklen an:

1. **Realm-JSON** — Import via `--import-realm` nur beim *ersten* Start. Keycloak importiert einen bestehenden Realm nie
   erneut; Änderungen an der Realm-Datei erreichen bereits initialisierte Datenbanken daher nicht von selbst.
2. **Identity Provider** — bei *jedem* Start über die Admin-API angewendet (`partialImport`, überschreibend); IdP- und
   Mapper-Änderungen werden mit einem Container-Neustart ausgerollt.
3. **Langfuse-Sysadmin-Gate** — Authentifizierungs-Flows werden von `partialImport` nicht unterstützt, daher gleicht der
   Entrypoint das Gate bei jedem Start idempotent per `kcadm` ab (Details in
   [Langfuse-Sysadmin-Gate](1_langfuse_sysadmin_gate/)).
