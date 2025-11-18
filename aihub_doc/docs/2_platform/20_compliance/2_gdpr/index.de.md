---
title: GDPR-Konformität
source_sha: bea7bcc79ea412a8fc2d8084a41dd73ee323f91885925bd7a01cf9a66dd83f89
---

# GDPR-Konformität

Die Plattform bietet technische Maßnahmen zur Unterstützung der GDPR-Konformität. Organisationen, die die Plattform
nutzen, agieren als Datenverantwortliche und bleiben für ihre eigene Compliance verantwortlich.

## Anwendbarkeit auf Schweizer Organisationen

Die GDPR gilt für Schweizer Organisationen, wenn sie personenbezogene Daten von Personen in der EU verarbeiten, sofern
sich die Verarbeitung bezieht auf:

- Das Anbieten von Waren oder Dienstleistungen an EU-Bürger (unabhängig von der Bezahlung)
- Die Beobachtung des Verhaltens von Personen in der EU

Organisationen müssen die GDPR-Anforderungen auch ohne eine EU-Niederlassung erfüllen, wenn diese Bedingungen gegeben
sind.

## Rechtsgrundlage für die Verarbeitung

Artikel 6 GDPR erfordert eine Rechtsgrundlage für jede Verarbeitung personenbezogener Daten. Mindestens eine der
folgenden muss zutreffen:

- Einwilligung: Die betroffene Person hat eine klare Einwilligung für bestimmte Zwecke erteilt.
- Vertrag: Die Verarbeitung ist zur Erfüllung eines Vertrags oder zur Durchführung vorvertraglicher Maßnahmen
  erforderlich.
- Rechtliche Verpflichtung: Die Verarbeitung ist zur Einhaltung rechtlicher Anforderungen erforderlich.
- Vitales Interesse: Die Verarbeitung ist zum Schutz des Lebens oder der körperlichen Unversehrtheit erforderlich.
- Öffentliche Aufgabe: Die Verarbeitung ist für Aufgaben im öffentlichen Interesse oder zur Ausübung amtlicher
  Befugnisse erforderlich.
- Berechtigte Interessen: Die Verarbeitung ist für berechtigte Interessen erforderlich, es sei denn, diese werden durch
  die Rechte der betroffenen Person überlagert (nicht verfügbar für öffentliche Behörden).

Organisationen müssen ihre Rechtsgrundlage dokumentieren und die betroffenen Personen entsprechend informieren.

## GDPR-Grundsätze

Artikel 5 GDPR legt sechs Kernprinzipien für die Verarbeitung personenbezogener Daten sowie eine Rechenschaftspflicht
fest:

### Rechtmäßigkeit, Fairness und Transparenz

Die Plattform bietet Audit-Trails, Quellenzuordnung und Phoenix-Tracing für Transparenz. Organisationen müssen ihre
Rechtsgrundlage für die Verarbeitung dokumentieren, Datenschutzerklärungen bereitstellen, Aufzeichnungen über
Verarbeitungstätigkeiten führen und Datenschutz-Folgenabschätzungen durchführen. Die Verarbeitung muss rechtmäßig, fair
und für die betroffenen Personen transparent sein.

### Zweckbindung

Daten müssen für festgelegte, eindeutige und legitime Zwecke erhoben und dürfen nicht in einer mit diesen Zwecken
unvereinbaren Weise weiterverarbeitet werden. Organisationen sollten klare Zwecke für jede Datenerhebungs- und
Verarbeitungstätigkeit definieren.

### Datenminimierung

Mandanten-Isolation (Multi-tenant isolation), rollenbasierte Zugriffskontrolle (role-based access control) und
Namespace-Isolation beschränken den Datenzugriff auf das Notwendige. Die erhobenen Daten müssen angemessen, relevant und
auf das für die definierten Zwecke notwendige Maß beschränkt sein.

### Richtigkeit

Die Versionskontrolle verfolgt Datenänderungen, um die Richtigkeit zu gewährleisten. Organisationen müssen
sicherstellen, dass personenbezogene Daten richtig und, wo notwendig, auf dem neuesten Stand gehalten werden. Unrichtige
Daten müssen unverzüglich gelöscht oder berichtigt werden.

### Speicherbegrenzung

Ephimere Daten verfallen automatisch nach 30 Tagen. Organisationen konfigurieren Aufbewahrungsfristen für die permanente
Speicherung. Daten dürfen nicht länger in einer Form gespeichert werden, die die Identifizierung der betroffenen
Personen ermöglicht, als es für die Verarbeitungszwecke erforderlich ist.

### Integrität und Vertraulichkeit

Die Plattform erfordert TLS/SSL-Verschlüsselung und unterstützt OAuth-, OIDC- und SAML-Authentifizierung. Rollenbasierte
Zugriffskontrolle, Container-Sicherheit und Eingabevalidierung schützen die Datenintegrität. Die Verarbeitung muss eine
angemessene Sicherheit gewährleisten, einschließlich des Schutzes vor unbefugter oder unrechtmäßiger Verarbeitung und
vor versehentlichem Verlust, Zerstörung oder Beschädigung.

### Rechenschaftspflicht

Verantwortliche müssen die Einhaltung aller Grundsätze nachweisen können. Die Plattform unterstützt dies durch
umfassende Audit-Protokollierung, Dokumentationsfunktionen und Nachverfolgbarkeitsmerkmale.

## Rechte der betroffenen Personen

### Auskunftsrecht (Art. 15)

Nutzer können Kopien ihrer personenbezogenen Daten, Verarbeitungsdetails, Empfänger, Aufbewahrungsfristen und
Datenquellen anfordern. Die Plattform bietet eine Nutzerprofil-API und Zugriff auf Audit-Protokolle.

### Recht auf Berichtigung (Art. 16)

Nutzer können die Berichtigung unrichtiger Daten verlangen. Administratoren können Nutzerprofile über die API
aktualisieren. Thread-Nachrichten und Audit-Protokolle bleiben unveränderlich, um Audit-Trails zu erhalten.

### Recht auf Löschung (Art. 17)

Nutzer können die Löschung von Daten verlangen, wenn diese nicht mehr notwendig sind, die Einwilligung widerrufen wird
oder die Verarbeitung unrechtmäßig ist. Die Plattform unterstützt das Entfernen von Nutzern aus Threads, und ephemere
Daten werden automatisch nach 30 Tagen gelöscht.

Ausnahmen gelten, wenn die Verarbeitung notwendig ist für:

- Die Ausübung des Rechts auf freie Meinungsäußerung und Information
- Die Einhaltung einer rechtlichen Verpflichtung oder die Wahrnehmung einer Aufgabe im öffentlichen Interesse
- Gründe des öffentlichen Interesses im Bereich der öffentlichen Gesundheit
- Archivierungszwecke, wissenschaftliche oder historische Forschungszwecke oder statistische Zwecke (wenn die Löschung
  diese unmöglich machen oder ernsthaft beeinträchtigen würde)
- Die Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen

### Recht auf Datenübertragbarkeit (Art. 20)

Nutzer können ihre Daten in einem maschinenlesbaren Format anfordern. Dies gilt für Daten, die der Nutzer direkt
bereitgestellt hat (Nachrichten, Uploads), nicht für KI-generierte Antworten, Analysen oder abgeleitete Daten. Das Recht
gilt nur, wenn die Verarbeitung auf Einwilligung oder einem Vertrag beruht und mittels automatisierter Verfahren
erfolgt.

### Recht auf Einschränkung der Verarbeitung (Art. 18)

Nutzer können die Aussetzung der Verarbeitung verlangen, während die Datenrichtigkeit überprüft oder Einwände bewertet
werden. Administratoren können Konten über die rollenbasierte Zugriffskontrolle sperren.

### Widerspruchsrecht (Art. 21)

Nutzer können der Verarbeitung aufgrund berechtigter Interessen widersprechen. Der Widerruf von Berechtigungen über die
rollenbasierte Zugriffskontrolle stoppt die Verarbeitung.

## Technische Maßnahmen

Die Plattform implementiert Datenschutz durch Design (privacy by design) mit obligatorischer TLS/SSL-Verschlüsselung,
"default-deny" Zugriffskontrolle, automatischer Audit-Protokollierung, automatischer Löschung ephemerer Daten nach 30
Tagen und minimaler Datenerhebung. Details finden Sie unter
[Authentifizierung](/de/docs/2_platform/19_security/1_authentication/),
[Verschlüsselung](/de/docs/2_platform/19_security/5_data_encryption/) und
[Zugriffskontrolle](/de/docs/2_platform/11_access_management/).

## Internationale Datenübermittlungen

### EU-Angemessenheitsbeschluss für die Schweiz

Die Schweiz verfügt über einen EU-Angemessenheitsbeschluss (im Januar 2024 bestätigt), was bedeutet, dass die
Europäische Kommission das Schweizer Datenschutzrecht als ein angemessenes Schutzniveau anerkennt. Dies ermöglicht den
freien Fluss personenbezogener Daten von der EU in die Schweiz ohne zusätzliche Schutzmaßnahmen.

Für Organisationen, die in der Schweiz hosten, vereinfacht dies die Einhaltung sowohl der GDPR- als auch der Schweizer
DSG-Anforderungen. Für Hosting-Konfigurationen siehe
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/).

### Übermittlungen in andere Länder

Übermittlungen in Länder ohne Angemessenheitsbeschluss erfordern geeignete Garantien:

- Von der Europäischen Kommission genehmigte Standardvertragsklauseln (SCCs)
- Verbindliche interne Datenschutzvorschriften (BCRs)
- Genehmigte Verhaltenskodizes oder Zertifizierungsmechanismen
- Spezifische Ausnahmen (Einwilligung, Notwendigkeit des Vertrags, vitale Interessen usw.)

## Meldung von Datenschutzverletzungen

Artikel 33 GDPR verpflichtet zur Benachrichtigung der Aufsichtsbehörde **unverzüglich und, soweit machbar, spätestens 72
Stunden**, nachdem eine Verletzung bekannt wurde, die voraussichtlich zu einem Risiko für die Rechte und Freiheiten
natürlicher Personen führt. Erfolgt die Meldung nicht innerhalb von 72 Stunden, müssen die Gründe für die Verzögerung
angegeben werden. Eine Meldung ist nicht erforderlich, wenn die Verletzung voraussichtlich nicht zu einem Risiko führt.

Die Meldung muss die Art der Verletzung, die betroffenen Personen, die wahrscheinlichen Folgen und die ergriffenen
Abhilfemaßnahmen umfassen. Die betroffenen Personen müssen direkt informiert werden (Artikel 34), wenn die Verletzung
voraussichtlich zu einem hohen Risiko für ihre Rechte und Freiheiten führt.

Die Plattform bietet Audit-Protokolle, Nutzerzugriffsberichte, Monitoring, Alarme und Backup-Funktionen zur
Unterstützung der Untersuchung, Dokumentation und Reaktion auf Verletzungen.

## Verwandte Dokumentation

- [Schweizer DSG](../3_dsg/)
- [DSAR-Verfahren](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [GDPR Volltext](https://gdpr-info.eu/)
- [EDPB Richtlinien](https://edpb.europa.eu/)

---

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie Ihren Datenschutzbeauftragten oder
Rechtsbeistand.
:::
