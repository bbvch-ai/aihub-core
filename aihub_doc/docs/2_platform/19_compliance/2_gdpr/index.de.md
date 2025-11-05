---
title: DSGVO-Konformität
source_sha: 7be91a185d6c1ca5bd1392bdbba63c1b749d89d10d400e9dc472f50730091e36
---

# DSGVO-Konformität

Die Plattform bietet technische Maßnahmen zur Unterstützung der DSGVO-Konformität. Organisationen, die die Plattform
nutzen, agieren als Datenverantwortliche und bleiben für ihre eigene Konformität verantwortlich.

## Anwendbarkeit auf Schweizer Organisationen

Die DSGVO gilt für Schweizer Organisationen, wenn sie personenbezogene Daten von Personen in der EU verarbeiten und sich
die Verarbeitung bezieht auf:

- Das Anbieten von Waren oder Dienstleistungen für EU-Bürger (unabhängig von der Bezahlung)
- Die Überwachung des Verhaltens von Personen in der EU

Organisationen müssen die Anforderungen der DSGVO erfüllen, auch ohne eine Niederlassung in der EU, wenn diese
Bedingungen erfüllt sind.

## Rechtsgrundlage für die Verarbeitung

Artikel 6 DSGVO verlangt eine Rechtsgrundlage für jede Verarbeitung personenbezogener Daten. Mindestens eine der
folgenden muss zutreffen:

- Einwilligung: Die betroffene Person hat eine klare Einwilligung für bestimmte Zwecke erteilt.
- Vertrag: Die Verarbeitung ist für die Erfüllung eines Vertrags oder vorvertragliche Maßnahmen erforderlich.
- Rechtliche Verpflichtung: Die Verarbeitung ist zur Einhaltung rechtlicher Vorgaben erforderlich.
- Vitales Interesse: Die Verarbeitung ist zum Schutz des Lebens oder der körperlichen Unversehrtheit erforderlich.
- Öffentliche Aufgabe: Die Verarbeitung ist für Aufgaben im öffentlichen Interesse oder zur Ausübung öffentlicher Gewalt
  erforderlich.
- Berechtigtes Interesse: Die Verarbeitung ist für berechtigte Interessen erforderlich, es sei denn, die Rechte der
  betroffenen Person überwiegen (nicht anwendbar für Behörden).

Organisationen müssen ihre Rechtsgrundlage dokumentieren und die betroffenen Personen entsprechend informieren.

## DSGVO-Prinzipien

Artikel 5 DSGVO legt sechs Kernprinzipien für die Verarbeitung personenbezogener Daten fest, zuzüglich einer
Rechenschaftspflicht:

### Rechtmäßigkeit, Fairness und Transparenz

Die Plattform bietet Audit-Trails, Quellenattribution und Phoenix-Tracing für Transparenz. Organisationen müssen ihre
Rechtsgrundlage für die Verarbeitung dokumentieren, Datenschutzerklärungen bereitstellen, Verzeichnisse von
Verarbeitungstätigkeiten führen und Datenschutz-Folgenabschätzungen durchführen. Die Verarbeitung muss rechtmäßig, fair
und für die betroffenen Personen transparent sein.

### Zweckbindung

Daten müssen für festgelegte, eindeutige und legitime Zwecke erhoben und dürfen nicht in einer mit diesen Zwecken
unvereinbaren Weise weiterverarbeitet werden. Organisationen sollten klare Zwecke für jede Datenerhebungs- und
-verarbeitungsaktivität definieren.

### Datenminimierung

Mandantenfähigkeit, rollenbasierte Zugriffskontrolle und Namespace-Isolation beschränken den Datenzugriff auf das
Notwendige. Erhobene Daten müssen angemessen, relevant und auf das für die definierten Zwecke notwendige Maß beschränkt
sein.

### Richtigkeit

Versionskontrolle verfolgt Datenänderungen, um die Richtigkeit zu gewährleisten. Organisationen müssen sicherstellen,
dass personenbezogene Daten korrekt und bei Bedarf aktuell sind. Unrichtige Daten müssen unverzüglich gelöscht oder
berichtigt werden.

### Speicherbegrenzung

Ephemeral data (flüchtige Daten) läuft nach 30 Tagen automatisch ab. Organisationen konfigurieren Aufbewahrungsfristen
für die dauerhafte Speicherung. Daten dürfen nur so lange in einer Form gespeichert werden, die die Identifizierung der
betroffenen Personen ermöglicht, wie es für die Verarbeitungszwecke erforderlich ist.

### Integrität und Vertraulichkeit

Die Plattform erfordert TLS/SSL-Verschlüsselung und unterstützt OAuth-, OIDC- und SAML-Authentifizierung. Rollenbasierte
Zugriffskontrolle, Containersicherheit und Eingabevalidierung schützen die Datenintegrität. Die Verarbeitung muss eine
angemessene Sicherheit gewährleisten, einschließlich des Schutzes vor unbefugter oder unrechtmäßiger Verarbeitung sowie
vor versehentlichem Verlust, Zerstörung oder Beschädigung.

### Rechenschaftspflicht

Verantwortliche müssen die Einhaltung aller Prinzipien nachweisen können. Die Plattform unterstützt dies durch
umfassende Audit-Protokollierung, Dokumentationsfunktionen und Nachverfolgbarkeit.

## Rechte der betroffenen Person

### Auskunftsrecht (Art. 15)

Nutzer können Kopien ihrer personenbezogenen Daten, Verarbeitungsdetails, Empfänger, Aufbewahrungsfristen und
Datenquellen anfordern. Die Plattform bietet eine Benutzerprofil-API und Zugriff auf Audit-Protokolle.

### Recht auf Berichtigung (Art. 16)

Nutzer können die Berichtigung unrichtiger Daten verlangen. Administratoren können Benutzerprofile über die API
aktualisieren. Thread-Nachrichten und Audit-Protokolle bleiben unveränderlich, um Audit-Trails zu bewahren.

### Recht auf Löschung (Art. 17)

Nutzer können die Löschung von Daten verlangen, wenn diese nicht mehr erforderlich sind, die Einwilligung widerrufen
wird oder die Verarbeitung unrechtmäßig ist. Die Plattform unterstützt das Entfernen von Nutzern aus Threads, und
ephemere Daten werden nach 30 Tagen automatisch gelöscht.

Ausnahmen gelten, wenn die Verarbeitung erforderlich ist für:

- Die Ausübung des Rechts auf freie Meinungsäußerung und Information
- Die Erfüllung einer rechtlichen Verpflichtung oder einer Aufgabe im öffentlichen Interesse
- Gründe des öffentlichen Gesundheitswesens
- Archivzwecke im öffentlichen Interesse, wissenschaftliche oder historische Forschungszwecke oder statistische Zwecke
  (wenn die Löschung diese unmöglich machen oder ernsthaft beeinträchtigen würde)
- Die Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen

### Recht auf Datenübertragbarkeit (Art. 20)

Nutzer können ihre Daten in einem maschinenlesbaren Format anfordern. Dies gilt für Daten, die der Nutzer direkt
bereitgestellt hat (Nachrichten, Uploads), nicht für KI-generierte Antworten, Analysen oder abgeleitete Daten. Das Recht
gilt nur, wenn die Verarbeitung auf einer Einwilligung oder einem Vertrag beruht und mittels automatisierter Verfahren
erfolgt.

### Recht auf Einschränkung der Verarbeitung (Art. 18)

Nutzer können die Aussetzung der Verarbeitung verlangen, während die Richtigkeit der Daten überprüft oder Einwände
bewertet werden. Administratoren können Konten über die rollenbasierte Zugriffskontrolle sperren.

### Widerspruchsrecht (Art. 21)

Nutzer können der Verarbeitung aufgrund berechtigter Interessen widersprechen. Der Widerruf von Berechtigungen über die
rollenbasierte Zugriffskontrolle beendet die Verarbeitung.

## Technische Maßnahmen

Die Plattform implementiert Datenschutz durch Technikgestaltung mit obligatorischer TLS/SSL-Verschlüsselung,
Default-Deny-Zugriffskontrolle, automatischer Audit-Protokollierung, 30-tägiger Löschung temporärer Daten und minimaler
Datenerfassung. Weitere Details finden Sie unter [Authentifizierung](/de/docs/2_platform/18_security/1_authentication/),
[Verschlüsselung](/de/docs/2_platform/18_security/5_data_encryption/) und
[Zugriffskontrolle](/de/docs/2_platform/11_access_management/).

## Internationale Datenübermittlungen

### EU-Angemessenheitsbeschluss für die Schweiz

Die Schweiz verfügt über einen EU-Angemessenheitsbeschluss (im Januar 2024 bestätigt), was bedeutet, dass die
Europäische Kommission das Schweizer Datenschutzrecht als ein angemessenes Schutzniveau anerkkennt. Dies ermöglicht den
freien Fluss personenbezogener Daten von der EU in die Schweiz ohne zusätzliche Schutzmaßnahmen.

Für Organisationen, die in der Schweiz hosten, vereinfacht dies die Einhaltung sowohl der DSGVO- als auch der Schweizer
DSG-Anforderungen. Hosting-Konfigurationen finden Sie unter
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).

### Übermittlungen in andere Länder

Übermittlungen in Länder ohne Angemessenheitsbeschluss erfordern geeignete Schutzmaßnahmen:

- Von der Europäischen Kommission genehmigte Standardvertragsklauseln (SCCs)
- Verbindliche interne Datenschutzvorschriften (BCRs)
- Genehmigte Verhaltensregeln oder Zertifizierungsmechanismen
- Spezifische Ausnahmen (Einwilligung, Notwendigkeit des Vertrags, vitale Interessen usw.)

## Meldung von Datenschutzverletzungen

Artikel 33 DSGVO verlangt die Benachrichtigung der Aufsichtsbehörde **unverzüglich und, soweit möglich, spätestens 72
Stunden** nachdem eine Verletzung des Schutzes personenbezogener Daten bekannt geworden ist, die voraussichtlich zu
einem Risiko für die Rechte und Freiheiten natürlicher Personen führt. Erfolgt die Meldung nicht innerhalb von 72
Stunden, müssen die Gründe für die Verzögerung angegeben werden. Eine Meldung ist nicht erforderlich, wenn die
Verletzung voraussichtlich kein Risiko zur Folge hat.

Die Meldung muss die Art der Verletzung, die betroffenen Personen, die wahrscheinlichen Folgen und die ergriffenen
Abhilfemaßnahmen enthalten. Die betroffenen Personen müssen direkt informiert werden (Artikel 34), wenn die Verletzung
voraussichtlich ein hohes Risiko für ihre Rechte und Freiheiten zur Folge hat.

Die Plattform bietet Audit-Protokolle, Benutzerzugriffsberichte, Überwachungs-, Alarmierungs- und Sicherungsfunktionen,
um die Untersuchung, Dokumentation und Reaktion auf Datenschutzverletzungen zu unterstützen.

## Verwandte Dokumentation

- [Schweizer DSG](/de/docs/2_platform/19_compliance/3_dsg/)
- [DSAR-Verfahren](/de/docs/2_platform/19_compliance/6_data_subject_requests/)
- [Datenaufbewahrung](/de/docs/2_platform/19_compliance/1_data_retention/)
- [DSGVO vollständiger Text](https://gdpr-info.eu/)
- [EDPB Leitlinien](https://edpb.europa.eu/)

---

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie Ihren Datenschutzbeauftragten oder
Rechtsbeistand.
:::
