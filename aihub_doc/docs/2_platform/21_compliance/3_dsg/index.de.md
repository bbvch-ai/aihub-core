---
title: Schweizer Datenschutzgesetz (DSG)
source_sha: 32338ef47291fea7179109d797b13227c73d10c77244bb6f7121a722cc648c70
---

# Schweizer Datenschutzgesetz (revDSG)

Das revidierte Schweizer Bundesgesetz über den Datenschutz (revDSG) ist am 1. September 2023 in Kraft getreten. Die
Revision zielte darauf ab, die Standards des EU-Datenschutzes zu berücksichtigen, während gleichzeitig
schweizspezifische Ansätze für bestimmte Anforderungen beibehalten wurden.

:::info
Siehe [DSGVO-Konformität](../2_gdpr/) für gemeinsame Anforderungen. Dieses Dokument behandelt nur schweizspezifische
Unterschiede.
:::

:::warning Wann die DSGVO ebenfalls gilt
Schweizer Organisationen müssen sowohl dem revDSG als auch der DSGVO entsprechen, wenn sie Waren/Dienstleistungen für
EU-Bürger anbieten oder das Verhalten von Personen in der EU überwachen. Siehe
[Anwendbarkeit der DSGVO](../2_gdpr/#applicability-to-swiss-organizations).
:::

## Wesentliche Unterschiede zur DSGVO

| Aspekt                              | revDSG                                                                      | DSGVO                                                                                     |
| :---------------------------------- | :-------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- |
| Bussgelder                          | Bis zu CHF 250.000 für Einzelpersonen (nicht für Unternehmen)               | Bis zu 20 Mio. € oder 4 % des Umsatzes für Unternehmen                                    |
| DSB (Datenschutzbeauftragter)       | Nicht erforderlich                                                          | Oft obligatorisch                                                                         |
| Rechtsgrundlage                     | Keine explizite Rechtsgrundlage erforderlich (anderer Ansatz)               | Explizite Rechtsgrundlage obligatorisch (Art. 6)                                          |
| Meldung von Datenschutzverletzungen | „So rasch wie möglich“, wenn hohes Risiko besteht (keine gesetzliche Frist) | Ohne unnötige Verzögerung, wenn möglich innerhalb von 72 Stunden, wenn ein Risiko besteht |
| Besonders schützenswerte Daten      | Umfasst Daten über Verwaltungs- / Strafverfahren + Sozialversicherungsdaten | 9 besondere Kategorien                                                                    |
| Geltungsbereich                     | Nur natürliche Personen (juristische Personen seit 2023 ausgeschlossen)     | Nur natürliche Personen                                                                   |

## revDSG-spezifische Anforderungen

### Profiling mit hohem Risiko

Das revDSG verlangt eine Aufsicht für die automatisierte Bewertung persönlicher Aspekte wie Risikobewertung und
Verhaltensvorhersage. Die Plattform bietet Human-in-the-Loop-Funktionen, Langfuse-Tracing und Quellenzuordnung, um diese
Anforderung zu unterstützen. Organisationen müssen Profiling-Aktivitäten mit hohem Risiko identifizieren,
Datenschutz-Folgenabschätzungen durchführen und eine geeignete menschliche Aufsicht implementieren.

### Verzeichnis der Bearbeitungstätigkeiten

Organisationen müssen ein Verzeichnis der Bearbeitungstätigkeiten führen. Dies ist eine organisatorische Anforderung,
die keine Plattformfunktionen benötigt.

### Betroffenenrechte

Die Betroffenenrechte funktionieren ähnlich wie bei der DSGVO mit geringfügigen Unterschieden. Die Antwortzeit beträgt
30 Tage anstatt 1 Monat. Die Terminologie „Recht auf Vergessenwerden“ wird nicht verwendet, aber das Recht auf Löschung
besteht. Die Anforderungen an die Datenportabilität sind einfacher als bei der DSGVO. Siehe
[DSGVO-Dokumentation](../2_gdpr/#data-subject-rights) für Details, wie die Plattform diese Rechte unterstützt.

### Meldung von Datenschutzverletzungen

Das revDSG verlangt die Meldung von Datenschutzverletzungen an den Eidgenössischen Datenschutz- und
Öffentlichkeitsbeauftragten „so rasch wie möglich“, wenn eine Verletzung voraussichtlich zu einem hohen Risiko für die
Persönlichkeits- oder Grundrechte führt (Artikel 24). Im Gegensatz zur DSGVO legt das Schweizer Recht keine gesetzliche
Frist fest. Die Rechtspraxis interpretiert dies jedoch im Allgemeinen so, dass es der 72-Stunden-Erwartung der DSGVO
entspricht. Die Schwelle für die Meldung (hohes Risiko) ist strenger als die allgemeine Risikoschwelle der DSGVO. Die
Plattform bietet Audit-Logs, Monitoring und Alerting, um die Untersuchung und Meldung von Datenschutzverletzungen zu
unterstützen.

### Datenschutz durch Technikgestaltung

Das revDSG fordert nun explizit Datenschutz durch Technikgestaltung (Privacy by Design). Die Plattform setzt dies durch
obligatorische TLS/SSL-Verschlüsselung, Default-Deny-Zugriffskontrolle, 30-tägige automatische Löschung von ephemeren
Daten und Audit-Logging um.

## Schweizer Hosting und Angemessenheitsbeschluss

Die Schweiz verfügt über einen Angemessenheitsbeschluss der EU (bestätigt im Januar 2024), der den freien Fluss
personenbezogener Daten zwischen der EU und der Schweiz ohne zusätzliche Schutzmassnahmen ermöglicht. Dies bedeutet,
dass Schweizer Hosting die Compliance für Organisationen vereinfacht, die sowohl den Anforderungen der DSGVO als auch
des revDSG unterliegen.

Für rein schweizerische Operationen vermeidet das Hosten von Daten in der Schweiz auch die Anforderungen an
internationale Transfers gemäss revDSG. Die Plattform unterstützt On-Premise- und Schweizer Cloud-Deployments. Siehe
[Deployment-Optionen](../../3_deployment_guide/1_deployment_options/) und
[Internationale Datentransfers der DSGVO](../2_gdpr/#international-data-transfers).

## Datentransfers

Datentransfers erfordern einen angemessenen Schutz im Zielland, geeignete Garantien wie Standardvertragsklauseln oder
eine explizite Einwilligung. Schweizer Hosting vermeidet diese Anforderungen. Organisationen können auch Schweizer oder
EU-LLM-Anbieter über LiteLLM nutzen.

## Zugehörige Dokumentation

- [DSGVO](../2_gdpr/)
- [DSAR](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [EDÖB](https://www.edoeb.admin.ch/)
- [revDSG Gesetzestext](https://www.admin.ch/opc/en/classified-compilation/19920153/)

______________________________________________________________________

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie einen Rechtsberater oder den
Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten.
:::
