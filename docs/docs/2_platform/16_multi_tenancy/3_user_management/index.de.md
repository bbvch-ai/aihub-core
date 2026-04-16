---
title: Benutzer und Rollen verwalten
source_sha: fe3d8314b3fd0d0e11968bc40f4bcb72c64732f1a20b876c6360b139271f75ce
---

# Benutzer und Rollen verwalten

Benutzer greifen über Ihren Identitätsanbieter (Azure AD, Google Workspace, Okta, etc.) auf die Plattform zu, aber ihre
Rollen und Mandantenmitgliedschaften werden innerhalb der Plattform selbst verwaltet.

## Benutzerlebenszyklus

### Erster Login

::: info Authentifizierung vs. Autorisierung
Wenn sich jemand zum ersten Mal anmeldet:

1. Ihr Identitätsanbieter überprüft, wer sie sind
2. Die Plattform liest ihre Identität (Name, E-Mail) von Keycloak – es wird kein lokaler Benutzerdatensatz erstellt
3. Sie treten automatisch dem Standard-Mandanten mit Standard-Benutzerrollen bei
4. Sie sehen die Agents und Ressourcen des Standard-Mandanten

**Wichtig**: Die Plattform importiert keine Rollen von Ihrem Identitätsanbieter. Sie importiert nur
Identitätsinformationen (wer Sie sind, nicht was Sie tun können).
:::

### Hinzufügen zu weiteren Mandanten

Nach dem ersten Login eines Benutzers können Administratoren diese zu anderen Mandanten hinzufügen. Navigieren Sie zu
**Service** → **Mandanten**, wählen Sie einen Mandanten aus und klicken Sie auf der Registerkarte „Benutzer“ auf
**Benutzer hinzufügen**.

Suchen Sie den Benutzer nach Namen oder E-Mail. Wählen Sie aus, welche Rollen in diesem Mandanten zugewiesen werden
sollen. Der Benutzer kann nun zu diesem Mandanten wechseln und hat die durch diese Rollen definierten Berechtigungen.

Benutzer müssen sich nicht ab- und wieder anmelden. Änderungen treten bei ihrer nächsten Anfrage in Kraft.

### Aus Mandanten entfernen

Klicken Sie auf **Entfernen** neben einem Benutzer in der Benutzerliste des Mandanten. Dies entfernt ihre Mitgliedschaft
vollständig – sie verlieren alle Rollen in diesem Mandanten und können ihn nicht mehr auswählen.

Das Entfernen eines Benutzers aus dem Standard-Mandanten ist ungewöhnlich, aber erlaubt. Benutzer, die aus allen
Mandanten entfernt wurden, können auf keine Plattformressourcen zugreifen.

## Rollen

Rollen sind Sammlungen von Berechtigungen, die auf einen bestimmten Mandanten zugeschnitten sind. Die Rolle „Manager“ im
Finanz-Mandanten ist vollständig getrennt von einer Rolle „Manager“ im HR-Mandanten.

### Rollen erstellen

Navigieren Sie zur Registerkarte „Rollen“ eines Mandanten und klicken Sie auf **Rolle erstellen**.

Wählen Sie einen beschreibenden Namen: „Agent-Benutzer“, „Dokumentenprüfer“, „Abteilungsadministrator“. Der Name sollte
erklären, was die Rolle erlaubt.

Definieren Sie, was diese Rolle erlaubt. Für eine Abteilungsbenutzerrolle:

- Zugriff auf Abteilungs-Agents
- Zugriff auf Abteilungs-Workflows
- Kann administrative Services nicht sehen
- Kann Ressourcen anderer Abteilungen nicht sehen

Für eine Abteilungsadministratorrolle:

- Alles, was Abteilungsbenutzer tun können
- Agent-Instanzen erstellen
- Wissensaufnahme verwalten
- Benutzer zum Abteilungs-Mandanten hinzufügen
- Rollen an Abteilungsbenutzer zuweisen

### Rollenbereich innerhalb der Mandantengrenzen

Rollen gewähren Berechtigungen bis zur Grenze des Mandanten. Wenn der Mandant nur auf Finanz-Agents zugreifen kann, kann
eine Rolle in diesem Mandanten keinen Zugriff auf HR-Agents gewähren, selbst wenn dies konfiguriert wäre.

Der Mandant definiert, was existiert. Rollen definieren, was Benutzer mit dieser Rolle innerhalb des Existierenden tun
können.

### Rollen ändern

Wählen Sie eine Rolle aus und klicken Sie auf **Bearbeiten**. Änderungen wirken sich sofort auf alle Benutzer mit dieser
Rolle aus.

Das Hinzufügen von Berechtigungen zu einer Rolle gewährt diese Berechtigungen jedem, der sie besitzt. Das Entfernen von
Berechtigungen entzieht sie jedem, der diese Rolle besitzt.

Testen Sie Rollenänderungen sorgfältig, vorzugsweise zuerst in einem Test-Mandanten.

## Benutzerrollen verwalten

Klicken Sie auf **Rollen verwalten** neben einem Benutzer in der Benutzerliste des Mandanten.

Fügen Sie Rollen hinzu, indem Sie aus den verfügbaren Rollen in diesem Mandanten auswählen. Entfernen Sie Rollen, indem
Sie sie abwählen.

Benutzer können mehrere Rollen im selben Mandanten haben. Ihre effektiven Berechtigungen sind die Vereinigung all ihrer
Rollen. Wenn eine Rolle den Zugriff auf Agents und eine andere den Zugriff auf Workflows gewährt, können sie auf beides
zugreifen.

Ein Benutzer ohne Rollen in einem Mandanten ist technisch erlaubt, erfüllt aber keinen Zweck.

## Massenoperationen

### CSV-Import

::: details CSV-Importformat
Importieren Sie mehrere Benutzer gleichzeitig über **Service** → **Benutzer** → **Benutzer importieren**.

Erstellen Sie eine CSV-Datei mit drei Spalten:

- email
- name
- initial_roles (comma-separated role names)

Beispiel:

```csv
email,name,initial_roles
john.doe@company.com,John Doe,"StandardUser,AgentUser"
jane.smith@company.com,Jane Smith,StandardUser
```

Der Import:

- Erstellt Benutzerprofile, falls sie noch nicht existieren
- Fügt Benutzer zu Ihrem aktuellen Mandanten hinzu (bestimmt durch den Mandanten, in dem Sie sich befinden)
- Weist die angegebenen Rollen zu

Benutzer, die sich noch nicht angemeldet haben, erhalten Platzhalterprofile, die beim ersten Login aktualisiert werden.
:::

### Massenrollenzuweisung

Wählen Sie mehrere Benutzer über die Kontrollkästchen in der Benutzerliste aus. Wählen Sie **Massenaktionen** → **Rollen
zuweisen**.

Drei Modi:

- **Hinzufügen**: Fügen Sie ausgewählte Rollen zu den bestehenden Rollen der Benutzer hinzu
- **Entfernen**: Entfernen Sie ausgewählte Rollen, behalten Sie andere bei
- **Ersetzen**: Ersetzen Sie alle Rollen durch ausgewählte Rollen

Änderungen gelten sofort für alle ausgewählten Benutzer.

## Mandantenübergreifende Mitgliedschaft

Benutzer gehören oft mehreren Mandanten an, mit unterschiedlichen Rollen in jedem.

Jemand könnte sein:

- Admin im Entwicklungs-Mandanten (kann frei deployen und konfigurieren)
- Standardbenutzer im Staging-Mandanten (kann testen, aber nicht ändern)
- Betrachter im Produktions-Mandanten (schreibgeschützter Zugriff)

Sie wechseln zwischen den Mandanten über die Auswahlleiste oben. Die Benutzeroberfläche zeigt nur das an, was im
ausgewählten Mandanten verfügbar ist. Ihre Berechtigungen ändern sich basierend auf ihren Rollen in diesem Mandanten.

## Vererbung von Berechtigungen

Berechtigungen werden nicht zwischen Mandanten vererbt. Ein Admin in einem Mandanten gewährt keine Privilegien in einem
anderen Mandanten.

Berechtigungen werden nicht innerhalb von Rollenhierarchien vererbt. Der Besitz von Benutzerzugriff gewährt nicht
automatisch Admin-Zugriff.

## Gängige Rollenstrukturen

### Abteilungs-Mandant

**Standardbenutzer**: Mit Abteilungs-Agents chatten, an Workflows teilnehmen, Ergebnisse anzeigen

**Power User**: Fähigkeiten des Standardbenutzers plus Agent-Instanzen erstellen, Agents konfigurieren, Evaluierungen
durchführen

**Abteilungsadministrator**: Fähigkeiten des Power Users plus Benutzer verwalten, Rollen zuweisen, abteilungsspezifische
Rollen erstellen

### Management-Mandant

**Mandanten-Manager**: Neue Mandanten erstellen, Mandantengrenzen konfigurieren, Agents Mandanten zuweisen

**Benutzeradministrator**: Benutzer zu Mandanten hinzufügen, Rollen zuweisen, Benutzerzugriff über alle Mandanten hinweg
verwalten

**Plattform-Administrator**: Voller administrativer Zugriff auf alle Services und Konfigurationen

### Entwicklungs-Mandant

**Entwickler**: Agents deployen, Pipelines erstellen, Konfigurationen ändern, voller Service-Zugriff für Tests

**QA**: Test-Agent-Instanzen erstellen, Evaluierungen durchführen, alle Agents anzeigen, kann keinen Code deployen

**Beobachter**: Schreibgeschützter Zugriff auf alle Ressourcen zum Lernen und zur Dokumentation

## Best Practices

::: tip Best Practices für die Benutzerverwaltung
**Prinzip der geringsten Privilegien**: Gewähren Sie Benutzern nur die minimalen Berechtigungen, die sie für ihre Arbeit
benötigen. Sie können den Zugriff später jederzeit erweitern.

**Regelmäßige Audits**: Überprüfen Sie Benutzerrollen vierteljährlich. Personen wechseln Positionen. Ein für ein Projekt
gewährter Zugriff ist sechs Monate später möglicherweise nicht mehr angemessen.

**Klare Rollennamen**: „Finanz-Standardbenutzer“ ist klarer als „FSU“. Zukünftige Administratoren werden es Ihnen
danken.

**Vor der Bereitstellung testen**: Erstellen Sie einen Testbenutzer, fügen Sie ihn einem Mandanten mit einer neuen Rolle
hinzu und überprüfen Sie, ob er genau das sieht, was Sie beabsichtigen.

**Zwecke der Rollen dokumentieren**: Wenn Sie eine Rolle erstellen, dokumentieren Sie, warum sie existiert und welche
Verantwortlichkeiten sie hat. Dies verhindert Verwirrung bei der späteren Überprüfung des Zugriffs.

**Admin-Rollen begrenzen**: Admin-Benutzer können sich innerhalb ihres Mandanten jede Berechtigung selbst gewähren. Nur
vertrauenswürdiges Personal sollte Admin-Rollen besitzen.
:::

## Fehlerbehebung bei Zugriffsproblemen

Wenn ein Benutzer meldet, dass er auf etwas nicht zugreifen kann:

1. Überprüfen Sie, ob der richtige Mandant ausgewählt wurde (überprüfen Sie die Mandanten-Auswahlleiste oben)
2. Überprüfen Sie, ob ihr Mandant Zugriff auf diese Ressource hat
3. Überprüfen Sie, ob ihnen Rollen in diesem Mandanten zugewiesen sind
4. Überprüfen Sie, was diese Rollen erlauben

Das häufigste Problem ist, dass Benutzer im falschen Mandanten arbeiten. Das zweithäufigste Problem ist, dass die
Mandantengrenze den Zugriff verhindert, obwohl die Rolle ihn erlauben würde.
