# Kapitel 05: Administration und Governance

Der operative Betrieb einer Enterprise-KI-Plattform erfordert weit mehr als nur die Bereitstellung von Modellen und
Rechenleistung. Für Schweizer Unternehmen, die in einem streng regulierten Umfeld agieren, sind Nachvollziehbarkeit,
Kostentransparenz und die Durchsetzung interner Richtlinien (Governance) entscheidende Erfolgsfaktoren. Eine
unkontrollierte KI-Nutzung führt unweigerlich zu Schatten-IT, unvorhersehbaren Kosten und Compliance-Verstössen.

Dieses Kapitel beschreibt die administrativen Werkzeuge des Swiss AI Hub, die es ermöglichen, die Plattform zentral zu
steuern, in bestehende Unternehmensprozesse zu integrieren und dabei höchste Sicherheitsstandards zu wahren. Der Fokus
liegt auf der Balance zwischen technologischer Freiheit für Innovation und strikter Kontrolle für den sicheren,
revisionssicheren Betrieb.

## Auf einen Blick

- **Granulare Zugriffskontrolle (RBAC):** Ein hierarchisches Berechtigungssystem steuert den Zugriff bis auf die Ebene
  einzelner Agenten-Instanzen und blendet nicht autorisierte Dienste in der UI dynamisch aus («Security by
  Invisibility»).
- **Integrierte Kostenbremse:** Das LLM-Gateway erzwingt technisch definierte Budgets und Ratenlimits (Tokens per
  Minute) pro Benutzer oder Abteilung, um Kostenexplosionen proaktiv zu verhindern.
- **Evidenzbasierte Qualitätssicherung:** Automatisierte Experimente mit «Golden Record»-Datasets und KI-Richtern messen
  Korrektheit und Vollständigkeit von Antworten vor jedem Deployment.
- **Datenschutz-Automation:** Automatische Löschzyklen für ephemere Daten (30 Tage) und API-gestützte Prozesse für
  Betroffenenrechte unterstützen die Einhaltung von DSGVO und revDSG.
- **Nahtlose Observability:** Die Plattform liefert Metriken und Logs im OpenTelemetry-Standard, standardmässig
  visualisiert über SigNoz, aber kompatibel mit jeder Enterprise-Monitoring-Lösung.

## Zentralisierte Zugriffskontrolle und Identitätsmanagement

### Geschäftlicher Nutzen

In grossen Organisationen ist die Verwaltung von Benutzerrechten eine komplexe Herausforderung. Das Risiko, dass
Mitarbeiter Zugriff auf sensible Daten oder teure KI-Modelle erhalten, für die sie nicht autorisiert sind, muss
systemisch ausgeschlossen werden. Manuelle Benutzerverwaltung ist fehleranfällig und skaliert nicht. Unternehmen
benötigen eine Lösung, die sich nahtlos in ihre bestehende Mitarbeiterverwaltung (Identity Provider) einfügt und das
Prinzip der minimalen Rechtevergabe («Least Privilege») automatisch durchsetzt. Dies reduziert den administrativen
Aufwand und minimiert die Angriffsfläche für internen Datenabfluss.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt den Ansatz einer föderierten Identität mit granularer Rollenbasierter Zugriffskontrolle
(RBAC). Anstatt eine isolierte Benutzerdatenbank zu pflegen, delegiert die Plattform die Authentifizierung an
vertrauenswürdige Unternehmenssysteme (z.B. via OIDC). Die Autorisierung hingegen erfolgt innerhalb der Plattform über
ein hierarchisches Berechtigungsmodell.

Ein zentrales Konzept ist hierbei die «Dynamische Dienstsichtbarkeit» (Dynamic Service Visibility). Die
Benutzeroberfläche der Plattform passt sich in Echtzeit an die Berechtigungen des angemeldeten Benutzers an. Funktionen,
Datenquellen oder Agenten-Profile, für die ein Nutzer keine Freigabe besitzt, werden nicht ausgegraut, sondern gar nicht
erst angezeigt. Dies eliminiert «Access Denied»-Frustrationen und erhöht die Sicherheit durch Unsichtbarkeit. Zudem
unterstützt das System Multi-Tenancy, wodurch verschiedene Abteilungen oder Mandanten auf derselben Infrastruktur
logisch strikt voneinander getrennt arbeiten können.

### Technische Umsetzung im Swiss AI Hub

Die Authentifizierung erfolgt über die Industriestandards OpenID Connect (OIDC) und OAuth 2.0. Dies ermöglicht eine
native Integration mit Microsoft Entra ID (ehemals Azure AD), Keycloak oder anderen Enterprise-Identity-Providern.
Funktionen wie Single Sign-On (SSO) und Multi-Faktor-Authentifizierung (MFA) werden somit direkt vom Identity Provider
übernommen.

Das interne Berechtigungssystem nutzt eine präzise Punkt-Notation-Syntax, die Administratoren erlaubt, Zugriffsrechte
extrem feingliedrig zu definieren:

- **Hierarchische Struktur:** Berechtigungen folgen dem Schema `aihub.[user|admin].<service>.<resource_id>`. Ein
  Administrator kann beispielsweise einem Teamleiter Zugriff auf alle Support-Agenten gewähren
  (`aihub.user.agent.support.>`), während ein Sachbearbeiter nur Zugriff auf eine spezifische Instanz erhält
  (`aihub.user.agent.support.bot_v1`).
- **Access Checker:** Die Prüfung der Rechte erfolgt ausschliesslich im Backend über eine «Access Checker»-Komponente.
  Diese validiert bei jedem API-Aufruf die Berechtigungen gegen die im Token übermittelten Rollen.
- **Sofortige Wirksamkeit:** Änderungen an Rollenzuweisungen werden ohne Cache-Verzögerung wirksam. Die
  Benutzeroberfläche fragt beim Laden den autorisierten Dienstkatalog ab und rendert nur die erlaubten Elemente.

## Ressourcensteuerung und finanzielle Governance

### Geschäftlicher Nutzen

Die Abrechnungsmodelle kommerzieller LLM-Anbieter basieren meist auf dem verbrauchsabhängigen «Pay-per-Token»-Prinzip.
Ohne strikte Kontrollen kann ein fehlerhaft konfigurierter Agent oder eine exzessive Nutzung durch eine einzelne
Abteilung das IT-Budget innerhalb weniger Tage aufbrauchen. Finanzverantwortliche benötigen daher Instrumente, um Kosten
nicht nur nachträglich zu analysieren, sondern proaktiv zu begrenzen und intern verursachergerecht zu verrechnen
(Chargeback). Transparenz über die tatsächlichen Kosten pro Anwendungsfall ist die Basis für jede ROI-Betrachtung von
KI-Projekten.

### Konzeptioneller Ansatz

Die Plattform implementiert ein mehrstufiges Kostenkontrollsystem, das Transparenz mit harten Limits («Circuit
Breakers») kombiniert. Kosten werden granular erfasst – unterschieden nach Eingabe (Prompt) und Ausgabe (Completion), da
diese oft unterschiedliche Preispunkte haben. Das System erlaubt die Definition von Budgets auf verschiedenen Ebenen:
global für den Mandanten oder individuell pro Benutzer.

Zusätzlich zu finanziellen Limits kommen technische Ratenbegrenzungen (Rate Limiting) zum Einsatz. Diese verhindern,
dass einzelne Akteure die Systemressourcen monopolisieren und die Performance für andere Nutzer beeinträchtigen, was
besonders bei der Nutzung von kapazitätsbegrenzten lokalen Modellen kritisch ist.

### Technische Umsetzung im Swiss AI Hub

Die technische Durchsetzung erfolgt direkt im LLM-Gateway. Da jeglicher Modellverkehr diesen zentralen Punkt passiert,
können hier Regeln (Policies) effektiv angewendet werden:

- **Harte Budgets:** Über Umgebungsvariablen wie `LITE_LLM_PROXY_USER_MAX_BUDGET` werden Obergrenzen definiert. Erreicht
  ein Nutzer dieses Limit innerhalb einer Periode (z.B. `30d`), werden weitere Anfragen automatisch blockiert. «Soft
  Budgets» ermöglichen Warnmeldungen vor Erreichen des Limits.
- **Granulares Rate Limiting:** Administratoren können Parameter wie `TPM_LIMIT` (Tokens per Minute) oder `RPM_LIMIT`
  (Requests per Minute) konfigurieren, um die Last zu steuern.
- **Echtzeit-Tracking:** Das System protokolliert jeden API-Aufruf und berechnet die Kosten basierend auf den aktuellen
  Modellpreisen. Diese Informationen werden direkt im Konversations-Thread angezeigt, sodass auch Endanwender ein Gefühl
  für die verursachten Kosten entwickeln.

## Qualitätssicherung und Compliance-Tools

### Geschäftlicher Nutzen

Die Einhaltung gesetzlicher Vorgaben wie des Schweizer Datenschutzgesetzes (revDSG) oder der EU-DSGVO ist zwingend.
Insbesondere die Rechte von Betroffenen auf Löschung («Right to be Forgotten») stellen bei KI-Systemen eine
Herausforderung dar. Gleichzeitig müssen Unternehmen sicherstellen, dass Agenten qualitativ hochwertige und korrekte
Antworten liefern, bevor sie auf Kunden losgelassen werden. Ein Agent, der halluziniert, verursacht Reputationsschäden.
Die Qualitätssicherung darf sich daher nicht auf subjektives «Ausprobieren» verlassen, sondern muss messbar sein.

### Konzeptioneller Ansatz

Der Swiss AI Hub integriert Compliance- und Qualitätswerkzeuge direkt in den administrativen Workflow. Anstatt sich auf
Bauchgefühl zu verlassen, ermöglicht die Plattform eine evidenzbasierte Bewertung mittels definierter Datasets («Golden
Records»). Hierbei bewerten automatisierte KI-Richter die Antworten des Agenten anhand von Metriken wie Korrektheit,
Vollständigkeit und Prägnanz.

Für den Datenschutz verfolgt die Plattform den Ansatz der Datensparsamkeit («Privacy by Design»). Daten werden mit
Lebenszyklen versehen, sodass temporäre Daten automatisch aus dem System entfernt werden, ohne dass ein manueller
Eingriff erforderlich ist.

### Technische Umsetzung im Swiss AI Hub

Die Plattform stellt spezifische Dienste bereit, um diese Anforderungen technisch abzubilden:

- **Automatisierte Experimente:** Administratoren erstellen Datasets mit Frage-Antwort-Paaren. Ein Experimentier-Lauf
  testet den Agenten gegen diese Fälle. KI-Modelle fungieren als Richter und vergeben 0 bis 5 Sterne für die Qualität
  der Antwort im Vergleich zur Referenz. Dies deckt Regressionen nach Updates der Wissensdatenbank sofort auf.
- **Benutzerfeedback (Elo-Rating):** Nutzer können Antworten via Daumen-hoch/runter bewerten. Im «Arena-Modus» werden
  Antworten verschiedener Modelle blind verglichen. Dies speist eine Bestenliste (Elo-Rating), die zeigt, welche Modelle
  in der Praxis am besten performen.
- **Datenschutz-Automation:** Ephemere Daten verfallen standardmässig automatisch nach 30 Tagen. Für permanente Daten
  existieren APIs, um Benutzerprofile zu bereinigen oder Nutzer aus Konversations-Threads zu entfernen, was die
  Umsetzung von Löschbegehren gemäss Art. 17 DSGVO technisch ermöglicht.
- **Rechtsgrundlage:** Vor der ersten Nutzung können Nutzungsbedingungen und Datenschutzerklärungen eingeblendet werden
  (Consent Management), deren Zustimmung protokolliert wird.

## Operative Exzellenz und Überwachung

### Geschäftlicher Nutzen

Im produktiven Betrieb («Day 2 Operations») ist die Verfügbarkeit und Stabilität der Plattform entscheidend. IT-Teams
müssen Probleme erkennen, bevor sie den Endanwender beeinträchtigen. Eine isolierte KI-Plattform, die ihre eigenen
proprietären Monitoring-Tools mitbringt, erzeugt Datensilos. CIOs fordern daher Lösungen, die sich nahtlos in die
bestehende Überwachungslandschaft integrieren lassen, um einen zentralen Blick auf die gesamte IT-Gesundheit zu
gewährleisten.

### Konzeptioneller Ansatz

Die Observability-Strategie des Swiss AI Hub basiert auf den drei Säulen: Health Checks, Metriken und Logs. Das System
ist so konzipiert, dass es vollständige Transparenz über den Zustand der Infrastruktur und der Applikation bietet.

Entscheidend ist hierbei die Vermeidung von Herstellerabhängigkeiten (Vendor Lock-in). Die Plattform schreibt nicht vor,
welches Monitoring-Tool verwendet werden muss, sondern stellt die Daten im offenen OpenTelemetry-Standard bereit. Dies
ermöglicht es Unternehmen, ihre bestehenden Investitionen in Tools wie Splunk, Datadog oder Dynatrace weiter zu nutzen.

### Technische Umsetzung im Swiss AI Hub

Das technische Fundament bildet der **OpenTelemetry (OTel) Collector**, der als zentrale Datendrehscheibe fungiert.

- **SigNoz Integration:** Als offiziell unterstütztes Backend wird **SigNoz** für die Visualisierung von Logs, Metriken
  und Traces bereitgestellt. Es kann als Cloud-Service oder selbst gehostet (Self-Hosted) betrieben werden, um
  Datenhoheit zu gewährleisten.
- **Health Checks:** Die Plattform bietet mehrstufige Gesundheitsprüfungen. Von einfachen Docker-Checks («Läuft der
  Container?») bis zu synthetischen Probes, die die Reaktionsfähigkeit der Vektordatenbank prüfen.
- **Zentraler Export:** Über einfache Konfigurationsänderungen im OTel Collector können Telemetriedaten an beliebige
  externe Backends gesendet werden. Das System unterstützt Batching und Komprimierung, um die Netzwerklast zu
  minimieren.
- **Proaktives Alerting:** Kritische Ereignisse – wie das Erreichen von Budget-Limits oder Ausfälle von Komponenten –
  können Alarme auslösen, die via Webhook an Slack, Microsoft Teams oder PagerDuty weitergeleitet werden.
