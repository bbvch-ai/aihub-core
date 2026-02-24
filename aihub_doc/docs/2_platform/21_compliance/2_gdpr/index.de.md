---
title: DSGVO-Konformität
source_sha: 1b294315160818e2f2d4b7ec0b078132f39026819ef1983041e5827c948b4de9
---

# DSGVO-Konformität

Die Plattform bietet technische Maßnahmen zur Unterstützung der DSGVO-Konformität. Organisationen, die die Plattform
nutzen, agieren als Datenverantwortliche und bleiben für ihre eigene Konformität verantwortlich.

## Anwendbarkeit auf Schweizer Organisationen

Die DSGVO gilt für Schweizer Organisationen, wenn sie personenbezogene Daten von Personen in der EU verarbeiten, sofern
die Verarbeitung sich bezieht auf:

- Das Anbieten von Waren oder Dienstleistungen für EU-Bürger (unabhängig von der Bezahlung)
- Die Beobachtung des Verhaltens von Personen in der EU

Organisationen müssen die DSGVO-Anforderungen auch ohne EU-Niederlassung erfüllen, wenn diese Bedingungen zutreffen.

## Rechtsgrundlage für die Verarbeitung

Artikel 6 DSGVO erfordert eine Rechtsgrundlage für jede Verarbeitung personenbezogener Daten. Mindestens eine der
folgenden muss zutreffen:

- **Einwilligung**: Die betroffene Person hat eine klare Einwilligung für bestimmte Zwecke erteilt
- **Vertrag**: Die Verarbeitung ist für die Erfüllung eines Vertrags oder vorvertragliche Maßnahmen erforderlich
- **Rechtliche Verpflichtung**: Die Verarbeitung ist zur Einhaltung gesetzlicher Vorschriften erforderlich
- **Lebenswichtige Interessen**: Die Verarbeitung ist zum Schutz von Leben oder körperlicher Unversehrtheit erforderlich
- **Öffentliche Aufgabe**: Die Verarbeitung ist für Aufgaben im öffentlichen Interesse oder die Ausübung öffentlicher
  Gewalt erforderlich
- **Berechtigte Interessen**: Die Verarbeitung ist für berechtigte Interessen erforderlich, es sei denn, diese werden
  durch die Rechte der betroffenen Person überlagert (nicht verfügbar für Behörden)

Organisationen müssen ihre Rechtsgrundlage dokumentieren und die betroffenen Personen entsprechend informieren.

## DSGVO-Grundsätze

Artikel 5 DSGVO legt sechs Kernprinzipien für die Verarbeitung personenbezogener Daten fest, zuzüglich einer
Rechenschaftspflicht:

### Rechtmäßigkeit, Fairness und Transparenz

Die Plattform bietet Audit-Trails, Quellenzuordnung und Langfuse-Tracing für Transparenz. Organisationen müssen ihre
Rechtsgrundlage für die Verarbeitung dokumentieren, Datenschutzerklärungen bereitstellen, Aufzeichnungen über
Verarbeitungstätigkeiten führen und Datenschutz-Folgenabschätzungen durchführen. Die Verarbeitung muss rechtmäßig, fair
und transparent gegenüber den betroffenen Personen sein.

### Zweckbindung

Daten müssen für festgelegte, explizite und rechtmäßige Zwecke erhoben und nicht in einer mit diesen Zwecken
unvereinbaren Weise weiterverarbeitet werden. Organisationen sollten klare Zwecke für jede Datenerhebungs- und
-verarbeitungsaktivität definieren.

### Datenminimierung

Multi-Tenant-Isolation, rollenbasierte Zugriffskontrolle und Namespace-Isolation beschränken den Datenzugriff auf das
Notwendige. Erhobene Daten müssen angemessen, relevant und auf das für die definierten Zwecke notwendige Maß beschränkt
sein.

### Richtigkeit

Versionskontrolle verfolgt Datenänderungen, um die Richtigkeit zu gewährleisten. Organisationen müssen sicherstellen,
dass personenbezogene Daten korrekt und bei Bedarf aktuell gehalten werden. Unrichtige Daten müssen unverzüglich
gelöscht oder berichtigt werden.

### Speicherbegrenzung

Ephemeral-Daten verfallen automatisch nach 30 Tagen. Organisationen konfigurieren Aufbewahrungsfristen für die
dauerhafte Speicherung. Daten dürfen nicht länger in einer Form aufbewahrt werden, die die Identifizierung der
betroffenen Personen ermöglicht, als dies für die Verarbeitungszwecke erforderlich ist.

### Integrität und Vertraulichkeit

Die Plattform erfordert TLS/SSL-Verschlüsselung und unterstützt OAuth-, OIDC- und SAML-Authentifizierung. Rollenbasierte
Zugriffskontrolle, Containersicherheit und Eingabevalidierung schützen die Datenintegrität. Die Verarbeitung muss eine
angemessene Sicherheit gewährleisten, einschließlich des Schutzes vor unbefugter oder unrechtmäßiger Verarbeitung sowie
vor versehentlichem Verlust, Zerstörung oder Beschädigung.

### Rechenschaftspflicht

Verantwortliche müssen die Einhaltung aller Grundsätze nachweisen können. Die Plattform unterstützt dies durch
umfassende Audit-Logging, Dokumentationsfunktionen und Nachverfolgbarkeitsmerkmale.

## Rechte der betroffenen Personen

### Auskunftsrecht (Art. 15)

Benutzer können Kopien ihrer personenbezogenen Daten, Verarbeitungsdetails, Empfänger, Aufbewahrungsfristen und
Datenquellen anfordern. Die Plattform bietet eine Benutzerprofil-API und Zugriff auf Audit-Logs.

### Recht auf Berichtigung (Art. 16)

Benutzer können die Korrektur unrichtiger Daten verlangen. Administratoren können Benutzerprofile über die API
aktualisieren. Thread-Nachrichten und Audit-Logs bleiben unveränderlich, um Audit-Trails zu erhalten.

### Recht auf Löschung (Art. 17)

Benutzer können die Löschung von Daten verlangen, wenn diese nicht mehr notwendig sind, die Einwilligung widerrufen wird
oder die Verarbeitung unrechtmäßig ist. Die Plattform unterstützt das Entfernen von Benutzern aus Threads, und
Ephemeral-Daten werden nach 30 Tagen automatisch gelöscht.

Ausnahmen gelten, wenn die Verarbeitung notwendig ist für:

- Meinungs- und Informationsfreiheit
- Einhaltung rechtlicher Verpflichtungen oder Aufgaben im öffentlichen Interesse
- Gründe des öffentlichen Gesundheitswesens
- Archivierungs-, wissenschaftliche oder historische Forschungszwecke oder statistische Zwecke (wenn eine Löschung diese
  unmöglich machen oder ernsthaft beeinträchtigen würde)
- Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen

### Recht auf Datenübertragbarkeit (Art. 20)

Benutzer können ihre Daten in einem maschinenlesbaren Format anfordern. Dies gilt für Daten, die der Benutzer direkt
bereitgestellt hat (Nachrichten, Uploads), nicht für KI-generierte Antworten, Analysen oder abgeleitete Daten. Das Recht
gilt nur, wenn die Verarbeitung auf Einwilligung oder Vertrag beruht und mittels automatisierter Verfahren erfolgt.

### Recht auf Einschränkung der Verarbeitung (Art. 18)

Benutzer können die Aussetzung der Verarbeitung verlangen, während die Datenrichtigkeit überprüft oder Einwände bewertet
werden. Administratoren können Konten über die rollenbasierte Zugriffskontrolle sperren.

### Widerspruchsrecht (Art. 21)

Benutzer können der Verarbeitung aufgrund berechtigter Interessen widersprechen. Der Widerruf von Berechtigungen über
die rollenbasierte Zugriffskontrolle stoppt die Verarbeitung.

## Technische Maßnahmen

Die Plattform implementiert Datenschutz durch Technikgestaltung (Privacy by Design) mit obligatorischer
TLS/SSL-Verschlüsselung, standardmäßiger Zugriffsverweigerung (Default-Deny Access Control), automatischem
Audit-Logging, 30-tägiger Löschung von Ephemeral-Daten und minimaler Datenerfassung. Details finden Sie unter
[Authentifizierung](/de/docs/20_security/1_authentication/), [Verschlüsselung](/de/docs/20_security/5_data_encryption/)
und [Zugriffskontrolle](/de/docs/11_access_management/).

## Internationale Datenübermittlungen

### EU-Angemessenheitsbeschluss für die Schweiz

Die Schweiz hat einen EU-Angemessenheitsbeschluss (im Januar 2024 bestätigt), was bedeutet, dass die Europäische
Kommission das Schweizer Datenschutzrecht als ein angemessenes Schutzniveau anerkennnt. Dies ermöglicht den freien Fluss
personenbezogener Daten von der EU in die Schweiz ohne zusätzliche Schutzmaßnahmen.

Für Organisationen, die in der Schweiz hosten, vereinfacht dies die Einhaltung sowohl der DSGVO- als auch der Schweizer
DSG-Anforderungen. Hosting-Konfigurationen finden Sie unter
[Deployment-Optionen](/de/docs/3_deployment_guide/1_deployment_options/).

### Übermittlungen in andere Länder

Übermittlungen in Länder ohne Angemessenheitsbeschluss erfordern geeignete Schutzmaßnahmen:

- Von der Europäischen Kommission genehmigte Standardvertragsklauseln (SCCs)
- Verbindliche interne Datenschutzvorschriften (BCRs)
- Genehmigte Verhaltensregeln oder Zertifizierungsmechanismen
- Spezifische Ausnahmen (Einwilligung, Vertragsnotwendigkeit, lebenswichtige Interessen usw.)

## Meldung von Datenschutzverletzungen

Artikel 33 DSGVO verpflichtet zur Benachrichtigung der Aufsichtsbehörde **unverzüglich und, soweit möglich, spätestens
72 Stunden**, nachdem die Organisation Kenntnis von einer Verletzung erlangt hat, die voraussichtlich zu einem Risiko
für die Rechte und Freiheiten natürlicher Personen führt. Erfolgt die Benachrichtigung nicht innerhalb von 72 Stunden,
müssen die Gründe für die Verzögerung angegeben werden. Eine Benachrichtigung ist nicht erforderlich, wenn die
Verletzung voraussichtlich kein Risiko darstellt.

Die Benachrichtigung muss die Art der Verletzung, die betroffenen Personen, die wahrscheinlichen Folgen und die
ergriffenen Abhilfemaßnahmen umfassen. Betroffene Personen müssen direkt informiert werden (Artikel 34), wenn die
Verletzung voraussichtlich ein hohes Risiko für ihre Rechte und Freiheiten darstellt.

Die Plattform bietet Audit-Logs, Benutzerzugriffsberichte, Monitoring, Alerting und Backup-Funktionen zur Unterstützung
der Untersuchung, Dokumentation und Reaktion auf Datenschutzverletzungen.

## Verwandte Dokumentation

- [Schweizer DSG](../3_dsg/)
- [DSAR-Verfahren](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [Volltext der DSGVO](https://gdpr-info.eu/)
- [EDPB-Leitlinien](https://edpb.europa.eu/)

______________________________________________________________________

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie Ihren Datenschutzbeauftragten oder
Rechtsbeistand.
:::
