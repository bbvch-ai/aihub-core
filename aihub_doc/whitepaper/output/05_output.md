# Kapitel 05: Administration und Governance

Die effektive Implementierung von Künstlicher Intelligenz (KI) in Unternehmen erfordert weit mehr als nur technische
Funktionalität; sie verlangt eine robuste administrative Steuerung und die lückenlose Einhaltung komplexer
Governance-Vorgaben. Für Schweizer Organisationen, die höchsten Anforderungen an Datensouveränität, Compliance und
Transparenz unterliegen, ist eine Plattform entscheidend, die eine zentrale und revisionssichere Verwaltung der gesamten
KI-Landschaft ermöglicht. Dieses Kapitel legt dar, wie der Swiss AI Hub diese Herausforderungen adressiert, indem er
granulare Zugriffskonzepte, transparente Kostenkontrolle, kontinuierliche Qualitätssicherung und eine nahtlose
Integration in bestehende IT-Umgebungen bietet.

## 1. Granulare Zugriffssteuerung und nahtlose Identitätsintegration

Der Einsatz von KI in sensiblen Geschäftsbereichen macht eine präzise Kontrolle darüber unerlässlich, wer auf welche
KI-Funktionen und Daten zugreifen darf. Dies gewährleistet die Einhaltung strenger Compliance-Vorgaben und minimiert
Sicherheitsrisiken. Schweizer Unternehmen profitieren von einer Lösung, die nicht nur eine fragmentierte
Nutzerverwaltung vermeidet, sondern auch die Unternehmenssicherheit durch zentrale Authentifizierungsstandards stärkt.

### Mehrwert und Nutzen: Sicherheit, Compliance und operative Effizienz

Für C-Level-Führungskräfte bedeutet dies die Gewissheit, dass sensible Unternehmensdaten und KI-Anwendungen gemäss den
internen Richtlinien und externen Regularien (z.B. revDSG, DSGVO) geschützt sind. Eine konsistente Zugriffsverwaltung
reduziert das Risiko von Datenlecks und unautorisierten Aktionen. Für IT-Professionals resultiert die nahtlose
Identitätsintegration in einer erheblichen Effizienzsteigerung durch die Vermeidung paralleler Nutzerverwaltungen und
die Standardisierung von Authentifizierungsprozessen, was den administrativen Aufwand minimiert. Die dynamische
Benutzeroberfläche stellt zudem sicher, dass Anwender nur die für ihre Rolle relevanten Funktionen sehen, was die
Komplexität reduziert und die Benutzerakzeptanz fördert.

### Konzepte & Prozesse: Rollenbasierte Zugriffskontrolle und standardisierte Authentifizierung

Der Swiss AI Hub implementiert ein ausgeklügeltes, hierarchisches Rollenbasiertes Zugriffskontrollsystem (RBAC), das auf
dem Prinzip der geringsten Rechte basiert. Dieses System bildet komplexe Organisationsstrukturen ab und stellt sicher,
dass Nutzer ausschliesslich auf jene Ressourcen zugreifen können, für die sie explizit autorisiert sind. Die
Benutzeroberfläche nutzt eine dynamische Dienstsichtbarkeit: Beim Laden der Suite fragt sie das Backend nach dem
autorisierten Dienstkatalog des Benutzers ab. Das Backend bewertet die Berechtigungen des Benutzers anhand der
Anforderungen jedes registrierten Dienstes und gibt nur Dienste zurück, auf die der Benutzer zugreifen kann. Die
Benutzeroberfläche rendert Navigationselemente ausschliesslich für autorisierte Dienste, wodurch Benutzer keine
Funktionen sehen, die sie nicht nutzen können. Dies minimiert die Komplexität und eliminiert "Zugriff
verweigert"-Meldungen. Automatische Berechtigungsaktualisierungen stellen zudem sicher, dass Änderungen der
Rollenzuweisungen sofort in der Benutzeroberfläche des Benutzers reflektiert werden, sobald eine neue Sitzung gestartet
wird. Die Authentifizierung erfolgt über branchenübliche Protokolle wie OpenID Connect (OIDC) und OAuth 2.0, wodurch
eine sichere und standardkonforme Anbindung an bestehende Enterprise-Identitätssysteme ermöglicht wird.

### Technische Umsetzung im Swiss AI Hub: Access Checker, Entra ID und JWT-Validierung

Technisch verwendet der Swiss AI Hub eine strukturierte Punkt-Notation für Berechtigungen
(`aihub.[user|admin].<service>.<resource_type>.<resource_id>`), die Wildcard-Unterstützung (z.B. `aihub.user.agent.*`
für alle Agenten einer Klasse oder `aihub.user.agent.?>` für alle Agenten) und implizite Berechtigungen bietet, um eine
flexible, aber präzise Zugriffssteuerung zu ermöglichen. Die clientseitige Benutzeroberfläche fragt den autorisierten
Dienstkatalog vom Backend ab, der auf Basis der Benutzerberechtigungen gefiltert wird, sodass nur relevante Navigations-
und Funktionselemente gerendert werden. Die gesamte Berechtigungsbewertung erfolgt serverseitig über eine
`AccessChecker`-Komponente. Dies verhindert clientseitige Manipulationen und implementiert das "Sicherheit durch
Unsichtbarkeit"-Prinzip, indem nicht autorisierte Dienste keine Schnittstellenpräsenz haben und somit die Angriffsfläche
reduziert wird.

Die Plattform authentifiziert Benutzer über den OAuth 2.0 Authorization Code Flow mit PKCE und validiert JSON Web Tokens
(JWT) mittels öffentlicher Schlüssel vom JWKS-Endpoint des Identitäts-Providers. Für den API-Zugriff wird
standardmässige OAuth 2.0 Bearer Token-Authentifizierung unterstützt. Die primäre Integration erfolgt mit Microsoft
Entra ID (Azure Active Directory), wobei Benutzerprofile und Rollenzuweisungen über die Microsoft Graph API abgerufen
werden, was die Zuordnung von Organisationsgruppen zu Plattformrollen ermöglicht. Die Architektur unterstützt die
Erweiterung auf andere OIDC-konforme Identitäts-Provider. Die Multi-Tenant-Isolation, die eine vollständige Trennung von
Diensten und Ressourcen pro Organisationseinheit gewährleistet, unterstreicht die datenschutzkonforme Ausrichtung der
Plattform. Die Plattform unterstützt Multi-Faktor-Authentifizierung (MFA) und Conditional Access (kontextbasierte
Zugriffsrichtlinien) über die Integration mit dem jeweiligen Enterprise-Identitäts-Provider (z.B. Microsoft Entra ID).
Eine native Implementierung von Passkeys ist in der aktuellen Dokumentation nicht explizit aufgeführt, wird aber
prinzipiell von modernen OIDC-Providern unterstützt.

## 2. Transparente Kostenkontrolle und Ressourcenallokation

Der Betrieb von KI-Systemen kann ohne transparente Überwachung schnell zu unkontrollierten Ausgaben führen. Für
Unternehmen ist es daher von grosser Bedeutung, die Betriebskosten zu managen, Ausgaben zu optimieren und Budgets
präzise zu prognostizieren. Dies erfordert eine detaillierte Kostenkontrolle und die Möglichkeit zur
verursachergerechten internen Verrechnung.

### Mehrwert und Nutzen: Budget-Sicherheit und Kosteneffizienz

C-Level-Führungskräfte erhalten durch detaillierte Kostenübersichten die notwendige Transparenz, um KI-Investitionen zu
rechtfertigen, Budgets effektiv zu planen und Kostenexplosionen zu vermeiden. Die Möglichkeit zur internen Verrechnung
(Chargeback) pro Abteilung oder Projekt schafft Anreize für einen verantwortungsvollen Umgang mit KI-Ressourcen.
IT-Teams können Optimierungspotenziale identifizieren und Ressourcen effizienter zuweisen, was die Kosteneffizienz des
gesamten KI-Betriebs steigert.

### Konzepte & Prozesse: Token-basierte Kostenmodelle und proaktives Budgetmanagement

KI-Kosten werden primär durch die Token-Nutzung bestimmt, wobei zwischen verschiedenen Arten von Tokens unterschieden
wird: **Prompt-Tokens** (Ihre Eingabe an die KI), **Completion-Tokens** (die von der KI generierten Antworten) und
**Embedding-Tokens** (Dokumentenverarbeitung für Suche und Abruf). Jede dieser Token-Arten hat typischerweise
unterschiedliche Preispunkte. Die Plattform verfolgt diese Kosten über alle Modelle hinweg, unabhängig davon, ob es sich
um Cloud-Dienste (Pay-per-Token) oder lokal gehostete Lösungen (feste Infrastrukturkosten) handelt. Zur Optimierung
werden Modellstufen für unterschiedliche Anwendungsfälle empfohlen:

- **Flaggschiff-Modelle** (z.B. GPT-5) für komplexe Denkprozesse und Aufgaben mit hoher Genauigkeit (höchste Kosten).
- **Ausgewogene Modelle** (z.B. GPT-5 mini) für Standard-Workflows und interne Assistenten (mittlere Kosten).
- **Effiziente Modelle** (z.B. GPT-5 nano) für einfache Aufgaben mit hohem Volumen, wie Klassifizierung (geringste
  Kosten).

Budgets und Ratenbegrenzungen sind konzipiert, um Ausgabenlimits und Nutzungsbeschränkungen auf Nutzer- oder
Abteilungsebene durchzusetzen.

### Technische Umsetzung im Swiss AI Hub: Umfassendes Kosten-Tracking und Konfigurationsoptionen

Der Swiss AI Hub verfolgt die Kosten für jede Konversation, indem er die Token-Nutzung automatisch erfasst und die
Ausgaben berechnet. Diese Informationen werden direkt im Konversationsverlauf angezeigt und ermöglichen Administratoren
eine granulare Analyse auf Agenten-, Benutzer- oder Thread-Ebene. Für selbst gehostete Modelle können fixe Kostenwerte
zugewiesen werden, um eine konsistente Kostenverfolgung zu gewährleisten.

Budgets und Ratenbegrenzungsfunktionen werden durch LiteLLM bereitgestellt und können über Umgebungsvariablen wie
`LITE_LLM_PROXY_USER_MAX_BUDGET` (harte Obergrenze), `LITE_LLM_PROXY_USER_SOFT_BUDGET` (Warnschwelle),
`LITE_LLM_PROXY_USER_BUDGET_DURATION` (Zurücksetzungszeitraum), `LITE_LLM_PROXY_USER_TPM_LIMIT` (Tokens pro Minute),
`LITE_LLM_PROXY_USER_RPM_LIMIT` (Anfragen pro Minute) und `LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS` (gleichzeitige
Anfragen) konfiguriert werden. Es ist wichtig zu beachten, dass diese Infrastruktur zwar vorhanden ist, die Limits
jedoch standardmässig nicht aktiviert sind und eine explizite Umgebungskonfiguration während des Deployments erfordern.
Bei Aktivierung ermöglichen diese Funktionen eine feingranulare Steuerung und optimieren die Modellauswahl basierend auf
der Aufgabenkomplexität.

## 3. Kontinuierliche Qualitätssicherung und Feedback-Loops

Das Vertrauen in KI-Systeme und deren breite Akzeptanz im Unternehmen hängt massgeblich von der Qualität und
Verlässlichkeit ihrer Ergebnisse ab. Eine proaktive Qualitätssicherung ist unerlässlich, um Halluzinationen,
unerwünschten Bias oder Model-Drift frühzeitig zu erkennen und die KI-Performance kontinuierlich zu verbessern.

### Mehrwert und Nutzen: Verlässlichkeit, Vertrauen und iterative Verbesserung

Für Führungskräfte bedeutet eine robuste Qualitätssicherung die Gewissheit, dass die KI-Systeme präzise und
vertrauenswürdige Informationen liefern, was die Akzeptanz und den ROI von KI-Investitionen steigert. Die iterative
Verbesserung auf Basis von Nutzerfeedback und systematischen Tests hilft, die KI kontinuierlich an neue Anforderungen
anzupassen und ihre Leistungsfähigkeit zu maximieren. IT- und Fachteams profitieren von strukturierten Methoden zur
Identifizierung von Schwachstellen und zur Validierung von Optimierungsmassnahmen.

### Konzepte & Prozesse: Systematische Agentenbewertungen und integriertes Nutzerfeedback

Der Swiss AI Hub nutzt ein System für Agentenbewertungen, bei dem KI-Agenten anhand vordefinierter Datasets (Testfragen
mit bekannten Referenzantworten) evaluiert werden. Drei unabhängige KI-Richter (LLMs) bewerten die generierten
Antworten, um eine objektive Qualitätsmessung zu gewährleisten. Ergänzend dazu ermöglicht die Plattform die direkte
Integration von Benutzerfeedback über Daumen-hoch/Daumen-runter-Mechanismen in Konversationen. Dieses Feedback fliesst
in ein Elo-basiertes Ranglistensystem ein, das die Modellleistung basierend auf der tatsächlichen Nutzung bewertet und
themenbasiertes Reranking unterstützt. Der sogenannte Arena-Modus ermöglicht zudem einen unvoreingenommenen Vergleich
verschiedener Modelle, indem er zufällig Modelle für die Beantwortung auswählt und Benutzerfeedback direkt zur relativen
Bewertung nutzt.

### Technische Umsetzung im Swiss AI Hub: Datasets, Experimente und Bewertungsmetriken

Um die Qualität von Agenten zu testen, können Administratoren über den Bewertungsdienst Datasets erstellen, die
repräsentative Fragen und deren Referenzantworten enthalten. Diese Datasets dienen als Grundlage für Experimente, bei
denen ein ausgewählter Agent gegen das Dataset getestet wird. Die Bewertung erfolgt durch drei KI-Richter (LLMs), die
jede Agentenantwort anhand von drei Metriken (0-5 Sterne) bewerten:

- **Korrektheit:** Faktische Genauigkeit im Vergleich zur Referenzantwort, frei von Fehlinformationen, Halluzinationen
  oder Widersprüchen.
- **Vollständigkeit:** Behandelt alle Aspekte der Anfrage, einschliesslich mehrteiliger Fragen und impliziter
  Bedürfnisse.
- **Prägnanz:** Effiziente und direkte Formulierung ohne irrelevante Abschweifungen, Redundanzen oder übermässiges
  Füllmaterial.

Die Ergebnisse der Experimente zeigen Sternenbewertungen und eine detaillierte Aufschlüsselung pro Frage,
einschliesslich der Agentenantwort und Latenz. Die Phoenix UI, die unter `http://localhost:6006` erreichbar ist, kann
für tiefere Untersuchungen von Konversationsverläufen und Roh-Telemetriedaten herangezogen werden. Benutzer können
KI-Antworten in der Chat-Benutzeroberfläche bewerten. Bei Abgabe eines Feedbacks wird ein Schnappschuss des Chats
erstellt. Das Feedback-System hilft somit, die besten Modelle für spezifische Anwendungsfälle zu identifizieren und
Verbesserungspotenziale aufzuzeigen. Eine automatisierte, out-of-the-box Bias-Überwachung, Modell-Drift-Erkennung oder
Produktions-A/B-Tests mit Traffic-Aufteilung sind derzeit nicht implementiert, können aber auf dem bereitgestellten
Bewertungs-Framework und OpenTelemetry-Tracing aufgebaut werden.

## 4. Umfassende operative Überwachung (Observability) und Auditierung

Ein produktiver Betrieb von KI-Systemen erfordert Transparenz, Zuverlässigkeit und Vorhersehbarkeit. Um potenzielle
Probleme proaktiv zu erkennen und die Compliance zu gewährleisten, bedarf es einer integrierten Observability Suite und
revisionssicherer Audit-Trails.

### Mehrwert und Nutzen: Proaktive Problemerkennung und Compliance-Sicherheit

Für IT-Führungskräfte und Operations-Teams ist die umfassende Observability entscheidend, um die Gesundheit und Leistung
der Plattform in Echtzeit zu überwachen, Engpässe zu identifizieren und Ausfälle zu verhindern, bevor sie sich auf die
Benutzer auswirken. Dies minimiert den administrativen Aufwand und sichert eine hohe Verfügbarkeit. Lückenlose
Audit-Trails sind für Compliance-Teams von grundlegender Bedeutung, um regulatorische Anforderungen zu erfüllen und die
Nachvollziehbarkeit von KI-Entscheidungen zu gewährleisten, was die Rechtmässigkeit der Datenverarbeitung nachweisbar
macht.

### Konzepte & Prozesse: Die Säulen der Observability und Distributed Tracing

Die Überwachungsphilosophie der Plattform basiert auf den branchenüblichen Säulen der Observability: **Health Checks**
(Überprüfung der Liveness und Readiness jeder Komponente), **Metriken** (quantitative Messungen von Leistung und
Ressourcennutzung) und **Logs** (detaillierte, chronologische Aufzeichnungen aller Ereignisse). Ein zentrales Element
ist das **End-to-End Distributed Tracing** mittels OpenTelemetry, das jeden Anfragefluss über Dienste, Agenten und
LLM-Interaktionen hinweg verfolgt. Alle Authentifizierungs- und Autorisierungsereignisse werden lückenlos protokolliert.

Der Swiss AI Hub implementiert eine umfassende Observability-Strategie, die Distributed Tracing, semantische
Konventionen und KI-spezifische Instrumentierung kombiniert. Die Plattform nutzt **OpenTelemetry (OTel)** als
fundamentales Framework, ergänzt durch **OpenInference Semantic Conventions** für KI/ML-Workloads. Dies bedeutet, dass
jede Interaktion – von einer Benutzernachricht bis zu komplexen Multi-Agenten-Orchestrierungen – automatisch mit
umfangreichem Kontext getraced wird, einschliesslich kompletter Anfragenflüsse, KI-spezifischer Semantik (LLM-Aufrufe,
Embeddings, Retrievals) und Performance-Metriken.

### Technische Umsetzung im Swiss AI Hub: OpenTelemetry, SigNoz und Agent-Tracing

Der Swiss AI Hub basiert sein gesamtes Überwachungs- und Alarmierungssystem auf **OpenTelemetry (OTel)**, einem
herstellerneutralen, branchenüblichen Standard. Ein zentraler **OpenTelemetry Collector** empfängt Logs, Metriken und
Traces von allen Diensten, reichert diese mit Metadaten an und exportiert sie sicher an die gewählten Ziele. Dieser
Collector verwendet verschiedene Receiver (OTLP, `docker_stats`, `filelog`), Prozessoren (Batching,
Ressourcen-Erkennung, Attribut-Bearbeitung, Filterung) und Exporter. Die automatische Instrumentierung umfasst NATS
Messaging, Datenbankoperationen (FerretDB, ValKey, Milvus), HTTP-Aufrufe, LLM-Interaktionen, Embeddings und
Retrieval-Operationen, ohne Codeänderungen zu erfordern.

Als offiziell unterstütztes Observability-Backend dient **SigNoz**, eine Open-Source-, OpenTelemetry-native Plattform,
die vereinheitlichte Logs, Metriken und Traces in einer Oberfläche bereitstellt. SigNoz bietet Dashboards für
Infrastruktur, KI-Operationen (Modellnutzung, Token-Verbrauch, Kosten pro Operation), Anwendungsleistung und
Log-Analyse. Flexible Alarmierungsfunktionen können für kritische Dienstausfälle, Leistungsverschlechterung,
Ressourcenlimits, Kostenmanagement und Sicherheitsereignisse konfiguriert und an Kanäle wie E-Mail, Slack oder Microsoft
Teams weitergeleitet werden. Für Produktionsbereitstellungen wird die **Selbst-Hinterlegung von SigNoz auf einer
dedizierten VM** dringend empfohlen, um Leistungsisolation, hohe Verfügbarkeit, Datenhoheit und Netzwerksicherheit zu
gewährleisten. Durch die OTel-Grundlage können Telemetriedaten auch an alternative OTLP-kompatible Backends wie Grafana,
Datadog, Splunk, Prometheus, Elasticsearch/ELK oder New Relic exportiert werden, indem lediglich die
Collector-Konfiguration angepasst wird.

Das Distributed Tracing erfolgt mit spezialisierter Unterstützung für KI-Operationen durch OpenInference Semantic
Conventions. Agentenläufe werden mit hierarchischen Span-Strukturen getraced, die den gesamten Workflow von der
Benutzereingabe bis zur endgültigen Ausgabe abbilden. Der `AgentRunTracer` erstellt hierbei einen Zwei-Span-Ansatz mit
einem initialen AGENT-Span und einem finalen CHAIN-Span. LLM-Aufrufe, Embeddings, Retrieval-Operationen sowie HTTP- und
Datenbankoperationen werden automatisch instrumentiert und in den Traces sichtbar gemacht. Die Phoenix UI
(`http://localhost:6006`) bietet eine spezialisierte LLM-Observability mit Timeline-Ansichten und
Inspektionsmöglichkeiten abgerufener Dokumente während der Entwicklung. Jede Berechtigungsbewertung und Benutzeraktion
generiert detaillierte Audit-Log-Einträge, die dokumentieren, wer wann welche Aktion ausgeführt hat. Diese Audit-Trails
sind entscheidend für Compliance-Berichterstattung und Sicherheitsforensik. Die Log-Aufbewahrung ist konfigurierbar,
wobei ephemere Daten standardmässig nach 30 Tagen gelöscht werden.

## 5. Integriertes Consent-Management und umfassende Compliance-Unterstützung

Die Einhaltung von Datenschutzgesetzen wie dem revDSG und der DSGVO ist für Schweizer Unternehmen nicht verhandelbar.
Eine solide administrative und technische Basis für das Consent-Management und die Unterstützung der Rechte betroffener
Personen ist daher essenziell.

### Mehrwert und Nutzen: Rechtssicherheit, Vertrauen und Schutz der Personenrechte

Eine transparente Handhabung von Nutzer-Einwilligungen und die proaktive Unterstützung der Rechte betroffener Personen
schaffen die notwendige Vertrauensbasis für den Einsatz von KI in sensiblen Bereichen und minimieren rechtliche Risiken.
Dies gewährleistet eine rechtssichere Verwendung der KI durch die Belegschaft und demonstriert ein hohes Mass an
Datenverantwortung. Die technische Unterstützung bei der Umsetzung der Personenrechte entlastet zudem die
administrativen Prozesse im Unternehmen.

### Konzepte & Prozesse: Rechtsgrundlage der Verarbeitung und Personenrechte

Die Plattform unterstützt die Einhaltung der DSGVO-Prinzipien, darunter Rechtmässigkeit, Transparenz (durch Audit-Trails
und Tracing), Zweckbindung, Datenminimierung, Richtigkeit, Speicherbegrenzung (ephemere Daten, konfigurierbare
Aufbewahrungsfristen) sowie Integrität und Vertraulichkeit. Das Consent-Management als Rechtsgrundlage für die
Datenverarbeitung ist primär eine organisatorische Verantwortung des Datenverantwortlichen, die durch die technischen
Funktionen der Plattform unterstützt wird. Die Plattform ist darauf ausgelegt, die Rechte der betroffenen Personen
gemäss DSGVO (Art. 15-21) und revDSG (Art. 25, 32) zu unterstützen, einschliesslich Auskunftsrecht, Recht auf
Berichtigung, Löschung ("Recht auf Vergessenwerden"), Datenübertragbarkeit, Einschränkung der Verarbeitung und
Widerspruchsrecht.

### Technische Umsetzung im Swiss AI Hub: Privacy by Design und DSAR-Support

Der Swiss AI Hub implementiert "Privacy by Design" durch obligatorische TLS/SSL-Verschlüsselung,
Default-Deny-Zugriffskontrolle, automatische 30-Tage-Löschung temporärer Daten und umfassendes Audit-Logging. Die
Plattform bietet APIs für Benutzerprofile, Konversations-Threads und Audit-Logs, um Auskunftsrechten nachzukommen.
Administratoren können Benutzerprofile über die API aktualisieren, um Berichtigungsanfragen zu erfüllen, während
Thread-Nachrichten und Audit-Logs zur Wahrung der Audit-Trails unveränderlich bleiben. Das Entfernen von Nutzern aus
Threads und das Sperren von Konten über RBAC unterstützt das Recht auf Löschung und Einschränkung der Verarbeitung. Das
Recht auf Datenübertragbarkeit gilt für direkt bereitgestellte Daten (Nachrichten, Uploads) in maschinenlesbarem Format.

Obwohl die Plattform keine dedizierte "Consent-UI" bietet, unterstützt sie die organisatorische Verantwortung für das
Consent-Management durch die Bereitstellung notwendiger Audit-Trails und die Einhaltung von Datenschutzprinzipien.
Organisatorisch müssen Unternehmen sicherstellen, dass vor der ersten Interaktion organisationsspezifische Disclaimer
und Nutzungsbedingungen akzeptiert und dokumentiert werden. Im Falle einer Datenschutzverletzung stellt die Plattform
Audit-Protokolle, Benutzerzugriffsberichte und Überwachungsfunktionen bereit, um die fristgerechte Meldung und
Untersuchung zu unterstützen. Das Hosting in der Schweiz, verbunden mit dem EU-Angemessenheitsbeschluss, vereinfacht
zudem die Einhaltung internationaler Datenübermittlungsanforderungen.
