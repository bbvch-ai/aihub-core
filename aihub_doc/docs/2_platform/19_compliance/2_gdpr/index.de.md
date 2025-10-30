---
title: GDPR-Konformität
source_sha: a3b82acfc97dd9d61d3256815feff4006abc073c6edf8010b15d4390e4eb1913
---

# GDPR-Konformität

Die Plattform bietet technische Maßnahmen zur Unterstützung der GDPR-Konformität. Organisationen, die die Plattform
nutzen, agieren als Datenverantwortliche und bleiben für ihre eigene Einhaltung verantwortlich.

## Anwendbarkeit auf Schweizer Organisationen

Die GDPR gilt für Schweizer Organisationen bei der Verarbeitung personenbezogener Daten von Personen in der EU, wenn die
Verarbeitung sich bezieht auf:

- Das Anbieten von Waren oder Dienstleistungen für EU-Bürger (unabhängig von der Zahlung)
- Die Beobachtung des Verhaltens von Personen in der EU

Organisationen müssen die GDPR-Anforderungen auch ohne eine EU-Niederlassung einhalten, wenn diese Bedingungen erfüllt
sind.

## Rechtsgrundlage für die Verarbeitung

Artikel 6 der GDPR erfordert eine Rechtsgrundlage für jede Verarbeitung personenbezogener Daten. Mindestens eine der
folgenden muss zutreffen:

- Einwilligung: Die betroffene Person hat eine eindeutige Einwilligung für bestimmte Zwecke erteilt.
- Vertrag: Die Verarbeitung ist zur Erfüllung eines Vertrags oder zur Durchführung vorvertraglicher Maßnahmen
  erforderlich.
- Rechtliche Verpflichtung: Die Verarbeitung ist zur Einhaltung rechtlicher Verpflichtungen erforderlich.
- Lebenswichtige Interessen: Die Verarbeitung ist zum Schutz lebenswichtiger Interessen oder der körperlichen
  Unversehrtheit erforderlich.
- Öffentliche Aufgabe: Die Verarbeitung ist für Aufgaben im öffentlichen Interesse oder zur Ausübung öffentlicher Gewalt
  erforderlich.
- Berechtigte Interessen: Die Verarbeitung ist zur Wahrung berechtigter Interessen erforderlich, es sei denn, die Rechte
  der betroffenen Person überwiegen (nicht für öffentliche Behörden verfügbar).

Organisationen müssen ihre Rechtsgrundlage dokumentieren und die betroffenen Personen entsprechend informieren.

## GDPR-Grundsätze

Artikel 5 der GDPR legt sechs Grundsätze für die Verarbeitung personenbezogener Daten sowie eine Rechenschaftspflicht
fest:

### Rechtmäßigkeit, Verarbeitung nach Treu und Glauben und Transparenz

Die Plattform bietet Audit-Trails, Quellenzuordnung und Phoenix-Tracing für Transparenz. Organisationen müssen ihre
Rechtsgrundlage für die Verarbeitung dokumentieren, Datenschutzerklärungen bereitstellen, Verzeichnisse der
Verarbeitungstätigkeiten führen und Datenschutz-Folgenabschätzungen durchführen. Die Verarbeitung muss rechtmäßig, fair
und für die betroffenen Personen transparent sein.

### Zweckbindung

Daten müssen für festgelegte, ausdrückliche und rechtmäßige Zwecke erhoben und dürfen nicht in einer mit diesen Zwecken
unvereinbaren Weise weiterverarbeitet werden. Organisationen sollten klare Zwecke für jede Datenerhebungs- und
-verarbeitungsaktivität definieren.

### Datenminimierung

Mandantenisolation, rollenbasierte Zugriffskontrolle und Namespace-Isolation beschränken den Datenzugriff auf das
Notwendige. Erfasste Daten müssen angemessen, relevant und auf das für die definierten Zwecke notwendige Maß beschränkt
sein.

### Richtigkeit

Die Versionskontrolle verfolgt Datenänderungen zur Wahrung der Richtigkeit. Organisationen müssen sicherstellen, dass
personenbezogene Daten richtig und, wo erforderlich, auf dem neuesten Stand gehalten werden. Unrichtige Daten müssen
unverzüglich gelöscht oder berichtigt werden.

### Speicherbegrenzung

Ephemere Daten laufen nach 30 Tagen automatisch ab. Organisationen konfigurieren Aufbewahrungsfristen für die dauerhafte
Speicherung. Daten müssen in einer Form gespeichert werden, die die Identifizierung betroffener Personen nicht länger
als für die Verarbeitungszwecke erforderlich ermöglicht.

### Integrität und Vertraulichkeit

Die Plattform erfordert TLS/SSL-Verschlüsselung und unterstützt OAuth-, OIDC- und SAML-Authentifizierung. Rollenbasierte
Zugriffskontrolle, Container-Sicherheit und Eingabevalidierung schützen die Datenintegrität. Die Verarbeitung muss eine
angemessene Sicherheit gewährleisten, einschließlich des Schutzes vor unbefugter oder unrechtmäßiger Verarbeitung und
vor versehentlichem Verlust, Zerstörung oder Beschädigung.

### Rechenschaftspflicht

Verantwortliche müssen die Einhaltung aller Grundsätze nachweisen können. Die Plattform unterstützt dies durch
umfassende Audit-Protokollierung, Dokumentationsfunktionen und Nachverfolgbarkeit.

## Rechte der betroffenen Personen

### Auskunftsrecht (Art. 15)

Nutzer können Kopien ihrer personenbezogenen Daten, Verarbeitungsdetails, Empfänger, Aufbewahrungsfristen und
Datenquellen anfordern. Die Plattform bietet eine Benutzerprofil-API und Zugriff auf Audit-Protokolle.

### Recht auf Berichtigung (Art. 16)

Nutzer können die Berichtigung unrichtiger Daten verlangen. Administratoren können Benutzerprofile über die API
aktualisieren. Thread-Nachrichten und Audit-Protokolle bleiben unveränderlich, um Audit-Trails zu erhalten.

### Recht auf Löschung („Recht auf Vergessenwerden“) (Art. 17)

Nutzer können die Löschung von Daten verlangen, wenn diese nicht mehr notwendig sind, die Einwilligung widerrufen wird
oder die Verarbeitung unrechtmäßig ist. Die Plattform unterstützt das Entfernen von Nutzern aus Threads, und ephemere
Daten werden nach 30 Tagen automatisch gelöscht.

Ausnahmen gelten, wenn die Verarbeitung erforderlich ist für:

- Das Recht auf freie Meinungsäußerung und Information
- Die Einhaltung rechtlicher Verpflichtungen oder Aufgaben im öffentlichen Interesse
- Gründe des öffentlichen Interesses im Bereich der öffentlichen Gesundheit
- Archivierungszwecke im öffentlichen Interesse, wissenschaftliche oder historische Forschungszwecke oder statistische
  Zwecke (wenn die Löschung diese unmöglich machen oder ernsthaft beeinträchtigen würde)
- Die Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen

### Recht auf Datenübertragbarkeit (Art. 20)

Nutzer können ihre Daten in einem maschinenlesbaren Format anfordern. Dies gilt für Daten, die der Nutzer direkt
bereitgestellt hat (Nachrichten, Uploads), nicht für KI-generierte Antworten, Analysen oder abgeleitete Daten. Das Recht
gilt nur, wenn die Verarbeitung auf Einwilligung oder Vertrag beruht und automatisiert erfolgt.

### Recht auf Einschränkung der Verarbeitung (Art. 18)

Nutzer können die Aussetzung der Verarbeitung verlangen, während die Datenrichtigkeit überprüft oder Einwände bewertet
werden. Administratoren können Konten über die rollenbasierte Zugriffskontrolle sperren.

### Widerspruchsrecht (Art. 21)

Nutzer können der Verarbeitung aufgrund berechtigter Interessen widersprechen. Der Widerruf von Berechtigungen über die
rollenbasierte Zugriffskontrolle beendet die Verarbeitung.

## Technische Maßnahmen

Die Plattform implementiert Datenschutz durch Technikgestaltung (Privacy by Design) mit obligatorischer
TLS/SSL-Verschlüsselung, Zugriffssteuerung nach dem „Default-Deny"-Prinzip, automatischer Audit-Protokollierung,
automatischer Löschung ephemerer Daten nach 30 Tagen und minimaler Datenerhebung. Weitere Informationen finden Sie unter
[Authentifizierung](../../18_security/1_authentication/), [Verschlüsselung](../../18_security/5_data_encryption/) und
[Zugriffskontrolle](../../11_access_management/).

## Internationale Datenübermittlung

### EU-Angemessenheitsbeschluss für die Schweiz

Die Schweiz besitzt einen EU-Angemessenheitsbeschluss (im Januar 2024 bestätigt), was bedeutet, dass die Europäische
Kommission das schweizerische Datenschutzrecht als ein angemessenes Schutzniveau anerkennt. Dies ermöglicht den freien
Fluss personenbezogener Daten von der EU in die Schweiz ohne zusätzliche Schutzmaßnahmen.

Für Organisationen, die in der Schweiz hosten, vereinfacht dies die Einhaltung der GDPR- und schweizerischen
DSG-Anforderungen. Siehe [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) für
Hosting-Konfigurationen.

### Übermittlungen in andere Länder

Übermittlungen in Länder ohne Angemessenheitsbeschluss erfordern geeignete Schutzmaßnahmen:

- Von der Europäischen Kommission genehmigte Standardvertragsklauseln (SCCs)
- Verbindliche interne Datenschutzvorschriften (BCRs)
- Genehmigte Verhaltensregeln oder Zertifizierungsmechanismen
- Spezifische Ausnahmen (Einwilligung, Vertragserfüllung, lebenswichtige Interessen usw.)

## Meldung von Datenschutzverletzungen

Artikel 33 der GDPR schreibt vor, die Aufsichtsbehörde **unverzüglich und, soweit machbar, spätestens 72 Stunden**
nachdem Kenntnis von einer Verletzung erlangt wurde, die voraussichtlich zu einem Risiko für die Rechte und Freiheiten
natürlicher Personen führt, zu benachrichtigen. Erfolgt die Meldung nicht innerhalb von 72 Stunden, müssen die Gründe
für die Verzögerung angegeben werden. Eine Meldung ist nicht erforderlich, wenn die Verletzung voraussichtlich kein
Risiko darstellt.

Die Meldung muss die Art der Verletzung, die betroffenen Personen, die voraussichtlichen Folgen und die ergriffenen
Abhilfemaßnahmen enthalten. Betroffene Personen müssen direkt informiert werden (Artikel 34), wenn die Verletzung
voraussichtlich ein hohes Risiko für ihre Rechte und Freiheiten darstellt.

Die Plattform bietet Audit-Protokolle, Benutzerzugriffsberichte, Überwachung, Alarmierung und Sicherungsfunktionen zur
Unterstützung der Untersuchung, Dokumentation und Reaktion auf Datenschutzverletzungen.

## Verwandte Dokumentation

- [Schweizer DSG](../3_dsg/)
- [DSAR-Verfahren](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [GDPR Volltext](https://gdpr-info.eu/)
- [EDPB-Leitlinien](https://edpb.europa.eu/)

---

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie Ihren Datenschutzbeauftragten oder
Rechtsbeistand.
:::
