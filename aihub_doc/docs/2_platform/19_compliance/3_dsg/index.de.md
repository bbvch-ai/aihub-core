---
title: Schweizer Datenschutzgesetz (DSG)
source_sha: "710330de8ba2171f821b4741c6e886b6bc4de4883668c2c3620d86a68adf7f5b"
---

# Schweizer Datenschutzgesetz (revDSG)

Das revidierte Schweizer Bundesgesetz über den Datenschutz (revDSG/FADP) ist am 1. September 2023 in Kraft getreten. Die Revision wurde entwickelt, um die EU-Datenschutzstandards zu erfüllen, während gleichzeitig schweizspezifische Ansätze für bestimmte Anforderungen beibehalten wurden.

:::info
Gemeinsame Anforderungen finden Sie unter [GDPR-Konformität](../2_gdpr/). Dieses Dokument behandelt nur die schweizspezifischen Unterschiede.
:::

:::warning Wann die GDPR ebenfalls gilt
Schweizer Organisationen müssen sowohl das revDSG als auch die GDPR einhalten, wenn sie Waren/Dienstleistungen für EU-Bürger anbieten oder das Verhalten von Personen in der EU überwachen. Siehe [Anwendbarkeit der GDPR auf Schweizer Organisationen](../2_gdpr/#applicability-to-swiss-organizations).
:::

## Wesentliche Unterschiede zur GDPR

| Aspekt | revDSG | GDPR |
|--------|---------|------|
| Bussen | Bis zu CHF 250K für Einzelpersonen (nicht für Unternehmen) | Bis zu €20M oder 4% des Jahresumsatzes für Unternehmen |
| DSB | Nicht erforderlich | Oft obligatorisch |
| Rechtsgrundlage | Keine explizite Rechtsgrundlage erforderlich (anderer Ansatz) | Explizite Rechtsgrundlage obligatorisch (Art. 6) |
| Meldung von Datenschutzverletzungen | „So schnell wie möglich“, wenn hohes Risiko (keine gesetzliche Frist) | Ohne unangemessene Verzögerung, wenn möglich innerhalb von 72 Stunden, falls ein Risiko besteht |
| Sensible Daten | Umfasst administrative/strafrechtliche Verfahren + Sozialversicherungsdaten | 9 besondere Kategorien |
| Geltungsbereich | Nur natürliche Personen (juristische Personen seit 2023 ausgeschlossen) | Nur natürliche Personen |

## revDSG-spezifische Anforderungen

### Hochrisikoprofiling
Das revDSG erfordert eine Aufsicht bei der automatisierten Bewertung persönlicher Aspekte wie Risikobewertung und Verhaltensvorhersage. Die Plattform bietet Human-in-the-Loop-Funktionen, Phoenix-Tracing und Quellenattribution, um diese Anforderung zu unterstützen. Organisationen müssen Hochrisikoprofiling-Aktivitäten identifizieren, Datenschutz-Folgenabschätzungen durchführen und eine angemessene menschliche Aufsicht implementieren.

### Verzeichnis der Bearbeitungstätigkeiten
Organisationen müssen ein Verzeichnis der Bearbeitungstätigkeiten führen. Dies ist eine organisatorische Anforderung, die keine Plattformfunktionen benötigt.

### Rechte der betroffenen Personen
Die Rechte der betroffenen Personen funktionieren ähnlich wie bei der GDPR, mit geringfügigen Unterschieden. Die Antwortfrist beträgt 30 Tage anstatt 1 Monat. Die Terminologie „Recht auf Vergessenwerden" wird nicht verwendet, aber das Recht auf Löschung besteht. Die Portabilitätsanforderungen sind einfacher als bei der GDPR. Einzelheiten zur Unterstützung dieser Rechte durch die Plattform finden Sie in der [GDPR-Dokumentation](../2_gdpr/#data-subject-rights).

### Meldung von Datenschutzverletzungen
Das revDSG verlangt die Benachrichtigung des Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten (EDÖB) „so rasch wie möglich“, wenn eine Verletzung voraussichtlich zu einem hohen Risiko für die Persönlichkeitsrechte oder Grundrechte führt (Artikel 24). Anders als die GDPR sieht das Schweizer Recht keine gesetzliche Frist vor. Die Rechtspraxis interpretiert dies jedoch im Allgemeinen so, dass es der 72-Stunden-Erwartung der GDPR entspricht. Die Schwelle für die Meldepflicht (hohes Risiko) ist strenger als die allgemeine Risikoschwelle der GDPR. Die Plattform bietet Audit-Logs, Monitoring und Alerting zur Unterstützung der Untersuchung und Meldung von Verletzungen.

### Datenschutz durch Technikgestaltung (Privacy by Design)
Das revDSG fordert nun explizit den Datenschutz durch Technikgestaltung (Privacy by Design). Die Plattform setzt dies durch obligatorische TLS/SSL-Verschlüsselung, zugriffsverweigernde Standardeinstellungen, automatische Löschung temporärer Daten nach 30 Tagen und Audit-Logging um.

## Schweizer Hosting und Angemessenheitsentscheid

Die Schweiz verfügt über einen EU-Angemessenheitsentscheid (bestätigt im Januar 2024), der den freien Fluss personenbezogener Daten zwischen der EU und der Schweiz ohne zusätzliche Schutzmassnahmen ermöglicht. Dies bedeutet, dass Schweizer Hosting die Compliance für Organisationen vereinfacht, die sowohl den GDPR- als auch den revDSG-Anforderungen unterliegen.

Für reine Schweizer Operationen vermeidet das Hosten von Daten in der Schweiz auch internationale Übermittlungsanforderungen gemäss revDSG. Die Plattform unterstützt On-Premise- und Schweizer Cloud-Bereitstellung. Siehe [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) und [GDPR: Internationale Datenübermittlungen](../2_gdpr/#international-data-transfers).

## Datenübermittlungen

Datenübermittlungen erfordern einen angemessenen Schutz im Zielland, geeignete Garantien wie Standardvertragsklauseln oder eine ausdrückliche Einwilligung. Schweizer Hosting vermeidet diese Anforderungen. Organisationen können auch Schweizer oder EU LLM-Anbieter über LiteLLM nutzen.

## Verwandte Dokumentation

- [GDPR](../2_gdpr/)
- [DSAR](../6_data_subject_requests/)
- [Datenaufbewahrung](../1_data_retention/)
- [EDÖB](https://www.edoeb.admin.ch/)
- [Text des revDSG](https://www.admin.ch/opc/en/classified-compilation/19920153/)

---

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie einen Rechtsberater oder den Eidgenössischen Datenschutz- und Öffentlichkeitsbeauftragten (EDÖB).
:::
