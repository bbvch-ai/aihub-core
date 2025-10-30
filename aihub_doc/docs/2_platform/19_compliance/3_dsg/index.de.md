---
title: Schweizer Datenschutzgesetz (DSG)
source_sha: 432a306cad6bcebfb8cbeb0ef53aaefbe7740523f1ffada85799b074f4b0dc01
---

# Schweizer Datenschutzgesetz (revDSG)

Das revidierte Schweizer Bundesgesetz über den Datenschutz (revDSG/FADP) ist am 1. September 2023 in Kraft getreten. Die
Revision wurde darauf ausgelegt, sich an den EU-Datenschutzstandards zu orientieren, während gleichzeitig
schweizspezifische Ansätze für bestimmte Anforderungen beibehalten wurden.

:::info
Siehe [DSGVO-Konformität](../2_gdpr/) für gemeinsame Anforderungen. Dieses Dokument behandelt ausschliesslich
schweizspezifische Unterschiede.
:::

:::warning Wann auch die DSGVO gilt
Schweizer Organisationen müssen sowohl dem revDSG als auch der DSGVO entsprechen, wenn sie Waren/Dienstleistungen für
EU-Bürger anbieten oder das Verhalten von EU-Personen überwachen. Siehe
[Anwendbarkeit der DSGVO auf Schweizer Organisationen](../2_gdpr/#applicability-to-swiss-organizations).
:::

## Wesentliche Unterschiede zur DSGVO

| Aspekt                         | revDSG                                                                  | DSGVO                                                                                     |
| :----------------------------- | :---------------------------------------------------------------------- | :---------------------------------------------------------------------------------------- |
| Bussgelder                     | Bis zu CHF 250'000 für Einzelpersonen (nicht für Unternehmen)           | Bis zu 20 Mio. € oder 4% des Umsatzes für Unternehmen                                     |
| DPO                            | Nicht erforderlich                                                      | Oft obligatorisch                                                                         |
| Rechtsgrundlage                | Keine explizite Rechtsgrundlage erforderlich (anderer Ansatz)           | Explizite Rechtsgrundlage obligatorisch (Art. 6)                                          |
| Meldung von Datenpannen        | „So schnell wie möglich“, wenn hohes Risiko (keine gesetzl. Frist)      | Ohne unnötige Verzögerung, wenn möglich innerhalb von 72 Stunden, wenn ein Risiko besteht |
| Besonders schützenswerte Daten | Umfasst Administrativ-/Strafverfahren + Sozialversicherungsdaten        | 9 besondere Kategorien                                                                    |
| Geltungsbereich                | Nur natürliche Personen (juristische Personen seit 2023 ausgeschlossen) | Nur natürliche Personen                                                                   |

## revDSG-spezifische Anforderungen

### Hochrisikoprofiling

Das revDSG verlangt eine Aufsicht bei der automatisierten Bewertung persönlicher Aspekte wie Risikobewertung und
Verhaltensprognose. Die Plattform bietet Human-in-the-Loop-Funktionen, Phoenix-Tracing und Quellenattribution, um diese
Anforderung zu unterstützen. Organisationen müssen Hochrisikoprofiling-Aktivitäten identifizieren,
Datenschutz-Folgenabschätzungen durchführen und eine angemessene menschliche Aufsicht implementieren.

### Verzeichnis der Bearbeitungstätigkeiten

Organisationen müssen ein Verzeichnis der Bearbeitungstätigkeiten führen. Dies ist eine organisatorische Anforderung,
die keine Plattformfunktionen benötigt.

### Betroffenenrechte

Betroffenenrechte funktionieren ähnlich wie bei der DSGVO mit geringfügigen Unterschieden. Die Reaktionszeit beträgt 30
Tage anstatt 1 Monat. Die Terminologie „Recht auf Vergessenwerden“ wird nicht verwendet, aber das Recht auf Löschung
besteht. Die Portabilitätsanforderungen sind einfacher als bei der DSGVO. Siehe
[DSGVO-Dokumentation](../2_gdpr/#data-subject-rights) für Details, wie die Plattform diese Rechte unterstützt.

### Meldung von Datenschutzverletzungen

Das revDSG verlangt die Meldung an den Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten „so schnell wie
möglich“, wenn eine Verletzung voraussichtlich zu einem hohen Risiko für die Persönlichkeits- oder Grundrechte führt
(Artikel 24). Im Gegensatz zur DSGVO sieht das schweizerische Recht keine gesetzliche Frist vor. Die Rechtspraxis
interpretiert dies jedoch im Allgemeinen so, dass es der 72-Stunden-Erwartung der DSGVO entspricht. Die Schwelle für die
Meldepflicht (hohes Risiko) ist strenger als die allgemeine Risikoschwelle der DSGVO. Die Plattform bietet Audit-Logs,
Monitoring und Alerting zur Unterstützung von Untersuchungs- und Meldeverfahren bei Datenschutzverletzungen.

### Datenschutz durch Technikgestaltung (Privacy by Design)

Das revDSG verlangt nun explizit Datenschutz durch Technikgestaltung (Privacy by Design). Die Plattform implementiert
dies durch obligatorische TLS/SSL-Verschlüsselung, Default-Deny-Zugriffskontrolle, automatische Löschung temporärer
Daten nach 30 Tagen und Audit-Logging.

## Schweizer Hosting und Angemessenheitsbeschluss

Die Schweiz verfügt über einen EU-Angemessenheitsbeschluss (im Januar 2024 bestätigt), der den freien Fluss
personenbezogener Daten zwischen der EU und der Schweiz ohne zusätzliche Schutzmassnahmen ermöglicht. Dies bedeutet,
dass Schweizer Hosting die Compliance für Organisationen vereinfacht, die sowohl den Anforderungen der DSGVO als auch
des revDSG unterliegen.

Für rein schweizerische Operationen vermeidet das Hosting von Daten in der Schweiz auch internationale
Übertragungsanforderungen gemäss revDSG. Die Plattform unterstützt On-Premise- und Schweizer Cloud-Deployments. Siehe
[Bereitstellungsoptionen](/de/docs/2_platform/3_deployment_guide/1_deployment_options/) und
[DSGVO Internationale Datenübermittlungen](../2_gdpr/#international-data-transfers).

## Datenübermittlungen

Datenübermittlungen erfordern einen angemessenen Schutz im Zielland, geeignete Garantien wie Standardvertragsklauseln
oder eine explizite Einwilligung. Schweizer Hosting vermeidet diese Anforderungen. Organisationen können auch Schweizer
oder EU LLM-Anbieter über LiteLLM nutzen.

## Verwandte Dokumentation

- [DSGVO](../2_gdpr/)
- [DSAR](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [EDÖB](https://www.edoeb.admin.ch/)
- [revDSG Text](https://www.admin.ch/opc/en/classified-compilation/19920153/)

---

:::info Rechtlicher Hinweis
Dies ist technische Dokumentation, keine Rechtsberatung. Konsultieren Sie einen Rechtsbeistand oder den Eidgenössischen
Datenschutz- und Öffentlichkeitsbeauftragten.
:::
