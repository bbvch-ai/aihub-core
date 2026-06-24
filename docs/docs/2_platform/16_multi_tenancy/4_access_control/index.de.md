---
title: Technische Referenz - Zugriffssteuerung
source_sha: 687cf8c26a74c5b75eba6ef75c23c12905f088c0bc886cb4aedbdd667fbd7e97
---

# Technische Referenz: Zugriffssteuerung

Dieses Kapitel dokumentiert die technischen Details, wie die Plattform die Zugriffssteuerung durchsetzt. Diese
Informationen sind nützlich für Systemadministratoren, die Mandanten und Rollen konfigurieren, sowie für Entwickler, die
die Plattform erweitern.

## Format der Zugriffsregeln

Zugriffsregeln verwenden ein hierarchisches Muster: `aihub.[user|admin].<service>.<resource>.<identifier>`

Beispiele:

```
aihub.user.agent.>                      # All agents (user access)
aihub.admin.agent.research.*            # All research agents (admin access)
aihub.user.knowledge.hr-docs.policies   # Specific knowledge namespace
aihub.admin.service.tenant              # Tenant management service
```

### Platzhalter

**Ein-Ebenen-Platzhalter** (`*`) entspricht genau einem Segment:

- `agent.research.*` entspricht `agent.research.instance-1`, aber nicht `agent.research.team.instance-1`

**Mehr-Ebenen-Platzhalter** (`>`) entspricht einem oder mehreren Segmenten am Ende:

- `agent.>` entspricht `agent.research.instance-1`, `agent.analysis.team.special` und jedem anderen Agentenpfad
- Muss das letzte Token in der Regel sein

### Admin- vs. Benutzerregeln

Regeln, die mit `aihub.admin.*` beginnen, gewähren administrativen Zugriff. Benutzer mit Admin-Zugriff haben automatisch
gleichwertigen Benutzerzugriff.

Ein Benutzer mit `aihub.admin.agent.>` kann auf Ressourcen zugreifen, die entweder `aihub.admin.agent.*` oder
`aihub.user.agent.*` erfordern.

## Auflösung von Berechtigungen

Wenn eine Anfrage eingeht, führt die Plattform Folgendes aus:

1. Extrahiert die Benutzeridentität aus dem Authentifizierungstoken
2. Liest den `X-Tenant-Id`-Header, um den Mandantenkontext zu bestimmen
3. Fragt die Rollen des Benutzers innerhalb dieses spezifischen Mandanten ab
4. Sammelt alle Zugriffsregeln aus diesen Rollen
5. Ruft die Zugriffsregeln des Mandanten ab
6. Prüft, ob sowohl der Mandant als auch der Benutzer die angeforderte Aktion zulassen

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database

    User->>API: Request with X-Tenant-Id
    API->>Database: Get user roles in tenant
    Database-->>API: Role IDs
    API->>Database: Get access rules for roles
    Database-->>API: User access rules
    API->>Database: Get tenant access rules
    Database-->>API: Tenant access rules
    API->>API: Check both rule sets
    API-->>User: Success or 403 Forbidden
```

### Zweischichtige Überprüfung

Der Zugriff erfordert das Bestehen beider Schichten:

**Schicht 1: Mandantengrenze** – Erlaubt der Mandant diese Ressource überhaupt?

Wenn die Zugriffsregeln des Mandanten die angeforderte Ressource nicht enthalten, wird der Zugriff sofort verweigert,
ohne die Benutzerrollen zu prüfen.

**Schicht 2: Benutzerberechtigungen** – Erlaubt die Rolle des Benutzers diese Aktion?

Nachdem bestätigt wurde, dass der Mandant die Ressource erlaubt, prüft das System, ob die Rollen des Benutzers die
erforderliche Berechtigung erteilen.

Beide müssen bestanden werden, damit der Zugriff gewährt wird.

### Beispiel

Mandant hat: `aihub.user.agent.research.*`

Benutzer hat: `aihub.user.agent.>` (aus seiner Rolle)

Benutzeranfrage: `aihub.user.agent.research.instance-1`

- Mandantenprüfung: ✓ (Mandant erlaubt Forschungs-Agents)
- Benutzerprüfung: ✓ (Benutzerrolle erlaubt alle Agents)
- Ergebnis: Zugriff gewährt

Benutzeranfrage: `aihub.user.agent.finance.instance-1`

- Mandantenprüfung: ✗ (Mandant erlaubt nur Forschungs-Agents)
- Ergebnis: Zugriff verweigert (Benutzerprüfung nicht ausgewertet)

## Berechtigungen auf Service-Ebene

Jeder Service erfordert eine Basisberechtigung: `aihub.user.service.<service-name>`

Bevor ressourcenspezifische Berechtigungen geprüft werden, verifiziert das System, dass der Benutzer Zugriff auf den
Service selbst hat.

Um auf einen Agent zuzugreifen, benötigen Sie:

- Service-Zugriff: `aihub.user.service.agent`
- Ressourcenzugriff: `aihub.user.agent.<agent-class>.<agent-id>`

Wenn der Mandant keinen Service-Zugriff gewährt, sind keine Ressourcen in diesem Service zugänglich, unabhängig von
anderen Regeln.

## Pfadparameter-Substitution

Berechtigungsvorlagen verwenden Platzhalter, die aus der Anfrage aufgelöst werden:

Vorlage: `aihub.user.agent.{agent_class}.{agent_id}`

Anfrage: `GET /api/v1/agents/research/instance-alpha`

Aufgelöste Berechtigung: `aihub.user.agent.research.instance-alpha`

Das System prüft diese konkrete Berechtigung anhand der Benutzer- und Mandanten-Zugriffsregeln.

## Zugriffsebenen

Das System gibt drei Ebenen zurück:

**ACCESS_DENIED**: Keine Berechtigung. Gibt HTTP 403 zurück.

**ACCESS_USER**: Zugriff auf Benutzerebene, um die Ressource anzuzeigen und mit ihr zu interagieren.

**ACCESS_ADMIN**: Zugriff auf Administratorebene, um die Ressource zu ändern, zu konfigurieren oder zu löschen.

Controller können zwischen Benutzer- und Administratorzugriff für Prüfzwecke unterscheiden, obwohl viele Operationen nur
prüfen, ob der Zugriff gewährt (nicht verweigert) wird.

## Konfiguration über Umgebungsvariablen

Konfigurieren Sie das Standardverhalten über Umgebungsvariablen:

```bash
# Startup tenant (seeded on first boot; an ordinary tenant thereafter)
AIHUB_STARTUP_TENANT_NAME="Swiss AI Hub"
AIHUB_STARTUP_TENANT_ACCESS_RULES="aihub.admin.>"

# Automatic user signup
AIHUB_USER_SIGNUP_DEFAULT_TENANT="default"
AIHUB_USER_SIGNUP_DEFAULT_ROLES="AIHubUser,AIHubAgentUser"
FIRST_AIHUB_USER_SIGNUP_DEFAULT_ROLES="AIHubAdmin"
```

## Sysadmin-Zugriff

Benutzer mit der Keycloak Realm-Rolle `AIHubSysAdmin` erhalten impliziten Admin-Zugriff auf jeden Mandanten und jede
Ressource. Die oben beschriebene zweistufige Mandanten-/Benutzerprüfung wird umgangen – ein Sysadmin wird überall als
Admin behandelt.

Sysadmins können auch ohne Mandantenkontext agieren, was mandantenübergreifende Endpunkte wie die
Mandantenverwaltungs-UI ermöglicht. Jeder Sysadmin ist ein echter Keycloak-Benutzer mit einer echten Benutzer-ID, sodass
seine Aktionen in Langfuse nachvollziehbar bleiben und sie in Mandanten-Mitgliederlisten wie jeder andere Benutzer
erscheinen.

Weisen Sie die Keycloak Realm-Rolle `AIHubSysAdmin` direkt oder über Identity Provider Mapper zu. Die Plattform legt
auch ein dediziertes Superuser-Konto aus `SUPERUSER_EMAIL` / `SUPERUSER_PASSWORD` an (der Benutzername wird gleich
`SUPERUSER_EMAIL` gesetzt, sodass sich dieses Konto mit seiner E-Mail-Adresse anmeldet) und materialisiert
`SUPERUSER_TOKEN` als Bearer-Token für diesen Benutzer, damit interne Services die API ohne Browsersitzung aufrufen
können.

Sparsam verwenden – der Sysadmin-Zugriff dient der Plattformadministration, nicht dem Tagesgeschäft.

## Validierungsregeln

::: warning Anforderungen an das Format von Zugriffsregeln
Beim Erstellen von Zugriffsregeln:

**Erforderliches Format**:

- Muss mit `aihub.user.` oder `aihub.admin.` beginnen
- Nur Kleinbuchstaben, Zahlen, Punkte, Bindestriche, Unterstriche, `*`, `>`
- Mehr-Ebenen-Platzhalter `>` nur am Ende

**Verboten**:

- Grossbuchstaben
- Sonderzeichen ausser `.`, `-`, `_`, `*`, `>`
- `>` in der Mitte einer Regel

Das System validiert Regeln beim Erstellen oder Bearbeiten von Mandanten und Rollen. Ungültige Regeln lösen einen Fehler
mit dem spezifischen Problem aus.
:::

## Häufige Muster

### Umfassender Plattformzugriff

```
aihub.admin.>
```

Voller Admin-Zugriff auf alles. Verwendung für Sysadmin-Mandanten.

### Service-Administratoren

```
aihub.admin.service.user
aihub.admin.service.role
aihub.admin.service.tenant
```

Kann Benutzer, Rollen und Mandanten verwalten, aber keine anderen Services.

### Abteilungszugriff

```
aihub.user.agent.department-finance.*
aihub.user.knowledge.finance-docs.>
aihub.user.process.finance-workflows.*
```

Nur Zugriff auf finanzspezifische Ressourcen.

### Schreibgeschützter Zugriff

```
aihub.user.agent.>
aihub.user.knowledge.>
```

Kann Agents und Wissen anzeigen und nutzen, aber nicht erstellen oder ändern.

### Power-User

```
aihub.user.>
aihub.admin.agent.<department>.*
aihub.admin.knowledge.<department>-docs.>
```

Benutzerzugriff überall, Admin-Zugriff nur auf Abteilungsressourcen.

## Fehlerbehebung bei Zugriffsproblemen

::: details Checkliste zur Fehlerbehebung
Bei der Fehlerbehebung überprüfen Sie diese Punkte in der angegebenen Reihenfolge:

1. **Mandantenauswahl**: Verifizieren Sie, dass der Benutzer den beabsichtigten Mandanten ausgewählt hat
2. **Mandantengrenze**: Bestätigen Sie, dass die Zugriffsregeln des Mandanten die Ressource enthalten
3. **Benutzerzugehörigkeit**: Verifizieren Sie, dass der Benutzer zum Mandanten gehört
4. **Rollenzuweisung**: Prüfen Sie, ob der Benutzer Rollen in diesem Mandanten hat
5. **Rollenregeln**: Überprüfen Sie, was diese Rollen erlauben
6. **Service-Zugriff**: Verifizieren Sie, dass die Berechtigung auf Service-Ebene existiert

Die Plattform gibt detaillierte Fehlermeldungen zurück, die angeben, welche Berechtigung fehlgeschlagen ist. Verwenden
Sie diese, um die fehlende Regel zu identifizieren.
:::

## Hinweise zur Performance

Die Zugriffsprüfung ist optimiert:

- Regeln werden einmal pro Anfrage kompiliert
- Mehrere Berechtigungsprüfungen für denselben Benutzer verwenden die kompilierten Regeln wieder
- Komplexe Platzhaltermuster haben minimale Performance-Auswirkungen
- Rollenänderungen treten sofort ohne Cache-Verzögerungen in Kraft

Das Wechseln von Mandanten löst eine vollständige Cache-Invalidierung im Frontend aus, was dazu führt, dass Daten neu
abgerufen werden.
