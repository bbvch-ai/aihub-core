---
title: Mandanten einrichten
source_sha: "0f190b057f573e9ee0cf8f9ec8360cc5b39c083632ef9b5e7fd345ade8eab3d9"
---

# Mandanten einrichten

Das Erstellen von Mandanten erfordert die Planung Ihrer Organisationsstruktur und das Verständnis dessen, was jede Benutzergruppe tun können soll. Dieses Kapitel erläutert praktische Ansätze für das Mandantendesign.

## Ihre Mandantenstruktur planen

Beginnen Sie damit, die Gruppen zu identifizieren, die getrennte Arbeitsbereiche benötigen. Gängige Muster:

**Organisationshierarchie**: Systemadministratoren, Manager und Abteilungen erhalten jeweils einen eigenen Mandanten. Dies trennt technische Operationen von der Geschäftsadministration und der täglichen Arbeit.

**Geschäftsbereiche**: Marketing, Vertrieb, Entwicklung, Operations erhalten jeweils einen Mandanten. Sie teilen sich einige Ressourcen (unternehmensweite Agents), haben aber bereichsspezifische Agents.

**Kundenisolation**: Jeder Kunde erhält einen eigenen Mandanten. Nützlich für Serviceprovider oder SaaS-Deployments, bei denen Kunden niemals die Daten oder Agents anderer Kunden sehen dürfen.

**Umgebungstrennung**: Entwicklung, Staging und Produktion laufen als separate Mandanten. Entwickler können im Entwicklungs-Mandanten experimentieren, ohne die Produktionsbenutzer zu beeinträchtigen.

**Compliance-Grenzen**: Gesetzliche Anforderungen können eine Trennung zwischen Entitäten, geografischen Regionen oder Datenklassifikationen vorschreiben. Jede regulierte Grenze wird zu einem Mandanten.

## Das Drei-Ebenen-Muster

Die meisten Deployments profitieren von drei Mandanten-Ebenen:

```mermaid
graph TD
    T1[Level 1: Sysadmin Tenant]
    T2[Level 2: Management Tenant]
    T3A[Level 3: Finance Tenant]
    T3B[Level 3: HR Tenant]
    T3C[Level 3: Legal Tenant]

    T1 -->|creates & deploys| Agents[Agent Classes]
    T1 -->|configures| Pipelines[Data Pipelines]
    T2 -->|creates instances| AgentInst[Agent Instances]
    T2 -->|creates & manages| T3A
    T2 -->|creates & manages| T3B
    T2 -->|creates & manages| T3C
    AgentInst -->|assigned to| T3A
    AgentInst -->|assigned to| T3B
    AgentInst -->|assigned to| T3C

    style T1 fill:#ffebee
    style T2 fill:#fff3e0
    style T3A fill:#e8f5e9
    style T3B fill:#e8f5e9
    style T3C fill:#e8f5e9
```

### Ebene 1: Systemadministration

Erstellen Sie einen Mandanten für Personen, die die Plattforminfrastruktur warten. Diese Benutzer:

- Deployen Agent- und Prozesscode auf die Plattform
- Konfigurieren Daten-Pipelines für das Einlesen von Dokumenten
- Verwalten Plattform-Services und Monitoring
- Haben vollen Zugriff auf alle Plattformfunktionen

Dies sind typischerweise 2-5 Personen: Ihr DevOps-Team, leitende Entwickler oder IT-Mitarbeiter, die für die Plattform verantwortlich sind.

### Ebene 2: Geschäftsadministration

Erstellen Sie einen Mandanten für Personen, die die Plattform für Geschäftsbenutzer administrieren. Diese Benutzer:

- Erstellen und konfigurieren neue Mandanten
- Fügen Benutzer zu Mandanten hinzu und weisen Rollen zu
- Erstellen Agent-Instanzen aus deployten Klassen
- Überwachen die Agent-Performance und führen Evaluierungen durch
- Verwalten Wissensdatenbanken (Ingestionsstatus anzeigen, Probleme beheben)

Dies sind Business-Analysten, Projektmanager oder Abteilungsleiter, die die Anforderungen der Organisation verstehen, aber keinen Code schreiben.

### Ebene 3: Endbenutzer

Erstellen Sie Mandanten für Personen, die Agents verwenden, um Aufgaben zu erledigen. Diese Benutzer:

- Chatten mit Agents, die für ihre Rolle relevant sind
- Nehmen an Prozessen teil, die ihre Abteilung betreffen
- Können keine administrativen Oberflächen sehen oder Agent-Instanzen erstellen

Dies sind alle anderen in Ihrer Organisation.

## Einen Mandanten erstellen

Navigieren Sie in der Admin-Oberfläche zu **Service** → **Mandanten**. Sie müssen sich in einem Mandanten befinden, der administrativen Zugriff auf den Mandanten-Service hat.

Klicken Sie auf **Mandanten erstellen**. Sie benötigen drei Informationen:

**Name**: Wählen Sie etwas Klares und Beschreibendes. "Finanzabteilung", "Kunde - Acme Corp", "Produktionsumgebung". Benutzer sehen diesen Namen, wenn sie auswählen, in welchem Mandanten sie arbeiten möchten.

**Beschreibung**: Erläutern Sie, wofür dieser Mandant gedacht ist. "Benutzer der Finanzabteilung – Zugriff auf Finanzberichts-Agents und Abteilungsrichtlinien." Dies hilft aktuellen und zukünftigen Administratoren, den Zweck des Mandanten zu verstehen.

**Scope**: Definieren Sie, auf welche Ressourcen dieser Mandant zugreifen kann. Für das Drei-Ebenen-Muster:

- Sysadmin-Ebene: Voller Plattformzugriff
- Management-Ebene: Administrative Services, aber keine Deployment-Fähigkeiten
- Endbenutzer-Ebene: Spezifische Agents und Prozesse, keine Services

## Mandanten-Scope definieren

Der Scope des Mandanten bestimmt den maximalen Zugriff, den jeder in diesem Mandanten haben kann. Stellen Sie sich das als eine Grenze um Ressourcen vor.

Für einen Mandanten der Finanzabteilung könnten Sie den Scope folgendermaßen festlegen:

- Finanzbezogene Agents (Berichts-Agents, Richtlinien-Agents, Genehmigungs-Workflows)
- Finanz-Wissensdatenbanken (für Manager, die Ingestionsprobleme beheben)
- Spezifische Prozesse (Budgetgenehmigungs-Workflow, Spesenabrechnung)

Ein Benutzer im Finanz-Mandanten kann nicht auf HR-Agents zugreifen, selbst wenn Sie ihm eine Administratorrolle innerhalb des Finanz-Mandanten geben. Die Mandantengrenze verhindert dies.

### Breit anfangen vs. eng anfangen

Sie haben zwei Ansätze:

**Breiter Scope**: Geben Sie dem Mandanten anfänglich Zugriff auf alles. Benutzer können alle Agents, alle Services, alle Prozesse sehen. Wenn Sie lernen, was sie tatsächlich benötigen, schränken Sie den Scope ein, indem Sie den Zugriff auf ungenutzte Ressourcen entfernen.

**Enger Scope**: Geben Sie dem Mandanten nur Zugriff auf spezifische Ressourcen. Wenn Benutzer weitere Funktionen anfordern, erweitern Sie den Scope schrittweise.

Ein breiter Scope ist anfänglich einfacher, erfordert aber später mehr Bereinigung. Ein enger Scope ist sicherer, aber Benutzer werden Zugriff anfordern, wenn sie Bedürfnisse entdecken.

Für Endbenutzer-Mandanten (Abteilungen, Kunden) beginnen Sie eng. Diese Benutzer benötigen keine breite Sichtbarkeit – sie benötigen spezifische Tools. Für Management-Mandanten beginnen Sie breit, da diese Benutzer Flexibilität zur Administration der Plattform benötigen.

## Rollen innerhalb von Mandanten konfigurieren

Nachdem Sie den Mandanten erstellt haben, konfigurieren Sie Rollen, die Benutzer in diesem Mandanten haben können. Rollen definieren, was Benutzer innerhalb der Mandantengrenzen tun können.

Für einen Abteilungs-Mandanten könnten Sie erstellen:

**Standardbenutzer**: Kann mit Abteilungs-Agents chatten, an Prozessen teilnehmen, aber nichts erstellen oder ändern.

**Teamleiter**: Kann Agent-Instanzen erstellen, Agents für sein Team konfigurieren, Evaluationsergebnisse anzeigen, aber keine Benutzer verwalten oder Mandanteneinstellungen ändern.

**Abteilungsadministrator**: Volle Kontrolle innerhalb des Abteilungs-Mandanten – kann Benutzer hinzufügen, Rollen zuweisen, Agents erstellen und alle Abteilungsressourcen verwalten.

Diese Rollen gelten nur innerhalb dieses Mandanten. Ein Benutzer, der im Finanz-Mandanten „Abteilungsadministrator“ ist, hat im HR-Mandanten keine Berechtigungen, es sei denn, diese wurden explizit erteilt.

## Benutzer zu Mandanten hinzufügen

Nachdem Sie Rollen erstellt haben, fügen Sie Benutzer zum Mandanten hinzu und weisen ihnen Rollen zu.

Suchen Sie Benutzer nach E-Mail oder Namen. Wenn ein Benutzer noch nicht existiert (er hat sich noch nicht angemeldet), können Sie ihn trotzdem hinzufügen. Sein Profil wird erstellt, wenn er sich zum ersten Mal über Ihren Identitätsanbieter authentifiziert.

Benutzer können mehreren Mandanten angehören. Jemand könnte sein:

- Standardbenutzer in ihrem Abteilungs-Mandanten
- Teamleiter in einem mandantenübergreifenden Projekt-Mandanten
- Administrator in einem Test-Mandanten zum Ausprobieren neuer Funktionen

## Standardverhalten des Mandanten

Wenn sich jemand zum ersten Mal anmeldet, tritt er automatisch dem Standard-Mandanten mit Standardbenutzerrollen bei. Konfigurieren Sie dieses Verhalten mit Umgebungsvariablen:

```bash
USER_SIGNUP_DEFAULT_TENANT="default"
USER_SIGNUP_DEFAULT_ROLES="AIHubUser"
FIRST_USER_SIGNUP_DEFAULT_ROLES="AIHubAdmin"
```

Die erste Person, die sich anmeldet, erhält Administratorrollen, um sicherzustellen, dass jemand die Plattform sofort administrieren kann. Nachfolgende Benutzer erhalten Standardrollen.

Diese automatische Zuweisung erfolgt nur einmal pro Benutzer. Danach fügen Sie sie bei Bedarf explizit zu anderen Mandanten hinzu.

## Gängige Konfigurationen

### Einzelnes Unternehmen mit Abteilungen

Sysadmin-Mandant → Management-Mandant → Ein Mandant pro Abteilung

Manager erstellen Abteilungs-Mandanten und konfigurieren, auf welche Agents jede Abteilung zugreifen kann. Abteilungsbenutzer sehen nur die Ressourcen ihrer Abteilung.

### Multi-Kunden-SaaS

Sysadmin-Mandant → Management-Mandant → Ein Mandant pro Kunde

Jeder Kunden-Mandant ist isoliert. Kunden können die Agents oder Daten anderer Kunden nicht sehen. Manager onboarden neue Kunden, indem sie einen Mandanten erstellen, relevante Agents konfigurieren und die Benutzer dieses Kunden hinzufügen.

### Beratungsunternehmen

Sysadmin-Mandant → Management-Mandant → Ein Mandant pro Kundenprojekt

Projekt-Mandanten geben Beratern Zugriff auf kundenspezifische Agents und Wissen. Wenn ein Projekt endet, archivieren Sie den Mandanten. Wenn ein Berater einem neuen Projekt beitritt, fügen Sie ihn dem Mandanten dieses Projekts hinzu.

### Entwicklungs-Workflow

Sysadmin-Mandant → Dev-Mandant → Staging-Mandant → Produktions-Mandant

Entwickler arbeiten im Entwicklungs-Mandanten mit gelockerten Kontrollen. Der Staging-Mandant spiegelt die Produktion zum Testen wider. Der Produktions-Mandant hat strenge Zugriffskontrollen. Dieselben Agents, derselbe Code, unterschiedliche Mandanten für unterschiedliche Zwecke.

## Mandanten-Lebenszyklus

Mandanten bleiben bestehen, bis sie explizit gelöscht werden. Sie können:

**Einen Mandanten archivieren**: Alle Benutzer entfernen, aber den Mandanten und seine Rollen behalten. Nützlich für abgeschlossene Projekte oder inaktive Kunden. Niemand kann darauf zugreifen, aber die Konfiguration bleibt erhalten, falls Sie ihn reaktivieren müssen.

**Einen Mandanten löschen**: Den Mandanten, alle seine Rollen und alle Benutzerzuordnungen entfernen. Permanent. Nur möglich, nachdem zuerst alle Benutzer entfernt wurden.

::: warning Schutz des Standard-Mandanten
Der Standard-Mandant kann nicht gelöscht werden. Dies stellt sicher, dass die Plattform immer mindestens einen funktionierenden Mandanten hat.
:::

## Praktische Tipps

::: tip Best Practices **Dokumentieren Sie Ihre Entscheidungen**: Halten Sie schriftlich fest, warum Sie jeden Mandanten erstellt haben und wie sein Scope sein sollte. Sechs Monate später, wenn sich Rollen geändert haben, verhindert diese Dokumentation Verwirrung.

**Einfach beginnen**: Ein Management-Mandant und ein Endbenutzer-Mandant funktionieren für viele Organisationen. Fügen Sie Komplexität nur dann hinzu, wenn Sie sie benötigen.

**Mit eingeschränkten Benutzern testen**: Erstellen Sie ein Testkonto, fügen Sie es einem neuen Mandanten hinzu und überprüfen Sie, was dieser Benutzer sehen kann. Nicht annehmen – überprüfen.

**Vierteljährlich überprüfen**: Personen wechseln Rollen. Projekte enden. Neue Abteilungen entstehen. Ihre Mandantenstruktur sollte sich mit Ihrer Organisation entwickeln.

**Wachstum planen**: "Kunde 1" funktioniert, wenn Sie drei Kunden haben. "Kunde - Acme Corp" funktioniert, wenn Sie dreihundert haben.
:::
