# Kapitel 07: Datensicherheit und Datenfluss

## Kapitelziel

Dieses Kapitel legt dar, wie die Integrität, Vertraulichkeit und Verfügbarkeit von Daten über ihren gesamten
Lebenszyklus hinweg – von der Erfassung über die Verarbeitung bis hin zur Ausgabe – durchgängig gewährleistet wird. Es
beschreibt die Sicherheitsarchitektur zur Härtung aller Ein- und Austrittspunkte, um manipulative Eingaben abzuwehren
und unbeabsichtigten Datenabfluss zu verhindern. Ein zentraler Schwerpunkt liegt auf dem Schutz sensibler Informationen
(PII), unter anderem durch automatisierte Anonymisierungsverfahren vor der Übergabe an verarbeitende Logiken oder
Sprachmodelle. Des Weiteren wird aufgezeigt, wie durch strikte logische Mandantentrennung sowie durchgehende
Verschlüsselung (Data-at-Rest und Data-in-Transit) ein Höchstmaß an Sicherheit realisiert wird. Abschließend werden die
Mechanismen zur revisionssicheren Datenlöschung sowie das kontinuierliche Monitoring zur frühzeitigen Erkennung von
Anomalien im Datenfluss erläutert.

## Kernaussagen

- Schutz vor KI-spezifischen Angriffen: Die Sicherheitsarchitektur implementiert spezialisierte Filtermechanismen
  ("Input Guardrails"), die Angriffe wie Prompt-Injection oder Jailbreaking-Versuche erkennen und blockieren, bevor sie
  die Sprachmodelle erreichen.
- Automatisierte PII-Anonymisierung: Integrierte Erkennungsverfahren identifizieren personenbezogene Daten (PII) im
  Datenstrom und anonymisieren oder schwärzen diese dynamisch, um einen ungewollten Abfluss sensibler Informationen an
  LLMs zu verhindern.
- Durchgängige Verschlüsselung: Sämtliche Datenbewegungen werden durch moderne kryptografische Standards (TLS/mTLS)
  geschützt (Data-in-Transit), während gespeicherte Informationen – von Vektordatenbanken bis zu Logs – verschlüsselt
  abgelegt werden (Data-at-Rest).
- Isolation und Mandantentrennung: Eine strikte logische Trennung der Datenräume gewährleistet, dass Informationen
  verschiedener Mandanten oder Abteilungen isoliert verarbeitet werden und keine Überschneidungen (Data Leaks) zwischen
  getrennten Kontexten auftreten.
- Sichere Ein- und Ausgabe-Filterung: Neben der Eingabevalidierung werden auch die generierten KI-Antworten vor der
  Ausspielung auf sensible Inhalte oder Schadcode geprüft, um die Sicherheit der Endanwender zu garantieren.
- Data Loss Prevention (DLP): Kontinuierliche Analysen der Datenströme überwachen auf Anomalien und verhindern exzessive
  Datenexporte oder ungewöhnliche Zugriffsmuster, die auf eine Kompromittierung hindeuten könnten.
- Revisionssichere Löschverfahren: Systematische Löschprozesse stellen sicher, dass Daten auf Anfrage (z. B. „Recht auf
  Vergessenwerden“) nicht nur aus dem Index, sondern auch unwiderruflich aus den Vektorspeichern und Caches entfernt
  werden.

## Umfang

max. 1200 Wörter, 4 Seiten

## Business-Fragen, die das Kapitel beantwortet

- Wie werden User-Eingaben gegen Injection-Attacks geschützt?
- Was ist Prompt-Injection und wie wird dagegen geschützt?
- Wie werden hochgeladene Dokumente auf Malware geprüft?
- Schützt die Plattform vor Advanced Persistent Threats (APTs)?
- Wie werden externe Datenquellen sicher angebunden?
- Welche Authentifizierungsmethoden werden für API-Integrationen unterstützt?
- Wie wird vor API-Missbrauch und DoS geschützt (Rate-Limiting)?
- Wie erkennt die Plattform personenbezogene Daten (PII)?
- Wird PII automatisch anonymisiert oder geschwärzt?
- Wie wird verhindert, dass sensible Daten an LLM-Provider gesendet werden?
- Sind Transformations-Pipelines isoliert und auditiert?
- Wie werden Embeddings in Vector-Datenbanken geschützt?
- Wie wird Chat-Kontext verschlüsselt und wann wird er gelöscht?
- Wie wird die Kommunikation mit LLM-Providern gesichert?
- Werden Daten bei LLM-Providern gespeichert (Retention)?
- Kann die Plattform komplett offline betrieben werden (Air-Gap)?
- Wie werden Quellenangaben DSGVO-konform dargestellt?
- Werden sensible Daten automatisch aus AI-Antworten gefiltert?
- Wie werden Daten-Exports gesichert?
- Wie werden Logs an externe SIEM-Systeme sicher übertragen?
- Sind Daten im Ruhezustand verschlüsselt (Data-at-Rest)?
- Wie funktioniert Key-Management (HSM, KMS)?
- Ist alle Netzwerk-Kommunikation verschlüsselt (SSL/TLS)?
- Wird Perfect Forward Secrecy (PFS) unterstützt?
- Wird Mutual TLS (mTLS) für Service-to-Service-Kommunikation verwendet?
- Wie werden Daten verschiedener Organisationen getrennt (Multi-Tenant-Isolation)?
- Ist physische Isolation für besonders sensible Organisationen möglich?
- Wie werden Daten vollständig gelöscht (Right to be Forgotten)?
- Werden gelöschte Daten wirklich überschrieben (Secure-Delete)?
- Wie kann ich nachweisen, dass Daten gelöscht wurden (Audit-Trail)?
- Wie werden Datenflüsse überwacht?
- Erkennt die Plattform Anomalien und verdächtige Datentransfers?
- Gibt es Data Exfiltration Prevention (DLP)?
- Wie funktioniert Incident-Response bei Sicherheitsvorfällen?
- Werden regelmäßig Penetration-Tests durchgeführt?
