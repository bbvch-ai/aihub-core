---
title: Benutzer und Rollen verwalten
source_sha: e917a83dd1d4481ba4179e4927cd0dd4fe83591e90a7ff8ee244eba3fc2e287b
---

# Benutzer und Rollen verwalten

Benutzer greifen über Ihren Identitätsanbieter (Azure AD, Google Workspace, Okta usw.) auf die Plattform zu, aber ihre
Rollen und Mandantenmitgliedschaften werden innerhalb der Plattform selbst verwaltet.

## Benutzerlebenszyklus

### Erstanmeldung

::: info Authentifizierung vs. Autorisierung
Wenn sich jemand zum ersten Mal anmeldet:

1. Ihr Identitätsanbieter überprüft deren Identität
2. Die Plattform erstellt ihr Benutzerprofil (Name, E-Mail, Profilbild)
3. Sie treten automatisch dem Standardmandanten mit Standardbenutzerrollen bei
4. Sie sehen die Agents und Ressourcen des Standardmandanten

**Wichtig**: Die Plattform importiert keine Rollen von Ihrem Identitätsanbieter. Sie importiert nur
Identitätsinformationen (wer Sie sind, nicht was Sie tun können).
:::

### Hinzufügen zu weiteren Mandanten

Nach der Erstanmeldung eines Benutzers können Administratoren ihn zu weiteren Mandanten hinzufügen. Navigieren Sie zu
**Service** → **Tenants**, wählen Sie einen Mandanten aus und klicken Sie auf der Registerkarte „Users“ auf **Add
User**.

Suchen Sie den Benutzer nach Namen oder E-Mail. Wählen Sie aus, welche Rollen in diesem Mandanten zugewiesen werden
sollen. Der Benutzer kann nun zu diesem Mandanten wechseln und hat die durch diese Rollen definierten Berechtigungen.

Benutzer müssen sich nicht ab- und wieder anmelden. Änderungen treten bei ihrer nächsten Anfrage in Kraft.

### Entfernen aus Mandanten

Klicken Sie neben einem Benutzer in der Benutzerliste des Mandanten auf **Remove**. Dadurch wird dessen Mitgliedschaft
vollständig entfernt – er verliert alle Rollen in diesem Mandanten und kann ihn nicht mehr auswählen.

Das Entfernen eines Benutzers aus dem Standardmandanten ist ungewöhnlich, aber erlaubt. Benutzer, die aus allen
Mandanten entfernt wurden, können auf keine Plattformressourcen mehr zugreifen.

## Rollen

Rollen sind Sammlungen von Berechtigungen, die auf einen bestimmten Mandanten beschränkt sind. Die Rolle „Manager“ im
Finanz-Mandanten ist vollständig getrennt von einer „Manager“-Rolle im HR-Mandanten.

### Rollen erstellen

Navigieren Sie zur Registerkarte „**Roles**“ eines Mandanten und klicken Sie auf **Create Role**.

Wählen Sie einen aussagekräftigen Namen: „Agent User“, „Document Reviewer“, „Department Admin“. Der Name sollte
erklären, was die Rolle erlaubt.

Definieren Sie, was diese Rolle erlaubt. Für eine Abteilungsbenutzerrolle:

- Zugriff auf Abteilungs-Agents
- Zugriff auf Abteilungsprozesse
- Kann keine administrativen Services sehen
- Kann keine Ressourcen anderer Abteilungen sehen

Für eine Abteilungs-Admin-Rolle:

- Alles, was Abteilungsbenutzer tun können
- Agenteninstanzen erstellen
- Wissensaufnahme verwalten
- Benutzer zum Abteilungs-Mandanten hinzufügen
- Rollen an Abteilungsbenutzer zuweisen

### Rollenumfang innerhalb der Mandantengrenzen

Rollen erteilen Berechtigungen bis zur Grenze des Mandanten. Wenn der Mandant nur auf Finanz-Agents zugreifen kann, kann
eine Rolle in diesem Mandanten keinen Zugriff auf HR-Agents gewähren, selbst wenn dies konfiguriert ist.

Der Mandant definiert, was existiert. Rollen definieren, was Benutzer mit dieser Rolle innerhalb des Bestehenden tun
können.

### Rollen ändern

Wählen Sie eine Rolle aus und klicken Sie auf **Edit**. Änderungen wirken sich sofort auf alle Benutzer mit dieser Rolle
aus.

Das Hinzufügen von Berechtigungen zu einer Rolle gewährt diese Berechtigungen jedem, der sie besitzt. Das Entfernen von
Berechtigungen entzieht sie jedem mit dieser Rolle.

Testen Sie Rollenänderungen sorgfältig, vorzugsweise zuerst in einem Test-Mandanten.

## Benutzerrollen verwalten

Klicken Sie neben einem Benutzer in der Benutzerliste des Mandanten auf **Manage Roles**.

Fügen Sie Rollen hinzu, indem Sie aus den verfügbaren Rollen in diesem Mandanten auswählen. Entfernen Sie Rollen, indem
Sie die Auswahl aufheben.

Benutzer können mehrere Rollen im selben Mandanten haben. Ihre effektiven Berechtigungen sind die Vereinigung all ihrer
Rollen. Wenn eine Rolle Zugriff auf Agents gewährt und eine andere Zugriff auf Prozesse, können sie auf beides
zugreifen.

Ein Benutzer ohne Rollen in einem Mandanten ist technisch erlaubt, erfüllt aber keinen Zweck.

## Massenoperationen

### CSV-Import

::: details CSV-Importformat
Importieren Sie viele Benutzer gleichzeitig über **Service** → **Users** → **Import Users**.

Erstellen Sie eine CSV-Datei mit drei Spalten:

- email
- name
- initial_roles (durch Kommas getrennte Rollennamen)

Beispiel:

```csv
email,name,initial_roles
john.doe@company.com,John Doe,"StandardUser,AgentUser"
jane.smith@company.com,Jane Smith,StandardUser
```

Der Import:

- Erstellt Benutzerprofile, falls sie noch nicht existieren
- Fügt Benutzer Ihrem aktuellen Mandanten hinzu (bestimmt durch den Mandanten, in dem Sie sich befinden)
- Weist die angegebenen Rollen zu

Benutzer, die sich noch nicht angemeldet haben, erhalten Platzhalterprofile, die bei der ersten Authentifizierung
aktualisiert werden.
:::

### Massen-Rollenzuweisung

Wählen Sie mehrere Benutzer über Kontrollkästchen in der Benutzerliste aus. Wählen Sie **Bulk Actions** → **Assign
Roles**.

Drei Modi:

- **Hinzufügen**: Ausgewählte Rollen zu den bestehenden Rollen der Benutzer hinzufügen
- **Entfernen**: Ausgewählte Rollen entfernen, andere beibehalten
- **Ersetzen**: Alle Rollen durch ausgewählte Rollen ersetzen

Änderungen werden sofort auf alle ausgewählten Benutzer angewendet.

## Mandantenübergreifende Mitgliedschaft

Benutzer gehören oft mehreren Mandanten an und haben in jedem unterschiedliche Rollen.

Jemand könnte sein:

- Admin im Development-Mandanten (kann frei deployen und konfigurieren)
- Standardbenutzer im Staging-Mandanten (kann testen, aber nicht ändern)
- Viewer im Production-Mandanten (nur Lesezugriff)

Sie wechseln zwischen Mandanten mithilfe der Auswahlleiste oben. Die Oberfläche zeigt nur das an, was im ausgewählten
Mandanten verfügbar ist. Ihre Berechtigungen ändern sich basierend auf ihren Rollen in diesem Mandanten.

## Berechtigungsvererbung

Berechtigungen werden nicht zwischen Mandanten vererbt. Administrator in einem Mandanten zu sein, gewährt keine
Privilegien in einem anderen Mandanten.

Berechtigungen werden nicht innerhalb von Rollenhierarchien vererbt. Benutzerzugriff zu haben, gewährt nicht automatisch
Administratorzugriff.

## Häufige Rollenstrukturen

### Abteilungs-Mandant

- **Standardbenutzer**: Mit Abteilungs-Agents chatten, an Prozessen teilnehmen, Ergebnisse anzeigen
- **Power-User**: Standardbenutzer-Fähigkeiten plus Agenteninstanzen erstellen, Agents konfigurieren, Evaluierungen
  durchführen
- **Abteilungs-Admin**: Power-User-Fähigkeiten plus Benutzer verwalten, Rollen zuweisen, abteilungsspezifische Rollen
  erstellen

### Management-Mandant

- **Mandanten-Manager**: Neue Mandanten erstellen, Mandantengrenzen konfigurieren, Agents Mandanten zuweisen
- **Benutzeradministrator**: Benutzer zu Mandanten hinzufügen, Rollen zuweisen, Benutzerzugriff über alle Mandanten
  hinweg verwalten
- **Plattformadministrator**: Voller administrativer Zugriff auf alle Services und Konfigurationen

### Entwicklungs-Mandant

- **Entwickler**: Agents deployen, Pipelines erstellen, Konfigurationen ändern, voller Servicezugriff zum Testen
- **QA**: Test-Agenteninstanzen erstellen, Evaluierungen durchführen, alle Agents anzeigen, kann keinen Code deployen
- **Beobachter**: Nur Lesezugriff auf alle Ressourcen zum Lernen und zur Dokumentation

## Best Practices

::: tip Best Practices für die Benutzerverwaltung
**Prinzip der geringsten Berechtigung**: Gewähren Sie Benutzern die minimalen Berechtigungen, die für ihre Arbeit
erforderlich sind. Sie können den Zugriff später jederzeit erweitern.

**Regelmäßige Audits**: Überprüfen Sie Benutzerrollen vierteljährlich. Positionen ändern sich. Ein für ein Projekt
gewährter Zugriff ist möglicherweise sechs Monate später nicht mehr angemessen.

**Klare Rollennamen**: „Finance Standard User“ ist klarer als „FSU“. Zukünftige Administratoren werden es Ihnen danken.

**Vor der Einführung testen**: Erstellen Sie einen Testbenutzer, fügen Sie ihn einem Mandanten mit einer neuen Rolle
hinzu und überprüfen Sie, ob er genau das sieht, was Sie beabsichtigen.

**Zweck der Rollen dokumentieren**: Dokumentieren Sie beim Erstellen einer Rolle, warum sie existiert und welche
Verantwortlichkeiten sie hat. Dies verhindert Verwirrung bei der späteren Überprüfung des Zugriffs.

**Administratorrollen begrenzen**: Administratorbenutzer können sich selbst jede Berechtigung innerhalb ihres Mandanten
erteilen. Nur vertrauenswürdiges Personal sollte Administratorrollen haben.
:::

## Fehlerbehebung bei Zugriffsproblemen

Wenn ein Benutzer meldet, dass er auf etwas nicht zugreifen kann:

1. Überprüfen Sie, ob der richtige Mandant ausgewählt wurde (überprüfen Sie die Mandantenauswahl in der oberen Leiste)
2. Überprüfen Sie, ob ihr Mandant Zugriff auf diese Ressource hat
3. Überprüfen Sie, ob ihnen Rollen in diesem Mandanten zugewiesen sind
4. Überprüfen Sie, welche Berechtigungen diese Rollen gewähren

Das häufigste Problem ist, dass Benutzer im falschen Mandanten arbeiten. Das zweithäufigste Problem ist, dass die
Mandantengrenze den Zugriff verhindert, obwohl die Rolle ihn erlauben würde.
