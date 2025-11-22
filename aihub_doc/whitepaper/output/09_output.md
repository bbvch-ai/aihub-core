# Kapitel 09: Regulatorische Compliance

Die erfolgreiche Implementierung von Künstlicher Intelligenz (KI) in Schweizer Unternehmen ist untrennbar mit der
Einhaltung strenger regulatorischer Vorgaben verbunden. Von nationalen Datenschutzgesetzen wie dem revidierten Schweizer
Datenschutzgesetz (revDSG) über die europäische Datenschutz-Grundverordnung (DSGVO) bis hin zu kommenden Regelwerken wie
dem EU KI-Gesetz – die Forderung nach Datensouveränität, Transparenz und Rechenschaftspflicht steigt stetig. Dieses
Kapitel beleuchtet, wie der Swiss AI Hub durch integrierte funktionale Mechanismen eine robuste Basis für Compliance
schafft, rechtliche Risiken minimiert und Unternehmen dabei unterstützt, KI verantwortungsvoll und gesetzeskonform
einzusetzen.

## 1. Souveräne Datenhaltung für Schweizer Compliance

Die Sicherstellung, dass sensible Unternehmensdaten die Schweiz nicht verlassen, ist für viele Organisationen von
fundamentaler Bedeutung, um den Anforderungen des revDSG und der DSGVO gerecht zu werden. Der Swiss AI Hub gewährleistet
dies durch flexible und datensouveräne Bereitstellungsmodelle, die eine harte Datenisolation ermöglichen.

### Mehrwert und Nutzen: Garantierte Datenresidenz und minimiertes Compliance-Risiko

Für C-Level-Führungskräfte bedeutet dies die Gewissheit, dass Daten stets im kontrollierten Hoheitsgebiet verbleiben,
was Compliance-Risiken erheblich reduziert und das Vertrauen in KI-gestützte Prozesse stärkt. Insbesondere für
öffentliche Institutionen ist dies entscheidend, um gesetzliche Vorgaben zur Datenhaltung lückenlos zu erfüllen.
IT-Professionals profitieren von klaren Deployment-Optionen, die eine Architektur ohne Datentransfers in unsichere
Drittstaaten ermöglichen, was den administrativen Aufwand für die Einhaltung internationaler
Datenübermittlungsbestimmungen eliminiert. Selbst bei der optionalen Nutzung gemeinsam genutzter LLM-Ressourcen bleiben
sensible Prompts und Responses unter der Kontrolle der Organisation.

### Konzepte & Prozesse: Isolierte Betriebsmodelle und lokale Kontrolle

Der Swiss AI Hub ist primär für Einzelinstanz-Deployments konzipiert (Multi-Instancing), die jede Organisation mit einer
vollständigen, isolierten Instanz ausstatten. Dieses Design verhindert einen ungewollten Datenaustausch zwischen
Organisationen und ermöglicht die volle Kontrolle über die physische Speicherung und Verarbeitung der Daten. Selbst wenn
mehrere solcher isolierten Instanzen optional Backend-LLM-Ressourcen oder Authentifizierungsinfrastrukturen teilen, sind
die gemeinsam genutzten LLM-Backends stets zustandslos und persistieren keine Prompts oder Responses. Der gesamte
Konversationskontext und die Historie verbleiben innerhalb der Infrastruktur jeder einzelnen Instanz. Das System
unterstützt zudem Air-Gapped-Operationen, bei denen die Plattform vollständig vom Internet isoliert betrieben werden
kann, wenn lokal gehostete Sprachmodelle (LLMs) verwendet werden. Die Schweiz verfügt über einen
EU-Angemessenheitsbeschluss, der den freien Fluss personenbezogener Daten von der EU in die Schweiz ohne zusätzliche
Schutzmassnahmen erlaubt und somit die Compliance weiter vereinfacht.

### Technische Umsetzung im Swiss AI Hub: Flexible Hosting-Optionen und Air-Gap-Fähigkeit

Organisationen können den Swiss AI Hub auf ihren eigenen Servern **On-Premise** betreiben, wodurch die gesamte
Infrastruktur unter ihrer Kontrolle liegt und ein Air-Gapped-Betrieb ermöglicht wird. Alternativ kann die Plattform in
der **eigenen Private Cloud** des Kunden gehostet werden, mit der Option, spezifische Schweizer Regionen für die
Datenresidenz zu wählen. Als dritte Option bietet die bbv **SaaS (Schweizer Cloud-Hosting)** an, bei dem der AI Hub auf
einer Schweizer Cloud-Infrastruktur verwaltet wird, wobei die Daten stets in der Schweiz und unter Schweizer
Rechtshoheit verbleiben. Jede Instanz verfügt über einen vollständigen Stack mit eigenen Anwendungsdiensten, Datenbanken
(FerretDB/PostgreSQL), Vektor-Stores (Milvus oder Azure AI Search) und Dateispeichern (SeaweedFS oder Azure Data Lake),
wodurch die Datenisolation strikt umgesetzt wird. Der eigene LiteLLM-Proxy jeder Instanz handhabt dabei die
Modellauswahl, Budgets, Ratenbegrenzungen und Versionen. LLM-Anfragen werden vom LiteLLM-Proxy mit einer Instanz-ID,
aber ohne Prompt-Inhalt protokolliert, bevor sie optional an geteilte, zustandslose LLM-Backends weitergeleitet werden.

## 2. "Privacy by Design" und Rechte der betroffenen Personen

Eine datenschutzkonforme KI-Plattform muss Datenschutzprinzipien bereits im Systemkern verankern und effiziente
Mechanismen zur Wahrung der Betroffenenrechte bereitstellen. Der Swiss AI Hub wurde nach den Grundsätzen von "Privacy by
Design" entwickelt.

### Mehrwert und Nutzen: Regulatorische Sicherheit und effiziente DSAR-Bearbeitung

Diese Integration schafft für C-Level-Führungskräfte die notwendige Rechtssicherheit, um KI-Anwendungen auch in
datensensiblen Bereichen rechtskonform (revDSG, DSGVO) und vertrauenswürdig einzusetzen. IT-Teams profitieren von
standardisierten Workflows und APIs, die die Bearbeitung von Betroffenenrechten – wie Auskunftsersuchen (DSAR) oder das
"Recht auf Vergessenwerden" – effizient und fristgerecht ermöglichen und den administrativen Aufwand minimieren.

### Konzepte & Prozesse: DSGVO-Prinzipien und DSAR-Verfahren

Die Plattform unterstützt die Einhaltung der zentralen Datenschutzprinzipien wie Rechtmässigkeit, Fairness, Transparenz
(durch Audit-Trails und Tracing), Zweckbindung, Datenminimierung (durch RBAC und Namespace-Isolation), Richtigkeit,
Speicherbegrenzung und Integrität/Vertraulichkeit. Für Schweizer Organisationen ist dies massgebend, da das revDSG
explizit "Privacy by Design" fordert. Das Consent-Management als Rechtsgrundlage für die Datenverarbeitung ist primär
eine organisatorische Verantwortung, die durch die technischen Funktionen der Plattform unterstützt wird.
Betroffenenrechte wie Auskunftsrecht (Art. 15 DSGVO / Art. 25 revDSG), Berichtigung, Löschung ("Recht auf
Vergessenwerden", Art. 17 DSGVO / Art. 32 revDSG) und Datenübertragbarkeit (Art. 20 DSGVO / Art. 28 revDSG) werden
umfassend unterstützt.

### Technische Umsetzung im Swiss AI Hub: Technische Schutzmassnahmen und API-Unterstützung

Der Swiss AI Hub implementiert "Privacy by Design" durch obligatorische TLS/SSL-Verschlüsselung,
Default-Deny-Zugriffskontrolle und automatische 30-Tage-Löschung temporärer Daten. Für Auskunftsersuchen bietet die
Plattform APIs für Benutzerprofile, Konversations-Threads und Audit-Logs. Administratoren können Benutzerprofile zur
Berichtigung aktualisieren; Thread-Nachrichten und Audit-Logs bleiben zur Wahrung der Integrität unveränderlich. Das
Recht auf Löschung wird durch die Möglichkeit unterstützt, Nutzer aus Threads zu entfernen und ephemere Daten nach 30
Tagen automatisch zu löschen. Die Datenübertragbarkeit gilt für direkt bereitgestellte Daten in maschinenlesbarem
Format. Das Verhindern von unautorisiertem Datenabfluss wird zudem durch die optionale PII-Anonymisierung mittels
Presidio unterstützt, bevor Daten externe LLMs erreichen.

## 3. Vorbereitung auf das EU KI-Gesetz (AI Act) und ethische KI-Verarbeitung

Das EU KI-Gesetz wird die regulatorische Landschaft für KI-Systeme grundlegend verändern. Der Swiss AI Hub integriert
Mechanismen, die auf diese kommenden Anforderungen ausgerichtet sind, um langfristige Konformität zu gewährleisten.

### Mehrwert und Nutzen: Zukunftsfähigkeit und ethisches Vertrauen

Für Führungskräfte sichert die Plattform die Zukunftsfähigkeit von KI-Investitionen, indem sie proaktiv auf neue
Regulierungen vorbereitet ist. Dies minimiert rechtliche Unsicherheiten und fördert das Vertrauen in den ethischen und
verantwortungsvollen Einsatz von KI im Unternehmen. IT-Teams erhalten die technischen Werkzeuge zur Implementierung von
Transparenz, Risikobewertung und menschlicher Aufsicht, die für den Einsatz in sensiblen oder risikobehafteten Kontexten
unerlässlich sind.

### Konzepte & Prozesse: Risikobasierter Ansatz und menschliche Aufsicht

Das KI-Gesetz klassifiziert Systeme nach ihrem Risiko. Die meisten Anwendungsfälle des Swiss AI Hub fallen in die
Kategorien "begrenzten" oder "minimalen Risikos", wobei Hochrisiko-Systeme (z.B. in Beschäftigung oder Bildung)
strengere Anforderungen haben. Die Plattform adressiert diese Anforderungen durch die Verankerung von
Transparenzmechanismen und zwingende menschliche Aufsicht (Human-in-the-Loop). Für das Hochrisikoprofiling, wie es das
revDSG fordert, sind diese Funktionen ebenfalls entscheidend, um menschliche Überprüfung und Nachvollziehbarkeit
sicherzustellen. Die Plattform operationalisiert Prinzipien für "Responsible AI" durch die Bereitstellung von Kontroll-
und Nachvollziehbarkeitsmechanismen, die die Erkennung und Minderung von algorithmischen Verzerrungen (Bias)
unterstützen.

### Technische Umsetzung im Swiss AI Hub: Transparenzfunktionen und Human-in-the-Loop

Der Swiss AI Hub bietet umfassende technische Massnahmen, die die Compliance mit dem EU KI-Gesetz unterstützen. Dazu
gehören detaillierte Audit-Protokolle und lückenlose Rückverfolgbarkeit (siehe auch Kapitel 04). Die Phoenix-Tracing-UI
ermöglicht eine tiefgehende Analyse der KI-Entscheidungsketten und der Quellenzuordnung für KI-Ausgaben.
Human-in-the-Loop-Funktionen sind fest in die Agenten-Workflows integriert (siehe Kapitel 04), um menschliches
Urteilsvermögen und Eingreifen bei kritischen Entscheidungen zu ermöglichen. Dies trägt zur Sicherstellung von
Genauigkeit und Robustheit bei und ist ein wesentlicher Mechanismus gegen AI-Bias, da menschliche Prüfer potenziell
problematische Ergebnisse identifizieren und korrigieren können.

## 4. Rechenschaftspflicht, Audit-Trails und Datenlebenszyklus

Die Fähigkeit, die Einhaltung regulatorischer Anforderungen nachzuweisen, ist für Unternehmen unerlässlich. Der Swiss AI
Hub unterstützt eine umfassende Rechenschaftspflicht durch detaillierte Audit-Trails und ein konfiguriertes
Datenlebenszyklus-Management.

### Mehrwert und Nutzen: Revisionssichere Nachweise und minimierte Aufbewahrungsrisiken

Für Führungskräfte gewährleistet dies die Fähigkeit, Datenschutz-Folgenabschätzungen (DPIA) effektiv zu erstellen und
gegenüber Aufsichtsbehörden rechtssichere Nachweise der Compliance zu erbringen. Die klare Definition von
Datenaufbewahrungsfristen minimiert zudem langfristige Speicher- und Haftungsrisiken. IT-Teams profitieren von
automatisierten Prozessen für die Datenlöschung und umfassenden Audit-Funktionen, die die forensische Analyse bei
Sicherheitsvorfällen erleichtern und den administrativen Aufwand reduzieren. Die transparente Verfolgung der LLM-Nutzung
pro Instanz und Benutzer ermöglicht eine genaue Kosten- und Verantwortlichkeitszuweisung.

### Konzepte & Prozesse: Rechenschaftspflicht gemäss DSGVO und gestaffelte Aufbewahrung

Die Plattform unterstützt das DSGVO-Prinzip der Rechenschaftspflicht (Artikel 5), indem sie umfassende
Audit-Protokollierung und Nachverfolgbarkeit bietet. Dies ist entscheidend für die Meldung von Datenschutzverletzungen
(Art. 33 DSGVO / Art. 24 revDSG). Die Datenaufbewahrungsstrategie ist gestaffelt: Ephemere Daten und Workflow-Ereignisse
werden nach 30 Tagen automatisch gelöscht, während für den permanenten NoSQL-Speicher Organisationen eigene
Lifecycle-Richtlinien definieren. Die Plattform unterstützt zudem das manuelle Löschen von Benutzerdaten und die
ordnungsgemässe Datenlöschung bei Kontolöschung durch Funktionen wie das Entfernen von Nutzern aus Threads. Die
LLM-Nutzung wird pro Instanz verfolgt, was eine detaillierte Zuordnung von Token-Verbrauch und Kosten ermöglicht.

### Technische Umsetzung im Swiss AI Hub: Audit-Logs, Observability und Lifecycle-Richtlinien

Umfassende Audit-Logs (siehe Kapitel 04) dokumentieren jede Benutzeraktion und jede Berechtigungsbewertung und bieten
die Grundlage für Compliance-Nachweise. Die integrierte Observability mit OpenTelemetry und SigNoz ermöglicht Monitoring
und Alarmierung bei sicherheitsrelevanten Ereignissen oder ungewöhnlichem Datenfluss, was die Unterstützung für die
Meldung von Datenschutzverletzungen stärkt. Ephemere Daten im Redis-Cache und Workflow-Ereignisse in NATS JetStream
werden nach 30 Tagen automatisch gelöscht, um Speicherbegrenzung zu gewährleisten. Für permanent gespeicherte Daten
müssen Organisationen explizite Daten-Lifecycle-Richtlinien implementieren, um die Datenaufbewahrung gemäss ihren
regulativen und geschäftlichen Anforderungen zu steuern. Die API-Nutzung von LLMs wird vom LiteLLM-Proxy pro Instanz und
Benutzer (Token-Anzahl, Modellnutzung, Kostenberechnungen, Budgeteinhaltung) verfolgt und ist über die LiteLLM-Admin-UI
oder für die Abrechnung exportierbar.

## 5. Mehrsprachigkeit und Internationalisierung

Die Schweiz ist ein mehrsprachiges Land. Eine KI-Plattform, die Schweizer Unternehmen dient, muss diese sprachliche
Vielfalt vollumfänglich unterstützen.

### Mehrwert und Nutzen: Breite Akzeptanz und vereinfachte Einführung

Für C-Level-Führungskräfte bedeutet die umfassende Mehrsprachigkeit eine breitere Akzeptanz der Plattform in allen
Schweizer Sprachregionen, was die Benutzerfreundlichkeit erhöht und die Einführung von KI-Lösungen beschleunigt.
Insbesondere für Schweizer Institutionen des öffentlichen Sektors ist die Bereitstellung von Dienstleistungen in
mehreren Landessprachen eine Grundvoraussetzung, die ohne kundenspezifische Entwicklung erfüllt wird. IT-Teams
profitieren von einer einheitlichen Plattforminstanz, die für verschiedene Sprachgemeinschaften nutzbar ist.

### Konzepte & Prozesse: Vier Landessprachen und dynamische Anpassung

Die Plattform unterstützt die vier Landessprachen der Schweiz: Deutsch, Englisch, Französisch und Italienisch. Die
Benutzeroberfläche, Fehlermeldungen, Hilfetexte und Navigation sind vollständig übersetzt. Benutzer können ihre
bevorzugte Sprache wählen, die über Sitzungen hinweg bestehen bleibt. Dynamisch generierte Inhalte wie
Dienstleistungsbeschreibungen und Agentennamen passen sich ebenfalls an die gewählte Sprache an. Die Plattform kann
zudem die Dokumentsprache für die Verarbeitung und das Wissensmanagement automatisch erkennen, was sprachspezifische
Suchoptimierung ermöglicht.

### Technische Umsetzung im Swiss AI Hub: Übersetzungsarchitektur und Lokalisierung

Alle benutzernahen Texte sind übersetzt, wobei Deutsch als Standardsprache dient, falls eine Übersetzung fehlt. Die
Übersetzungsqualität wird durch konsistente Terminologie gewährleistet. Benutzerdefinierte Ressourcen wie
Wissens-Namespaces können Übersetzungen für alle unterstützten Sprachen enthalten. Zahlen, Daten, Zeiten und Währungen
werden gemäss den regionalen Konventionen formatiert. Die Suchfunktionalität verwendet sprachspezifische Tokenisierung
und Stemming, um präzise Ergebnisse in jeder Sprache zu liefern. Organisationen können zudem benutzerdefinierte
Übersetzungen für unternehmensspezifische Begriffe hinzufügen, was die Anpassbarkeit an individuelle Bedürfnisse
sicherstellt. Die Plattform ermöglicht somit die Verarbeitung mehrsprachiger Dokumente und bietet
Compliance-Dokumentation sowie Benutzeroberflächen in den Schweizer Landessprachen.
