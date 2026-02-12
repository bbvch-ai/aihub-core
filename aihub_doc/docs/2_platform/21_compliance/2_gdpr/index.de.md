---
title: DSGVO-Konformität
source_sha: 3889176abc77e1865cfe855a752cad3902e7cb9313b1edb7e88a2d68d7bf84da
---

# DSGVO-Konformität

Die Plattform bietet technische Maßnahmen zur Unterstützung der DSGVO-Konformität. Organisationen, die die Plattform
nutzen, agieren als Datenverantwortliche und bleiben für ihre eigene Konformität verantwortlich.

## Anwendbarkeit auf Schweizer Organisationen

Die DSGVO gilt für Schweizer Organisationen, wenn sie personenbezogene Daten von Personen in der EU verarbeiten, sofern
sich die Verarbeitung bezieht auf:

- Das Anbieten von Waren oder Dienstleistungen für EU-Bürger (unabhängig von der Bezahlung)
- Die Überwachung des Verhaltens von Personen in der EU

Organisationen müssen die DSGVO-Anforderungen auch ohne EU-Niederlassung einhalten, wenn diese Bedingungen erfüllt sind.

## Rechtsgrundlage für die Verarbeitung

Artikel 6 DSGVO fordert eine Rechtsgrundlage für jede Verarbeitung personenbezogener Daten. Mindestens eine der
folgenden muss zutreffen:

- Einwilligung: Die betroffene Person hat eine klare Einwilligung für bestimmte Zwecke erteilt
- Vertrag: Die Verarbeitung ist für die Vertragserfüllung oder vorvertragliche Maßnahmen erforderlich
- Rechtliche Verpflichtung: Die Verarbeitung ist zur Einhaltung gesetzlicher Anforderungen erforderlich
- Lebenswichtige Interessen: Die Verarbeitung ist zum Schutz des Lebens oder der körperlichen Unversehrtheit
  erforderlich
- Öffentliche Aufgabe: Die Verarbeitung ist für Aufgaben im öffentlichen Interesse oder die Ausübung öffentlicher Gewalt
  erforderlich
- Berechtigte Interessen: Die Verarbeitung ist für berechtigte Interessen erforderlich, es sei denn, diese werden durch
  die Rechte der betroffenen Person überlagert (nicht verfügbar für öffentliche Behörden)

Organisationen müssen ihre Rechtsgrundlage dokumentieren und die betroffenen Personen entsprechend informieren.

## DSGVO-Prinzipien

Artikel 5 DSGVO legt sechs Kernprinzipien für die Verarbeitung personenbezogener Daten sowie eine Rechenschaftspflicht
fest:

### Rechtmäßigkeit, Fairness und Transparenz

Die Plattform bietet Audit-Trails, Quellenzuordnung und Langfuse-Tracing für Transparenz. Organisationen müssen ihre
Rechtsgrundlage für die Verarbeitung dokumentieren, Datenschutzhinweise bereitstellen, Verzeichnisse der
Verarbeitungstätigkeiten führen und Datenschutz-Folgenabschätzungen durchführen. Die Verarbeitung muss rechtmäßig, fair
und für die betroffenen Personen transparent sein.

### Zweckbindung

Daten müssen für festgelegte, eindeutige und legitime Zwecke erhoben und nicht in einer mit diesen Zwecken unvereinbaren
Weise weiterverarbeitet werden. Organisationen sollten klare Zwecke für jede Datenerhebungs- und -verarbeitungsaktivität
definieren.

### Datenminimierung

Multi-Mandanten-Isolation, rollenbasierte Zugriffskontrolle und Namespace-Isolation beschränken den Datenzugriff auf das
Notwendige. Die erhobenen Daten müssen angemessen, relevant und auf das für die definierten Zwecke notwendige Maß
beschränkt sein.

### Richtigkeit

Die Versionskontrolle verfolgt Datenänderungen, um die Richtigkeit zu gewährleisten. Organisationen müssen
sicherstellen, dass personenbezogene Daten richtig und, wo nötig, auf dem neuesten Stand gehalten werden. Unrichtige
Daten müssen unverzüglich gelöscht oder berichtigt werden.

### Speicherbegrenzung

Ephemere Daten verfallen automatisch nach 30 Tagen. Organisationen konfigurieren Aufbewahrungsfristen für die dauerhafte
Speicherung. Daten dürfen nicht länger in einer Form gespeichert werden, die die Identifizierung der betroffenen
Personen ermöglicht, als es für die Verarbeitungszwecke erforderlich ist.

### Integrität und Vertraulichkeit

Die Plattform erfordert TLS/SSL-Verschlüsselung und unterstützt OAuth-, OIDC- und SAML-Authentifizierung. Rollenbasierte
Zugriffskontrolle, Container-Sicherheit und Eingabevalidierung schützen die Datenintegrität. Die Verarbeitung muss eine
angemessene Sicherheit gewährleisten, einschließlich des Schutzes vor unbefugter oder unrechtmäßiger Verarbeitung und
vor versehentlichem Verlust, Zerstörung oder Beschädigung.

### Rechenschaftspflicht

Verantwortliche müssen in der Lage sein, die Einhaltung aller Prinzipien nachzuweisen. Die Plattform unterstützt dies
durch umfassende Audit-Protokollierung, Dokumentationsfunktionen und Nachverfolgbarkeitsfunktionen.

## Rechte der betroffenen Personen

### Auskunftsrecht (Art. 15)

Benutzer können Kopien ihrer personenbezogenen Daten, Verarbeitungsdetails, Empfänger, Aufbewahrungsfristen und
Datenquellen anfordern. Die Plattform bietet eine Benutzerprofil-API und Zugriff auf Audit-Logs.

### Recht auf Berichtigung (Art. 16)

Benutzer können die Berichtigung unrichtiger Daten verlangen. Administratoren können Benutzerprofile über die API
aktualisieren. Thread-Nachrichten und Audit-Logs bleiben unveränderlich, um Audit-Trails zu erhalten.

### Recht auf Löschung (Art. 17)

Benutzer können die Löschung von Daten verlangen, wenn diese nicht mehr erforderlich sind, die Einwilligung widerrufen
wird oder die Verarbeitung unrechtmäßig ist. Die Plattform unterstützt das Entfernen von Benutzern aus Threads, und
ephemere Daten werden nach 30 Tagen automatisch gelöscht.

Ausnahmen gelten, wenn die Verarbeitung notwendig ist für:

- Die Freiheit der Meinungsäußerung und Information
- Die Erfüllung einer rechtlichen Verpflichtung oder die Wahrnehmung einer Aufgabe im öffentlichen Interesse
- Gründe des öffentlichen Interesses im Bereich der öffentlichen Gesundheit
- Archivierungs-, wissenschaftliche oder historische Forschungszwecke oder statistische Zwecke (wenn die Löschung diese
  unmöglich machen oder ernsthaft beeinträchtigen würde)
- Die Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen

### Recht auf Datenübertragbarkeit (Art. 20)

Benutzer können ihre Daten in maschinenlesbarem Format anfordern. Dies gilt für Daten, die der Benutzer direkt
bereitgestellt hat (Nachrichten, Uploads), nicht für KI-generierte Antworten, Analysen oder abgeleitete Daten. Das Recht
gilt nur, wenn die Verarbeitung auf einer Einwilligung oder einem Vertrag basiert und durch automatisierte Verfahren
erfolgt.

### Recht auf Einschränkung der Verarbeitung (Art. 18)

Benutzer können die Aussetzung der Verarbeitung verlangen, während die Richtigkeit der Daten überprüft oder Widersprüche
beurteilt werden. Administratoren können Konten über die rollenbasierte Zugriffskontrolle sperren.

### Widerspruchsrecht (Art. 21)

Benutzer können der Verarbeitung aufgrund berechtigter Interessen widersprechen. Der Widerruf der Berechtigung über die
rollenbasierte Zugriffskontrolle beendet die Verarbeitung.

## Technische Maßnahmen

Die Plattform implementiert Datenschutz durch Technikgestaltung (Privacy by Design) mit obligatorischer
TLS/SSL-Verschlüsselung, standardmäßig verweigernder Zugriffskontrolle, automatischer Audit-Protokollierung,
automatischer Löschung ephemerer Daten nach 30 Tagen und minimaler Datenerfassung. Weitere Details finden Sie unter
[Authentifizierung](/de/docs/20_security/1_authentication/), [Verschlüsselung](/de/docs/20_security/5_data_encryption/)
und [Zugriffskontrolle](/de/docs/11_access_management/).

## Internationale Datenübermittlungen

### Angemessenheitsbeschluss der EU für die Schweiz

Die Schweiz hat einen Angemessenheitsbeschluss der EU (im Januar 2024 bestätigt), was bedeutet, dass die Europäische
Kommission das Schweizer Datenschutzrecht als ein angemessenes Schutzniveau anerkennnt. Dies ermöglicht den freien Fluss
personenbezogener Daten von der EU in die Schweiz ohne zusätzliche Garantien.

Für Organisationen, die in der Schweiz hosten, vereinfacht dies die Einhaltung sowohl der DSGVO- als auch der Schweizer
DSG-Anforderungen. Hosting-Konfigurationen finden Sie unter
[Deployment-Optionen](/de/docs/3_deployment_guide/1_deployment_options/).

### Übermittlungen in andere Länder

Übermittlungen in Länder ohne Angemessenheitsbeschluss erfordern geeignete Garantien:

- Von der Europäischen Kommission genehmigte Standardvertragsklauseln (SCCs)
- Verbindliche interne Datenschutzvorschriften (BCRs)
- Genehmigte Verhaltensregeln oder Zertifizierungsmechanismen
- Spezifische Ausnahmen (Einwilligung, Vertragserfüllung, lebenswichtige Interessen usw.)

## Meldung von Datenschutzverletzungen

Artikel 33 DSGVO schreibt vor, die Aufsichtsbehörde **unverzüglich und möglichst binnen 72 Stunden**, nachdem die
Organisation Kenntnis von einer Verletzung erlangt hat, zu benachrichtigen, wenn diese voraussichtlich zu einem Risiko
für die Rechte und Freiheiten natürlicher Personen führt. Erfolgt die Benachrichtigung nicht innerhalb von 72 Stunden,
müssen die Gründe für die Verzögerung angegeben werden. Eine Benachrichtigung ist nicht erforderlich, wenn die
Verletzung voraussichtlich nicht zu einem Risiko führt.

Die Benachrichtigung muss die Art der Verletzung, die betroffenen Personen, die wahrscheinlichen Folgen und die
ergriffenen Abhilfemaßnahmen enthalten. Betroffene Personen müssen direkt informiert werden (Artikel 34), wenn die
Verletzung voraussichtlich zu einem hohen Risiko für ihre Rechte und Freiheiten führt.

Die Plattform bietet Audit-Logs, Berichte über Benutzerzugriffe, Überwachungs-, Alarmierungs- und Sicherungsfunktionen
zur Unterstützung der Untersuchung, Dokumentation und Reaktion auf Verletzungen.

## Verwandte Dokumentation

- [Schweizer DSG](../3_dsg/)
- [DSAR-Verfahren](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [DSGVO Volltext](https://gdpr-info.eu/)
- [EDPB Leitlinien](https://edpb.europa.eu/)

---

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie Ihren Datenschutzbeauftragten oder
Rechtsbeistand.
:::
