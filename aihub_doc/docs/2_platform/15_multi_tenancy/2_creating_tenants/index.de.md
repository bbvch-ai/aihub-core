````markdown
---
title: Mandanten einrichten
source_sha: "f4d0827329dfb29df688f35743dcf26fd92bbf7615a7c1ad67db1609dd427ce6"
---

# Mandanten einrichten

Das Erstellen von Mandanten erfordert die Planung Ihrer Organisationsstruktur und das Verständnis, was jede Benutzergruppe tun können soll. Dieses Kapitel stellt praktische Ansätze für das Mandanten-Design vor.

## Planung Ihrer Mandantenstruktur

Beginnen Sie damit, die Gruppen zu identifizieren, die separate Arbeitsbereiche benötigen. Häufige Muster:

**Organisationshierarchie**: Systemadministratoren, Manager und Abteilungen erhalten jeweils einen eigenen Mandanten. Dies trennt technische Operationen von der Geschäftsverwaltung und dem täglichen Arbeitsablauf.

**Geschäftseinheiten**: Marketing, Vertrieb, Engineering und Betrieb erhalten jeweils einen Mandanten. Sie teilen sich einige Ressourcen (unternehmensweite Agents), verfügen aber über einheitsspezifische Agents.

**Kundenisolierung**: Jeder Kunde erhält einen eigenen Mandanten. Nützlich für Dienstleister oder SaaS-Implementierungen, bei denen Kunden niemals die Daten oder Agents anderer Kunden sehen dürfen.

**Umgebungstrennung**: Entwicklung, Staging und Produktion werden als separate Mandanten betrieben. Entwickler können im Entwicklungs-Mandanten experimentieren, ohne die Produktivnutzer zu beeinträchtigen.

**Compliance-Grenzen**: Gesetzliche Anforderungen können eine Trennung zwischen Entitäten, geografischen Regionen oder Datenklassifizierungen vorschreiben. Jede regulierte Grenze wird zu einem Mandanten.

## Das Drei-Ebenen-Muster

Die meisten Implementierungen profitieren von drei Ebenen von Mandanten:

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
````

### Ebene 1: Systemadministration

Erstellen Sie einen Mandanten für Personen, die die Plattforminfrastruktur warten. Diese Benutzer:

- Stellen Agenten- und Prozesscode auf der Plattform bereit
- Konfigurieren Datenpipelines für die Dokumentenerfassung
- Verwalten Plattformdienste und Überwachung
- Haben vollen Zugriff auf alle Plattformfunktionen

Dies sind typischerweise 2-5 Personen: Ihr DevOps-Team, leitende Entwickler oder IT-Mitarbeiter, die für die Plattform
verantwortlich sind.

### Ebene 2: Geschäftsadministration

Erstellen Sie einen Mandanten für Personen, die die Plattform für Geschäftsanwender verwalten. Diese Benutzer:

- Erstellen und konfigurieren neue Mandanten
- Fügen Benutzer zu Mandanten hinzu und weisen Rollen zu
- Erstellen Agenteninstanzen aus bereitgestellten Klassen
- Überwachen die Agentenleistung und führen Bewertungen durch
- Verwalten Wissensdatenbanken (Anzeigestatus der Erfassung, Fehlerbehebung)

Dies sind Business Analysts, Projektmanager oder Abteilungsleiter, die die Bedürfnisse der Organisation verstehen, aber
keinen Code schreiben.

### Ebene 3: Endbenutzer

Erstellen Sie Mandanten für Personen, die Agenten zur Erledigung von Aufgaben verwenden. Diese Benutzer:

- Chatten mit für ihre Rolle relevanten Agenten
- Nehmen an Prozessen teil, die ihre Abteilung betreffen
- Können keine administrativen Oberflächen sehen oder Agenteninstanzen erstellen

Dies ist jeder andere in Ihrer Organisation.

## Einen Mandanten erstellen

Navigieren Sie in der Admin-Oberfläche zu **Service** → **Tenants**. Sie müssen sich in einem Mandanten befinden, der
administrativen Zugriff auf den Mandantendienst hat.

Klicken Sie auf **Create Tenant**. Sie benötigen drei Informationen:

**Name**: Wählen Sie etwas Klares und Beschreibendes. „Finanzabteilung“, „Kunde - Acme Corp“, „Produktionsumgebung“.
Benutzer sehen diesen Namen, wenn sie auswählen, in welchem Mandanten sie arbeiten möchten.

**Beschreibung**: Erklären Sie, wofür dieser Mandant dient. „Benutzer der Finanzabteilung – Zugriff auf
Finanzberichterstattungs-Agenten und Abteilungsrichtlinien.“ Dies hilft aktuellen und zukünftigen Administratoren, den
Zweck des Mandanten zu verstehen.

**Geltungsbereich (Scope)**: Definieren Sie, auf welche Ressourcen dieser Mandant zugreifen kann. Für das
Drei-Ebenen-Muster:

- Sysadmin-Ebene: Voller Plattformzugriff
- Management-Ebene: Administrative Dienste, aber keine Bereitstellungsfunktionen
- Endbenutzer-Ebene: Spezifische Agenten und Prozesse, keine Dienste

## Mandanten-Geltungsbereich definieren

Der Geltungsbereich des Mandanten bestimmt den maximalen Zugriff, den jeder in diesem Mandanten haben kann. Stellen Sie
es sich wie das Ziehen einer Grenze um Ressourcen vor.

Für einen Mandanten der Finanzabteilung könnten Sie den Geltungsbereich festlegen auf:

- Finanzbezogene Agenten (Berichts-Agenten, Richtlinien-Agenten, Genehmigungs-Workflows)
- Finanz-Wissensdatenbanken (für Manager, die Probleme bei der Erfassung beheben)
- Spezifische Prozesse (Budgetgenehmigungs-Workflow, Spesenabrechnung)

Ein Benutzer im Finanz-Mandanten kann nicht auf HR-Agenten zugreifen, selbst wenn Sie ihm eine Administratorrolle
innerhalb des Finanz-Mandanten geben. Die Mandantengrenze verhindert dies.

### Breit anfangen vs. eng anfangen

Sie haben zwei Ansätze:

**Breiter Geltungsbereich**: Geben Sie dem Mandanten anfänglich Zugriff auf alles. Benutzer können alle Agenten, alle
Dienste, alle Prozesse sehen. Wenn Sie herausfinden, was sie tatsächlich benötigen, schränken Sie den Geltungsbereich
ein, indem Sie den Zugriff auf ungenutzte Ressourcen entfernen.

**Enger Geltungsbereich**: Geben Sie dem Mandanten nur Zugriff auf spezifische Ressourcen. Wenn Benutzer mehr Funktionen
anfordern, erweitern Sie den Geltungsbereich schrittweise.

Ein breiter Geltungsbereich ist anfänglich einfacher, erfordert aber später mehr Bereinigung. Ein enger Geltungsbereich
ist sicherer, aber Benutzer werden Zugriff anfordern, sobald sie Bedürfnisse entdecken.

Für Endbenutzer-Mandanten (Abteilungen, Kunden) beginnen Sie eng. Diese Benutzer benötigen keine breite Sichtbarkeit –
sie benötigen spezifische Tools. Für Management-Mandanten beginnen Sie breit, da diese Benutzer Flexibilität benötigen,
um die Plattform zu administrieren.

## Rollen innerhalb von Mandanten konfigurieren

Nachdem Sie den Mandanten erstellt haben, konfigurieren Sie Rollen, die Benutzer in diesem Mandanten haben können.
Rollen definieren, was Benutzer innerhalb der Grenzen des Mandanten tun können.

Für einen Abteilungs-Mandanten könnten Sie erstellen:

**Standardbenutzer**: Kann mit Abteilungs-Agenten chatten, an Prozessen teilnehmen, aber nichts erstellen oder ändern.

**Teamleiter**: Kann Agenteninstanzen erstellen, Agenten für sein Team konfigurieren, Bewertungsergebnisse einsehen,
aber keine Benutzer verwalten oder Mandanteneinstellungen ändern.

**Abteilungsadministrator**: Volle Kontrolle innerhalb des Abteilungs-Mandanten – kann Benutzer hinzufügen, Rollen
zuweisen, Agenten erstellen und alle Abteilungsressourcen verwalten.

Diese Rollen gelten nur innerhalb dieses Mandanten. Ein Benutzer, der in der Finanzabteilung „Abteilungsadministrator“
ist, hat keine Berechtigungen im HR-Mandanten, es sei denn, sie wurden explizit gewährt.

## Benutzer zu Mandanten hinzufügen

Nachdem Sie Rollen erstellt haben, fügen Sie Benutzer dem Mandanten hinzu und weisen ihnen Rollen zu.

Suchen Sie Benutzer nach E-Mail oder Name. Falls ein Benutzer noch nicht existiert (er hat sich noch nicht angemeldet),
können Sie ihn trotzdem hinzufügen. Sein Profil wird erstellt, wenn er sich zum ersten Mal über Ihren Identitätsanbieter
authentifiziert.

Benutzer können mehreren Mandanten angehören. Jemand könnte sein:

- Standardbenutzer in ihrem Abteilungs-Mandanten
- Teamleiter in einem funktionsübergreifenden Projekt-Mandanten
- Administrator in einem Test-Mandanten zum Ausprobieren neuer Funktionen

## Standardverhalten von Mandanten

Wenn sich jemand zum ersten Mal anmeldet, tritt er automatisch dem Standard-Mandanten mit Standard-Benutzerrollen bei.
Konfigurieren Sie dieses Verhalten mit Umgebungsvariablen:

```bash
USER_SIGNUP_DEFAULT_TENANT="default"
USER_SIGNUP_DEFAULT_ROLES="AIHubUser"
FIRST_USER_SIGNUP_DEFAULT_ROLES="AIHubAdmin"
```

Die erste Person, die sich anmeldet, erhält Administratorrollen, um sicherzustellen, dass jemand die Plattform sofort
verwalten kann. Nachfolgende Benutzer erhalten Standardrollen.

Diese automatische Zuweisung erfolgt nur einmal pro Benutzer. Danach fügen Sie sie bei Bedarf explizit zu anderen
Mandanten hinzu.

## Häufige Konfigurationen

### Einzelnes Unternehmen mit Abteilungen

Sysadmin-Mandant → Management-Mandant → Ein Mandant pro Abteilung

Manager erstellen Abteilungs-Mandanten und konfigurieren, auf welche Agenten jede Abteilung zugreifen kann.
Abteilungsbenutzer sehen nur die Ressourcen ihrer Abteilung.

### Multi-Kunden SaaS

Sysadmin-Mandant → Management-Mandant → Ein Mandant pro Kunde

Jeder Kunden-Mandant ist isoliert. Kunden können die Agenten oder Daten anderer Kunden nicht sehen. Manager nehmen neue
Kunden auf, indem sie einen Mandanten erstellen, relevante Agenten konfigurieren und die Benutzer dieses Kunden
hinzufügen.

### Beratungsunternehmen

Sysadmin-Mandant → Management-Mandant → Ein Mandant pro Kundenprojekt

Projekt-Mandanten geben Beratern Zugriff auf kundenspezifische Agenten und Wissen. Wenn ein Projekt endet, archivieren
Sie den Mandanten. Wenn ein Berater einem neuen Projekt beitritt, fügen Sie ihn dem Mandanten dieses Projekts hinzu.

### Entwicklungs-Workflow

Sysadmin-Mandant → Entwicklungs-Mandant → Staging-Mandant → Produktions-Mandant

Entwickler arbeiten im Entwicklungs-Mandanten mit gelockerten Kontrollen. Der Staging-Mandant spiegelt die Produktion
für Tests wider. Der Produktions-Mandant hat strenge Zugriffskontrollen. Dieselben Agenten, derselbe Code, verschiedene
Mandanten für verschiedene Zwecke.

## Mandanten-Lebenszyklus

Mandanten bleiben bestehen, bis sie explizit gelöscht werden. Sie können:

**Einen Mandanten archivieren**: Entfernen Sie alle Benutzer, behalten Sie aber den Mandanten und seine Rollen bei.
Nützlich für abgeschlossene Projekte oder inaktive Kunden. Niemand kann darauf zugreifen, aber die Konfiguration bleibt
erhalten, falls Sie sie reaktivieren müssen.

**Einen Mandanten löschen**: Entfernen Sie den Mandanten, alle seine Rollen und alle Benutzerzuordnungen. Permanent. Nur
möglich, nachdem zuerst alle Benutzer entfernt wurden.

::: warning Schutz des Standard-Mandanten
Der Standard-Mandant kann nicht gelöscht werden. Dies stellt sicher, dass die Plattform immer mindestens einen
funktionierenden Mandanten hat.
:::

## Praktische Tipps

::: tip Best Practices
**Dokumentieren Sie Ihre Entscheidungen**: Schreiben Sie auf, warum Sie jeden Mandanten erstellt haben und wie sein
Geltungsbereich sein soll. Sechs Monate später, wenn sich Rollen geändert haben, verhindert diese Dokumentation
Verwirrung.

**Beginnen Sie einfach**: Ein Management-Mandant und ein Endbenutzer-Mandant funktionieren für viele Organisationen.
Fügen Sie Komplexität nur hinzu, wenn Sie sie benötigen.

**Testen Sie mit eingeschränkten Benutzern**: Erstellen Sie ein Testkonto, fügen Sie es einem neuen Mandanten hinzu und
überprüfen Sie, was dieser Benutzer sehen kann. Nehmen Sie nichts an – verifizieren Sie.

**Vierteljährlich überprüfen**: Rollen ändern sich. Projekte enden. Neue Abteilungen entstehen. Ihre Mandantenstruktur
sollte sich mit Ihrer Organisation entwickeln.

**Planen Sie für Wachstum**: „Kunde 1“ funktioniert, wenn Sie drei Kunden haben. „Kunde - Acme Corp“ funktioniert, wenn
Sie dreihundert haben.
:::

```
```
