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
| `AIHubAccess`   | Voraussetzung für jeden Login. Benutzer ohne diese Rolle werden beim Login abgewiesen, ob über den IdP oder direkt mit Keycloak-Passwort.              |
| `AIHubSysAdmin` | Plattform-Administrator: schützt die OAuth2-Proxy-Admin-Tools (Dagster, Attu, SeaweedFS, Backup) sowie Langfuse und kennzeichnet Superuser in der API. |

## Tenant-Gruppen

Tenant-Zugehörigkeit wird als Keycloak-Gruppen unter `/tenants/<tenant-id>` modelliert. Die Startup-Tenant-Gruppe wird
beim Realm-Import angelegt und als Default-Gruppe gesetzt, sodass jeder neue Benutzer automatisch Mitglied wird. Der
Client-Scope `tenants` stellt die Gruppenpfade als Token-Claim bereit, über den die API die Tenants eines Benutzers
auflöst (siehe ADR `2026_02_20_keycloak_tenant_assignment_via_groups`).

## Clients

| Client                                                                       | Typ                 | Verwendet von                                                                                                             |
| ---------------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `aihub-frontend`                                                             | Public, PKCE        | Haupt-Web-UI **und** Sysadmin-Web-UI (gleiches Realm-Cookie → gemeinsames SSO)                                            |
| `openwebui`                                                                  | Confidential        | Open-WebUI-Chat-Oberfläche (OIDC-Login, erhält den `roles`-Claim)                                                         |
| `oauth2-proxy-dagster` / `-datalake` / `-attu` / `-backup`                   | Confidential        | Die OAuth2-Proxy-Sidecars vor den Admin-UIs; Zugriff über den `roles`-Claim (`AIHubSysAdmin`) beschränkt                  |
| `langfuse`                                                                   | Confidential, PKCE  | Natives Langfuse-Keycloak-SSO; trägt den Marker-Scope `langfuse-sysadmin-gate`                                            |
| `aihub-api-service`                                                          | Nur Service-Account | Das API-Backend; besitzt `realm-management`-Rollen (`manage-users`, `view-groups`, …) für die Benutzer-/Gruppenverwaltung |
| `KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_ID` (Standard `external-knowledge-writer`) | Nur Service-Account | Ein externes System, das Dokumente in Wissensdatenbanken eines Tenants hochlädt (siehe unten)                             |

### Externer Wissens-Schreiber

Ein externes System, etwa ein Dokumentenmanagementsystem, kann über
`POST /api/v1/{tenant}/knowledge/databases/{db}/namespaces/{ns}/documents/upload/initiate` und `.../validate` Dokumente
in die Wissensdatenbanken eines Tenants hochladen. Es meldet sich mit dem Client-Credentials-Grant eines verwalteten,
vertraulichen Clients an. Die Client-ID kommt aus `KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_ID`, das Secret aus
`KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_SECRET`. Der Client hat die Default-Scopes `profile` und `tenants` und einen
Audience-Mapper, der `account` hinzufügt, das die API in jedem Access Token verlangt. Weil der Client verwaltet ist,
bleibt er bei jedem Deploy erhalten. Ein in der Admin-Konsole von Hand angelegter Client wird beim nächsten Start
gelöscht.

Der Client stellt nur ein Token aus. Was das Token erreicht, ist Betriebskonfiguration in Keycloak und in der API, die
kein Deploy anfasst. Die Schritte in dieser Reihenfolge ausführen, **vor dem ersten API-Aufruf des Schreibers**:

1. **Upload-Rolle anlegen**, in jedem Tenant, in den der Schreiber schreibt. Sie bekommt nur diese Regeln:

   | Regel                                    | Warum                                                                                                  |
   | ---------------------------------------- | ------------------------------------------------------------------------------------------------------ |
   | `aihub.user.service.knowledge`           | Jeder Knowledge-Endpunkt prüft zuerst den Dienst. Ohne diese Regel lehnt `initiate` mit 403 ab.        |
   | `aihub.admin.knowledge.<db>.<namespace>` | `initiate` und `validate` verlangen Admin-Rechte auf dem Namespace. `<db>.>` gilt für alle Namespaces. |

   Nicht `AIHubKnowledgeAdmin` verwenden: Diese Rolle kann auch Datenbanken anlegen und löschen. Die Signup-Rolle
   `AIHubUser` (`aihub.user.>`) reicht ebenfalls nicht, weil sie keine Admin-Regel enthält.

   Mehr braucht der Schreiber nur, wenn er die Datenbank selbst anlegt. Dafür braucht er zusätzlich
   `aihub.admin.knowledge` und Zugriff auf das Embedding-Modell (`aihub.user.model.embedding.*`). Einfacher ist es, die
   Datenbank von einem Admin anlegen zu lassen.

2. **Upload-Rolle zuweisen**: In der Benutzerverwaltung des Tenants die Upload-Rolle dem Service-Account-Benutzer des
   Clients (`service-account-<Client-ID>`) geben. Hat der Benutzer beim ersten Aufruf keine Rolle im Tenant, gibt ihm
   die API die Signup-Rollen (`AIHUB_USER_SIGNUP_REGULAR_USER_ROLES`) oder, als erstem Mitglied des Tenants, die
   Admin-Rollen (`AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES`). Die vorher zugewiesene Rolle verhindert beides.

3. **Start-Tenant**: `/tenants/<Start-Tenant>` ist eine Default-Gruppe des Realms. Der Service-Account-Benutzer ist
   deshalb vom Anlegen an Mitglied des Start-Tenants. Entweder ihn aus dieser Gruppe entfernen (Admin-Konsole → Clients
   → der Client → Service account roles → Link zum Benutzer → Groups) oder ihm dort vor dem ersten Aufruf eine harmlose
   Rolle geben. Sonst bekommt er beim ersten Aufruf in diesem Tenant die Signup-Rollen oder die Admin-Rollen.

4. **Weitere Tenants**: Den Service-Account-Benutzer in die Gruppe `/tenants/<tenant-id>` jedes weiteren Tenants
   aufnehmen, in den er schreibt, jeweils nach Schritt 2 für diesen Tenant. Der `tenants`-Claim nennt dann diese
   Tenants.

Eine Änderung von `KEYCLOAK_KNOWLEDGE_WRITER_CLIENT_ID` ersetzt den Client und damit den Service-Account-Benutzer; seine
Rollen und Gruppenmitgliedschaften müssen dann neu gesetzt werden. Eine Installation, die den Schreiber nicht nutzt,
sollte den Service-Account-Benutzer aus der Gruppe des Start-Tenants entfernen (Schritt 3). Danach erreichen seine
Tokens keinen Tenant.

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
- **`browser-aihub` + seine Gates** — der Browser-Flow des Realms. Nach der Authentifizierung laufen zwei bedingte
  Zugriffsverweigerungen: der Sub-Flow `aihub-access-gate-browser` weist Benutzer ohne `AIHubAccess` ab (der
  Post-Broker-Flow läuft für lokale Realm-Benutzer nie, daher ist dies ihre einzige Prüfung), danach beschränkt das
  Langfuse-Sysadmin-Gate Langfuse-Logins auf `AIHubSysAdmin`. Mechanismus, Gründe für die Replikation des eingebauten
  Browser-Flows und die strukturellen Fallstricke sind in [Langfuse-Sysadmin-Gate](1_langfuse_sysadmin_gate/)
  dokumentiert.

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
