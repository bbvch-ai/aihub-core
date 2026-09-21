---
title: Langfuse-Sysadmin-Gate
description: Wie der benutzerdefinierte Browser-Flow und das Langfuse-Sysadmin-Gate aufgebaut sind und welche Strukturregeln bei Änderungen gelten
---

# Langfuse-Sysadmin-Gate

Langfuse-Logins sind über benutzerdefinierte Authentifizierungs-Flows im `aihub`-Realm auf Benutzer mit der Realm-Rolle
`AIHubSysAdmin` beschränkt. Die Durchsetzung erfolgt vollständig in Keycloak (kein oauth2-proxy) und ist in
`infra/deployment/templates/configs/keycloak-realm.json.j2` definiert — siehe [Keycloak-Konfiguration](../) für den
Realm-Überblick. Die Entscheidungsgrundlage ist im ADR
`docs/arc42/decisions/2026_06_11_langfuse_access_restricted_to_sysadmins.md` dokumentiert.

## Wie das Gate funktioniert

Ein Mapper-loser **Marker-Client-Scope** `langfuse-sysadmin-gate` ist ausschliesslich am `langfuse`-Client als
*Default*-Scope hinterlegt. Ein bedingter Sub-Flow (das "Gate") prüft:

1. `Condition - client scope` — trägt der anfragende Client den Marker-Scope?
2. `Condition - user role` — `AIHubSysAdmin`, **negiert** (wahr, wenn dem Benutzer die Rolle fehlt)
3. `Deny access` — verweigert den Login

Bedingungen innerhalb eines bedingten Sub-Flows werden UND-verknüpft, daher greift die Verweigerung nur bei
Langfuse-Logins von Nicht-Sysadmins. Für alle anderen Clients ist die erste Bedingung falsch und das Gate wird
vollständig übersprungen. Das macht einen Realm-weiten Flow sicher: Die Client-Eingrenzung steckt im Marker-Scope, nicht
in Client-spezifischen Flow-Bindings. Da der Marker ein *Default*-Scope ist, greift die Bedingung unabhängig vom
`scope`-Parameter der Anwendung — Langfuse selbst benötigt dafür keine Konfiguration.

Das Gate existiert zweimal, weil Keycloak zwei getrennte Login-Pfade hat:

| Gate-Sub-Flow               | Eltern-Flow                             | Deckt ab                                                    |
| --------------------------- | --------------------------------------- | ----------------------------------------------------------- |
| `langfuse-gate-browser`     | `browser-aihub` (eigener Browser-Flow)  | Bestehende SSO-Cookie-Sitzungen und direkte Keycloak-Logins |
| `langfuse-gate-post-broker` | `Post Broker Login - AIHubAccess Check` | Neue Logins über den externen IdP (z. B. Azure AD)          |

Neue Broker-Logins setzen den Browser-Flow nach dem externen Redirect **nicht** fort — der Post-Broker-Flow ist der
einzige Einhängepunkt auf diesem Pfad, weshalb beide Gates für vollständige Abdeckung nötig sind. Sub-Flows können nicht
von mehreren Eltern-Flows geteilt werden und Authenticator-Config-Aliase sind Realm-weit eindeutig — daher zwei
strukturell identische Kopien mit `-browser-`- bzw. `-post-broker-`-präfixierten Config-Aliasen.

## Warum der Browser-Flow repliziert wird (`browser-aihub*`-Flows)

Keycloaks eingebauter `browser`-Flow ist unveränderlich (`builtIn: true`), und Flows kennen keine Vererbung und keinen
Include-Mechanismus — um etwas hinzuzufügen, muss der gesamte Flow-Baum neu aufgebaut und als Realm-Browser-Flow
gebunden werden (Realm-Schlüssel `"browserFlow": "browser-aihub"`). Genau das sind die `browser-aihub*`-Aliase:

| Flow                            | Rolle                                                                          |
| ------------------------------- | ------------------------------------------------------------------------------ |
| `browser-aihub`                 | Oberste Ebene: `[REQUIRED authenticate] → [CONDITIONAL langfuse-gate-browser]` |
| `browser-aihub-authenticate`    | Die eingebauten Alternativen: Cookie-SSO, IdP-Redirector, Formulare            |
| `browser-aihub-forms`           | Benutzername/Passwort-Formular (Replikat des eingebauten `forms`)              |
| `browser-aihub-conditional-2fa` | Bedingtes OTP (Replikat des eingebauten `Browser - Conditional 2FA`)           |

Die Aliase tragen das Präfix `browser-aihub-`, weil Flow-Aliase Realm-weit eindeutig sind und die eingebauten Namen
(`forms`, …) bereits vergeben sind. Das entspricht dem, was die Aktion *Copy flow* der Admin-Konsole erzeugen würde —
das Realm-JSON deklariert die Kopie nur explizit.

## Strukturregeln bei Änderungen an diesen Flows

1. **Niemals einen CONDITIONAL-Sub-Flow auf dieselbe Ebene wie ALTERNATIVE-Ausführungen setzen.** Keycloak ignoriert
   dann die Alternativen und der Login bricht für *alle* Clients. Deshalb sind die Authentifizierungs-Alternativen im
   REQUIRED-Wrapper `browser-aihub-authenticate` verschachtelt und das Gate steht neben dem Wrapper, nicht neben den
   Alternativen.
2. **`description`-Felder von Flows sind auf 255 Zeichen begrenzt** (Datenbank-Spaltenlimit) — längere Werte brechen den
   gesamten Realm-Import beim ersten Start ab.
3. **Replizierte Flows erhalten keine Built-in-Flow-Migrationen.** Keycloak-Versions-Upgrades fügen `browser-aihub`
   keine neuen Ausführungen hinzu (z. B. Passkeys); der Flow ist bei grossen Keycloak-Sprüngen zu überprüfen.

## Wie das Gate laufende Instanzen erreicht

Das Realm-JSON wird nur beim **ersten** Keycloak-Start importiert, und Keycloaks `partialImport`-API unterstützt keine
Authentifizierungs-Flows. `infra/deployment/templates/configs/keycloak-entrypoint.sh.j2` gleicht das Gate daher bei
jedem Container-Start idempotent per `kcadm` ab: Marker-Scope anlegen → an den `langfuse`-Client hängen → Flows aufbauen
→ Realm-Browser-Flow binden. Jeder Schritt prüft zuerst die Existenz, sodass frische Importe zu No-Ops werden und
bereits initialisierte Datenbanken beim nächsten Container-Neustart ohne manuelle Schritte konvergieren.
