---
title: Benutzer- und Rollenverwaltung
description: Definieren und weisen Sie die App-Rollen zu, die den Zugriff auf den Swiss AI Hub gewähren
source_sha: 87c815508b4dc3f54c9207c16f6b953bbd1c0dea65215fcde6ed90915fce1e13
---

# Benutzer- und Rollenverwaltung

Der Zugriff auf den Swiss AI Hub wird über **App-Rollen** in der Azure App-Registrierung gewährt. Wenn sich ein Benutzer
anmeldet, nimmt Entra ID die zugewiesenen App-Rollen in den `roles`-Claim auf; Keycloak bildet jede dieser Rollen auf
eine Realm-Rolle desselben Namens ab.

Zwei Rollen wirken sich in der Plattform aus — definieren Sie beide in der App-Registrierung und weisen Sie sie den
Benutzern zu.

## App-Rollen definieren

Fügen Sie in der App-Registrierung diese App-Rollen hinzu (App-Rollen-Blade oder das Manifest). Der **Wert** muss exakt
übereinstimmen — er wird von Keycloak abgebildet:

| Anzeigename     | Wert            | Gewährt                                                                                  |
| --------------- | --------------- | ---------------------------------------------------------------------------------------- |
| AI-Hub Access   | `AIHubAccess`   | Berechtigung zur Anmeldung. **Erforderlich** — ohne diese wird die Anmeldung verweigert. |
| AI-Hub Sysadmin | `AIHubSysAdmin` | Plattformadministrator + Zugriff auf Admin-Tools (Dagster, Attu, …).                     |

Entsprechende `appRoles`-Manifesteinträge:

```json
"appRoles": [
  {
    "displayName": "AI-Hub Access",
    "value": "AIHubAccess",
    "description": "Allows login to the Swiss AI Hub",
    "allowedMemberTypes": ["User"],
    "isEnabled": true
  },
  {
    "displayName": "AI-Hub Sysadmin",
    "value": "AIHubSysAdmin",
    "description": "Platform administrator and admin tool access",
    "allowedMemberTypes": ["User"],
    "isEnabled": true
  }
]
```

::: warning
`AIHubAccess` ist obligatorisch. Keycloaks Login-Flow verweigert jedem Benutzer den Zugriff, der diese Rolle nicht
besitzt, unabhängig von anderen Rollen. Jeder Benutzer, der die Plattform erreichen soll, muss `AIHubAccess` zugewiesen
bekommen.
:::

## Rollen Benutzern zuweisen

Weisen Sie die App-Rollen Benutzern oder Gruppen in der zugehörigen **Enterprise Application** zu — siehe Microsofts
[Benutzer und Gruppen einer Anwendung zuweisen](https://learn.microsoft.com/entra/identity/enterprise-apps/assign-user-or-group-access-portal).
Zugewiesene App-Rollen erscheinen automatisch im `roles`-Claim des Tokens; es ist keine Konfiguration optionaler Claims
erforderlich.

Eine typische Zuweisung:

- **Alle Plattformbenutzer** → `AIHubAccess`
- **Plattformadministratoren** → `AIHubAccess` **und** `AIHubSysAdmin`

::: tip
Die Zuweisung einer Rolle zu einer **Gruppe** (anstatt zu einzelnen Benutzern) erfordert eine Microsoft Entra ID P1-
oder P2-Lizenz und `"Group"` in den `allowedMemberTypes` der Rolle. Die Zuweisung pro Benutzer funktioniert auf jeder
Stufe.
:::
