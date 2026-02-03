# Kapitel 05: Administration und Governance

Der produktive Einsatz einer Enterprise-KI-Plattform erfordert weit mehr als nur den Zugriff auf leistungsfähige
Sprachmodelle. Für Schweizer Unternehmen, die in einem anspruchsvollen regulatorischen Umfeld agieren, sind eine präzise
Steuerung, lückenlose Nachvollziehbarkeit und strikte Kostentransparenz die Grundvoraussetzungen für den «Day 2», den
stabilen Dauerbetrieb. Ohne eine zentrale Governance-Instanz drohen unkontrollierte Kostenexplosionen, Schatten-IT und
Compliance-Verstösse, welche die strategischen Vorteile der künstlichen Intelligenz zunichtemachen.

Dieses Kapitel erläutert, wie der Swiss AI Hub administrative Exzellenz und technische Kontrolle vereint. Durch ein tief
in die Architektur integriertes Rollen- und Mandantensystem sowie automatisierte Monitoring-Tools wird sichergestellt,
dass die Plattform nicht nur technologisch führend, sondern auch organisatorisch beherrschbar bleibt. Das Ziel ist eine
Umgebung, in der Innovation innerhalb klar definierter Leitplanken stattfindet.

## Auf einen Blick

- **Hierarchische Zugriffskontrolle (RBAC):** Ein feingliedriges Berechtigungssystem steuert den Zugriff bis auf die
  Ebene einzelner Agenten-Instanzen und setzt das Prinzip der minimalen Rechtevergabe («Least Privilege») konsequent um.
- **Mandantenfähigkeit mit Isolationsgarantie:** Die Plattform ermöglicht die logische Trennung von Abteilungen oder
  Kunden innerhalb einer Instanz, wobei das Agenten-Unabhängigkeitsprinzip für maximale Flexibilität sorgt.
- **Integriertes Kostenmanagement:** Durch das zentrale LLM-Gateway werden Budgets und Ratenlimits (Tokens per Minute)
  pro Benutzer oder Mandant in Echtzeit erzwungen, was finanzielle Planungssicherheit garantiert.
- **Enterprise Observability:** Basierend auf dem OpenTelemetry-Standard liefert die Plattform tiefe Einblicke in
  Systemgesundheit und Performance, nahtlos integrierbar in bestehende IT-Monitoring-Landschaften.
- **Automatisierte Compliance-Tools:** Vordefinierte Daten-Lifecycles (30 Tage für ephemere Daten) und Werkzeuge zur
  Qualitätssicherung unterstützen die Einhaltung von revDSG und DSGVO systematisch.

## Identitätsmanagement und hierarchische Zugriffskontrolle

### Mehrwert für die Unternehmenssicherheit

In einer modernen Unternehmensumgebung ist die manuelle Verwaltung von Benutzerrechten über verschiedene KI-Tools hinweg
nicht nur ineffizient, sondern ein massives Sicherheitsrisiko. Das Ziel jeder IT-Strategie muss es sein, den Zugriff auf
sensible Daten und teure Ressourcen so zu steuern, dass Mitarbeitende exakt die Werkzeuge sehen, die sie für ihre Arbeit
benötigen – nicht mehr und nicht weniger. Eine zentrale Identitätsverwaltung reduziert den administrativen Aufwand
drastisch, verhindert verwaiste Konten und stellt sicher, dass Sicherheitsrichtlinien wie Multi-Faktor-Authentifizierung
(MFA) unternehmensweit durchgesetzt werden.

### Föderierte Identität und dynamische Sichtbarkeit

Der Swiss AI Hub setzt auf das Konzept der föderierten Identität. Anstatt eine eigene, isolierte Benutzerdatenbank zu
führen, integriert sich die Plattform direkt in die bestehende Identitätsinfrastruktur des Unternehmens. Die
Autorisierung erfolgt über eine hierarchische rollenbasierte Zugriffskontrolle (RBAC), die über einfache
«Ja/Nein»-Entscheidungen hinausgeht.

Ein Kernkonzept ist hierbei die «Dynamische Dienstsichtbarkeit». Die Benutzeroberfläche passt sich in Echtzeit an die
Berechtigungen des Nutzers an. Funktionen, Wissenssammlungen oder Agenten-Profile, für die keine Autorisierung vorliegt,
werden nicht nur gesperrt, sondern gar nicht erst angezeigt. Diese «Security by Invisibility» minimiert die
Angriffsfläche und erhöht die Benutzerfreundlichkeit, da frustrierende Fehlermeldungen vermieden werden.

### Technische Implementierung via RBAC und OIDC

Technisch basiert die Authentifizierung auf den Industriestandards OpenID Connect (OIDC) und OAuth 2.0. Dies ermöglicht
die native Anbindung an Provider wie Microsoft Entra ID (ehemals Azure AD) oder Keycloak. Nach der Anmeldung validiert
die Plattform kryptografisch signierte JSON Web Tokens (JWT) und weist den Nutzer einer oder mehreren Rollen zu.

Das Berechtigungssystem nutzt eine präzise Punkt-Notation im Format `aihub.[user|admin].<service>.<resource_id>`.
Administratoren können durch Wildcards (z. B. `aihub.user.agent.hr.*`) Gruppen von Ressourcen effizient verwalten. Ein
zentraler «Access Checker» im Backend prüft bei jedem API-Aufruf die Berechtigungen, wodurch clientseitige
Manipulationen ausgeschlossen sind. Jede Zugriffsentscheidung wird zudem revisionssicher im Audit-Log protokolliert.

## Mandantenfähigkeit und organisatorische Trennung

### Effiziente Abbildung von Konzernstrukturen

Grosse Organisationen bestehen oft aus unabhängigen Geschäftseinheiten, die sich zwar eine Infrastruktur teilen, aber
ihre Daten und Prozesse strikt trennen müssen. Ohne eine saubere Mandantenfähigkeit (Multi-Tenancy) entstehen
unweigerlich Datensilos oder gefährliche Überschneidungen. Die Herausforderung besteht darin, eine Plattform so zu
strukturieren, dass Synergien bei der Wartung genutzt werden können, während die operative und datenschutzrechtliche
Trennung zwischen Abteilungen wie «Recht», «Finanz» oder «HR» gewahrt bleibt.

### Logische Isolation und das Agenten-Unabhängigkeitsprinzip

Die Plattform löst diese Anforderung durch die Schaffung logischer Mandanten (Tenants). Jeder Mandant bildet einen
isolierten Arbeitsbereich mit eigenen Benutzern, Rollen und Wissensdatenbanken. Ein entscheidendes Merkmal des Swiss AI
Hub ist dabei das «Agenten-Unabhängigkeitsprinzip».

Klassische Systeme lassen Agenten oft die Berechtigungen des Nutzers erben, was deren Einsatz in automatisierten
Workflows erschwert. Im Swiss AI Hub agieren Agenten unabhängig von den individuellen Rechten des Nutzers, der mit ihnen
interagiert. Der Datenzugriff eines Agenten wird exakt über sein Agenten-Profil definiert. Die Governance erfolgt
darüber, welcher Benutzer Zugriff auf welchen Agenten erhält. Dies ermöglicht es beispielsweise, einen «CFO-Agenten» zu
bauen, der auf alle Finanzdaten zugreift, aber nur für die Geschäftsleitung sichtbar ist.

### Drei-Ebenen-Mandantenmodell in der Praxis

In der praktischen Umsetzung hat sich ein dreistufiges Modell bewährt, das die Plattform standardmässig unterstützt:

1. **Systemadministrator-Ebene (Sysadmin):** Ein dedizierter Mandant für die IT-Infrastruktur-Teams, die
   Agenten-Baupläne deployen und die Systemgesundheit überwachen.
2. **Management-Ebene:** Mandanten für Business-Administratoren, die innerhalb ihrer Geschäftseinheit Agenten-Profile
   konfigurieren, Nutzer zuweisen und die Kosten kontrollieren, ohne in den Programmcode einzugreifen.
3. **Endbenutzer-Ebene (Abteilungen/Kunden):** Die operative Ebene, auf der Mitarbeitende mit den für sie
   freigeschalteten Agenten chatten oder an Prozessen teilnehmen. Diese Struktur trennt technische Operationen sauber
   von der geschäftlichen Administration und schützt die Integrität der gesamten Systemlandschaft.

## Ressourcensteuerung und Kostenmanagement

### Wirtschaftliche Planungssicherheit

Die verbrauchsabhängige Abrechnung moderner KI-Modelle stellt Finanzverantwortliche vor neue Herausforderungen. Ein
einziger fehlerhafter Workflow oder eine exzessive Nutzung durch eine Abteilung kann das IT-Budget innerhalb kürzester
Zeit belasten. Um KI nachhaltig im Unternehmen zu etablieren, ist ein System erforderlich, das Kosten nicht nur im
Nachhinein aufschlüsselt, sondern aktiv begrenzt. Nur durch absolute Transparenz über die Kosten pro Abteilung, Projekt
oder Agent kann ein klarer Business Case gerechnet und der Return on Investment (ROI) belegt werden.

### Proaktive Limits und Echtzeit-Monitoring

Die Strategie des Swiss AI Hub basiert auf einer Kombination aus Echtzeit-Tracking und harten technischen Sperren
(«Circuit Breakers»). Das System erfasst die Token-Nutzung für jede Interaktion, unterschieden nach Eingabe (Prompt) und
Ausgabe (Completion), da diese oft unterschiedlich bepreist werden.

Administratoren haben die Möglichkeit, Budgets auf verschiedenen Ebenen zu definieren: global für die gesamte Plattform
oder individuell für einzelne Benutzer und Mandanten. Neben finanziellen Limiten können auch technische
Ratenbegrenzungen (Rate Limiting) gesetzt werden. Diese verhindern, dass einzelne Power-User die verfügbare Bandbreite
der Modell-Provider monopolisieren und so die Performance für andere Abteilungen beeinträchtigen.

### Umsetzung im LLM-Gateway

Die technische Durchsetzung erfolgt zentral im LLM-Gateway (LiteLLM). Da jeglicher Modellverkehr diesen Punkt passieren
muss, können Policies hier effektiv angewendet werden. Über Parameter wie `LITE_LLM_PROXY_USER_MAX_BUDGET` wird eine
harte Obergrenze definiert. Wird dieses Limit erreicht, blockiert das Gateway weitere Anfragen für den betreffenden
Nutzer automatisch.

Zusätzlich können «Soft Budgets» konfiguriert werden, die bei Erreichen eines Schwellenwertes (z. B. 80 Prozent des
Budgets) Warnmeldungen via E-Mail oder Slack auslösen. Für die interne Verrechnung bietet das System detaillierte
Exportfunktionen, welche die verursachten Kosten bis auf die Ebene einzelner Agenten-Interaktionen aufschlüsseln, was
eine verursachergerechte Kostenallokation ermöglicht.

## Operative Überwachung und Compliance-Management

### Stabilität durch tiefe Observability

Für den produktiven Betrieb ist die Sichtbarkeit («Observability») der Systeme entscheidend. Wenn ein Agent eine falsche
Antwort liefert oder ein Workflow stockt, muss die IT in der Lage sein, die Ursache sofort zu identifizieren. In
regulierten Sektoren ist zudem die Dokumentation der Datenverarbeitung zwingend. Ein «Black-Box»-Betrieb ist mit
Schweizer Compliance-Vorgaben nicht vereinbar. Unternehmen benötigen Werkzeuge, die den gesamten Pfad einer Information
von der Quelle bis zur Antwort lückenlos nachvollziehbar machen.

### Standardbasierte Telemetrie und Daten-Lifecycles

Die Überwachungsstrategie des Swiss AI Hub basiert auf drei Säulen: Health Checks, Metriken und Distributed Tracing. Um
eine nahtlose Integration in bestehende Enterprise-Umgebungen zu ermöglichen, nutzt die Plattform den
herstellerneutralen OpenTelemetry-Standard (OTel). Dies verhindert einen Vendor-Lock-in bei Monitoring-Tools und erlaubt
die Nutzung vorhandener Dashboards in Splunk, Datadog oder Dynatrace.

Ein weiterer Pfeiler der Governance ist das automatisierte Datenmanagement. Um den Anforderungen der Datensparsamkeit
(revDSG/DSGVO) gerecht zu werden, implementiert die Plattform strikte Daten-Lifecycles. Ephemere Daten, die nur für das
Debugging oder die kurzfristige Prozesssteuerung nötig sind, werden nach einem definierten Fenster automatisch gelöscht.

### Technische Realisierung mit OTel und SigNoz

Die technische Zentrale für alle Telemetriedaten ist der OpenTelemetry Collector. Er empfängt Daten von allen
Plattform-Komponenten, filtert Rauschen heraus und leitet sie an die konfigurierten Backends weiter:

- **SigNoz:** Dient als offiziell unterstütztes Backend für die Visualisierung von Logs und System-Metriken (CPU,
  Speicher, Latenzen). Es bietet leistungsstarke Dashboards und ein flexibles Alarmierungssystem für kritische
  Dienstausfälle.
- **Phoenix:** Wird speziell für das KI-Tracing eingesetzt. Hier werden LLM-Aufrufe, Token-Nutzung und die abgerufenen
  Dokumenten-Snippets visualisiert.
- **Datenaufbewahrung:** In Redis gespeicherte Ausführungsdaten verfallen automatisch nach 30 Tagen. Für permanente
  Daten in der NoSQL-Datenbank können Organisationen individuelle Löschrichtlinien konfigurieren, um dem «Recht auf
  Vergessenwerden» technisch Rechnung zu tragen.
- **Qualitätssicherung:** Über den integrierten Evaluierungs-Service können Administratoren Agenten gegen «Golden
  Record»-Datasets testen. Ein KI-Richter bewertet dabei die Antworten auf Korrektheit und Vollständigkeit, was eine
  evidenzbasierte Freigabe von Agenten-Updates ermöglicht.
