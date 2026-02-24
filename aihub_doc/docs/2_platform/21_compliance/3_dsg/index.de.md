---
title: Schweizer Datenschutzgesetz (DSG)
source_sha: 138ae64edfe05e8d1bdcb34d14176ee9e8ac4d0c0b8232cfdb6eb3fd09c099db
---

# Schweizer Datenschutzgesetz (revDSG)

Das revidierte Schweizer Bundesgesetz über den Datenschutz (revDSG/FADP) ist am 1. September 2023 in Kraft getreten. Die
Revision wurde vorgenommen, um die EU-Datenschutzstandards zu übernehmen, während gleichzeitig schweizspezifische
Ansätze für bestimmte Anforderungen beibehalten wurden.

:::info
Siehe [DSGVO-Konformität](../2_gdpr/) für gemeinsame Anforderungen. Dieses Dokument behandelt ausschliesslich
schweizspezifische Unterschiede.
:::

:::warning Wann die DSGVO ebenfalls gilt
Schweizer Organisationen müssen sowohl das revDSG als auch die DSGVO einhalten, wenn sie Waren/Dienstleistungen für
EU-Bürger anbieten oder das Verhalten von EU-Personen überwachen. Siehe
[Anwendbarkeit der DSGVO](../2_gdpr/#applicability-to-swiss-organizations).
:::

## Hauptunterschiede zur DSGVO

| Aspekt                         | revDSG                                                                  | DSGVO                                                                                          |
| :----------------------------- | :---------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------- |
| Bussen                         | Bis zu CHF 250K gegen Einzelpersonen (nicht Unternehmen)                | Bis zu €20M oder 4% des Umsatzes gegen Unternehmen                                             |
| Datenschutzbeauftragter (DPO)  | Nicht erforderlich                                                      | Oft obligatorisch                                                                              |
| Rechtsgrundlage                | Keine explizite Rechtsgrundlage erforderlich (anderer Ansatz)           | Explizite Rechtsgrundlage obligatorisch (Art. 6)                                               |
| Meldung von Verletzungen       | „So schnell wie möglich“, wenn hohes Risiko (keine gesetzliche Frist)   | Ohne unangemessene Verzögerung, wenn möglich innerhalb von 72 Stunden, wenn ein Risiko besteht |
| Besonders schützenswerte Daten | Beinhaltet Verwaltungs-/Strafverfahren + Sozialversicherungsdaten       | 9 besondere Kategorien                                                                         |
| Anwendungsbereich              | Nur natürliche Personen (juristische Personen seit 2023 ausgeschlossen) | Nur natürliche Personen                                                                        |

## revDSG-spezifische Anforderungen

### Hochrisikoprofiling

Das revDSG erfordert die Überwachung der automatisierten Bewertung persönlicher Aspekte wie Risikobewertung und
Verhaltensvorhersage. Die Plattform bietet Human-in-the-Loop-Funktionen, Langfuse-Tracing und Quellenzuordnung zur
Unterstützung dieser Anforderung. Organisationen müssen Hochrisikoprofiling-Aktivitäten identifizieren,
Datenschutz-Folgenabschätzungen durchführen und eine angemessene menschliche Aufsicht implementieren.

### Verzeichnis der Bearbeitungstätigkeiten

Organisationen müssen ein Verzeichnis der Bearbeitungstätigkeiten führen. Dies ist eine organisatorische Anforderung,
die keine spezifischen Plattformfunktionen benötigt.

### Rechte der betroffenen Person

Die Rechte der betroffenen Person funktionieren ähnlich wie bei der DSGVO mit geringfügigen Unterschieden. Die
Antwortzeit beträgt 30 Tage statt 1 Monat. Die Terminologie „Recht auf Vergessenwerden“ wird nicht verwendet, aber das
Recht auf Löschung existiert. Die Anforderungen an die Datenportabilität sind einfacher als bei der DSGVO. Details zur
Unterstützung dieser Rechte durch die Plattform finden Sie in der [DSGVO-Dokumentation](../2_gdpr/#data-subject-rights).

### Meldung von Datenschutzverletzungen

Das revDSG verlangt die Meldung an den Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten „so schnell wie
möglich“, wenn eine Verletzung voraussichtlich zu einem hohen Risiko für die Persönlichkeits- oder Grundrechte führt
(Artikel 24). Im Gegensatz zur DSGVO sieht das Schweizer Recht keine gesetzliche Frist vor. Die Rechtspraxis
interpretiert dies jedoch in der Regel so, dass es der 72-Stunden-Erwartung der DSGVO entspricht. Die Schwelle für die
Meldepflicht (hohes Risiko) ist strenger als die allgemeine Risikoschwelle der DSGVO. Die Plattform bietet Audit-Logs,
Monitoring und Alerting zur Unterstützung der Untersuchung und Meldung von Datenschutzverletzungen.

### Privacy by Design

Das revDSG fordert nun explizit Privacy by Design. Die Plattform setzt dies durch obligatorische
TLS/SSL-Verschlüsselung, standardmässige Zugriffsverweigerung (default-deny access control), automatische
30-Tage-Löschung von ephemeren Daten und Audit-Logging um.

## Schweizer Hosting und Angemessenheitsbeschluss

Die Schweiz verfügt über einen Angemessenheitsbeschluss der EU (bestätigt im Januar 2024), der den freien Fluss
personenbezogener Daten zwischen der EU und der Schweiz ohne zusätzliche Schutzmassnahmen ermöglicht. Dies bedeutet,
dass Schweizer Hosting die Compliance für Organisationen vereinfacht, die sowohl den Anforderungen der DSGVO als auch
des revDSG unterliegen.

Für rein schweizerische Operationen vermeidet das Hosting von Daten in der Schweiz auch die Anforderungen an
internationale Übermittlungen gemäss revDSG. Die Plattform unterstützt On-Premise- und Schweizer Cloud-Bereitstellung.
Siehe [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) und
[Internationale Datenübermittlungen nach DSGVO](../2_gdpr/#international-data-transfers).

## Datenübermittlungen

Datenübermittlungen erfordern einen angemessenen Schutz im Zielland, geeignete Schutzmassnahmen wie
Standardvertragsklauseln oder eine ausdrückliche Einwilligung. Schweizer Hosting vermeidet diese Anforderungen.
Organisationen können auch Schweizer oder EU LLM-Anbieter über LiteLLM nutzen.

## Verwandte Dokumentation

- [DSGVO](../2_gdpr/)
- [DSAR](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [EDÖB](https://www.edoeb.admin.ch/)
- [Text des revDSG](https://www.admin.ch/opc/en/classified-compilation/19920153/)

______________________________________________________________________

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie einen Rechtsbeistand oder den
Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten.
:::
