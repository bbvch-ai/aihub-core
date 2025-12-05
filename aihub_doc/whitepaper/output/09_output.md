# Kapitel 09: Regulatorische Compliance

## Rechtssicherheit als Fundament der KI-Strategie

Für Schweizer Unternehmen und öffentliche Institutionen ist die Einhaltung gesetzlicher Vorgaben keine optionale
Checkliste, sondern die Lizenz zum Betrieb. Mit dem Inkrafttreten des revidierten Schweizer Datenschutzgesetzes (revDSG)
und der omnipräsenten Wirkung der europäischen Datenschutz-Grundverordnung (DSGVO) stehen Organisationen unter massivem
Druck. Der Einsatz generativer KI verschärft diese Situation: Wie kann gewährleistet werden, dass keine Personendaten in
intransparente Cloud-Modelle abfliessen oder Aufbewahrungsfristen verletzt werden?

Der Swiss AI Hub begegnet dieser Herausforderung nicht mit nachträglichen Anpassungen, sondern mit einer Architektur,
die Compliance «by Design» erzwingt. Die Plattform transformiert regulatorische Anforderungen von abstrakten
Gesetzestexten in harte technische Leitplanken. Dies ermöglicht es Datenschutzverantwortlichen, den Einsatz modernster
KI-Technologie zu genehmigen, ohne rechtliche Risiken einzugehen.

## Territoriale Konformität und Infrastruktur-Isolation

### Physische Trennung und Schweizer Datenhaltung

Ein Kernproblem bei der Nutzung globaler SaaS-Lösungen ist die Diskrepanz zwischen vertraglicher Zusicherung und
technischer Realität. Während Nutzungsbedingungen oft Datenresidenz versprechen, teilen sich Kunden in der Praxis häufig
Datenbanken (Multi-Tenancy). Für streng regulierte Bereiche ist dies unzureichend.

Der Swiss AI Hub unterstützt daher ein konsequentes **Multi-Instanz-Deployment**. In diesem Modell betreibt eine
Organisation mehrere vollständig isolierte Instanzen der Plattform. Jede Instanz verfügt über eine eigene, dedizierte
Infrastruktur: Separate Datenbanken (PostgreSQL/FerretDB), eigene Vektor-Speicher (Milvus) und getrennte Dateisysteme.
Ein Datenübertritt zwischen Mandanten ist technisch ausgeschlossen. Da die Schweiz über einen bestätigten
EU-Angemessenheitsbeschluss verfügt (bestätigt im Januar 2024), vereinfacht das Hosting in der Schweiz zudem die
Einhaltung der DSGVO-Anforderungen für den grenzüberschreitenden Datenverkehr erheblich, da ein freier Datenfluss ohne
zusätzliche komplexe Schutzmassnahmen möglich ist.

Für Szenarien mit höchsten Geheimhaltungsstufen bietet die Plattform zudem die Option eines **Air-Gapped-Betriebs**.
Hierbei werden lokale LLMs (wie vLLM oder llama.cpp) direkt auf der eigenen Infrastruktur ohne Internetverbindung
ausgeführt, womit der Datenabfluss in Drittstaaten physikalisch unterbunden wird.

## Privacy by Design und Datenlebenszyklus

### Betroffenenrechte und DSAR-Prozesse

Sowohl das revDSG als auch die DSGVO (Art. 15-21) garantieren Betroffenen umfangreiche Rechte, darunter Auskunft,
Berichtigung und Löschung. Die technische Umsetzung dieser Rechte in Vektordatenbanken ist komplex. Der Swiss AI Hub
stellt hierfür spezialisierte APIs bereit, die Administratoren befähigen, Anfragen von betroffenen Personen (DSAR)
effizient zu bearbeiten. Über Benutzerprofil-APIs können alle gespeicherten Daten – einschliesslich
Verarbeitungsdetails, Empfänger und Datenquellen – exportiert oder korrigiert werden. Wichtig ist dabei die
Unterscheidung: Das Recht auf Datenübertragbarkeit gilt für direkt bereitgestellte Daten (Uploads, Nachrichten), nicht
jedoch für rein KI-generierte Analysen.

### Gestaffelte Aufbewahrungsstrategie (Retention)

Um das Prinzip der Speicherbegrenzung technisch durchzusetzen, implementiert die Plattform eine duale
Aufbewahrungsstrategie:

- **Ephemere Daten (Automatische Löschung):** Temporäre Verarbeitungsdaten, wie Caches in Redis oder Workflow-Ereignisse
  in NATS JetStream, unterliegen einem harten Limit. Sie werden automatisch nach einem fixen 30-Tage-Fenster gelöscht.
  Dies verhindert die Entstehung von «Datenfriedhöfen» und stellt sicher, dass Debugging-Informationen nicht zu einer
  dauerhaften Compliance-Last werden.
- **Permanente Daten (Kontrolliertes Lifecycle-Management):** Für den dauerhaften Speicher (Vektordatenbanken,
  Chat-Historie) bietet die Plattform keine pauschale Löschung, sondern granulare Kontrolle. Organisationen können über
  die API eigene Löschfristen definieren und durchsetzen, um geschäftliche Aufbewahrungspflichten mit dem Recht auf
  Vergessenwerden in Einklang zu bringen.

## Vorbereitung auf den EU AI Act und ethische KI

### Transparenz und Risiko-Klassifizierung

Kommende Regulierungen wie der EU AI Act klassifizieren KI-Systeme nach ihrem Risiko. Während die meisten
Anwendungsfälle der Plattform in die Kategorien «begrenztes Risiko» oder «minimales Risiko» fallen, fordert der
Gesetzgeber Transparenz. Es muss nachvollziehbar sein, dass ein Nutzer mit einer KI interagiert und auf welcher Basis
Entscheidungen getroffen wurden.

Die Architektur des Swiss AI Hubs liefert diese Datenströme standardmässig. Durch die Integration von OpenTelemetry und
Tracing-Tools (Phoenix) wird jede Interaktion aufgezeichnet. Diese Logs enthalten die verwendeten Modellversionen,
System-Prompts und abgerufenen Wissensquellen («Quellenzuordnung»). Dies ermöglicht die Erstellung automatisierter
Compliance-Reports, wie sie für Datenschutz-Folgenabschätzungen oder Hochrisikoprofiling-Analysen erforderlich sind.

Ein zentrales Element ethischer KI ist zudem die menschliche Aufsicht («Human Oversight»). Die Plattform unterstützt
dies durch prozessuale Unterbrechungen (**Human-in-the-Loop**), bei denen ein Agent eine explizite Freigabe durch einen
autorisierten Benutzer anfordert, bevor eine kritische Aktion ausgeführt wird.

## Inklusion und nationale Sprachkonformität

Für Schweizer Behörden und öffentliche Institutionen ist die Unterstützung der Landessprachen eine zwingende
Compliance-Anforderung, um Diskriminierung zu vermeiden. Der Swiss AI Hub ist vollständig internationalisiert und
unterstützt Deutsch, Französisch, Italienisch und Englisch.

Dies betrifft nicht nur die Übersetzung der Benutzeroberfläche, sondern die tiefe Datenverarbeitung. Die
Suchfunktionalität verwendet sprachspezifische Tokenisierung, um Dokumente in allen Landessprachen korrekt zu indizieren
und aufzufinden (Stemming). Dynamische Inhalte wie Fehlermeldungen, Agenten-Namen oder Beschreibungen von
Wissens-Namespaces passen sich der gewählten Sprache des Nutzers an. Damit stellt die Plattform sicher, dass gesetzliche
Vorgaben zur Mehrsprachigkeit im Bürger- und Behördendialog technisch abgebildet sind.

## Fazit: Compliance als technischer Standard

Der Swiss AI Hub hebt die Compliance von einer organisatorischen Bürde auf ein technisches Leistungsmerkmal. Durch die
Kombination von harter Infrastruktur-Isolation, automatisierten Löschroutinen für ephemere Daten, mehrsprachiger
Architektur und lückenloser Auditierbarkeit erhalten Schweizer Organisationen ein Werkzeug, das Rechtssicherheit nicht
nur verspricht, sondern technisch durchsetzt.
