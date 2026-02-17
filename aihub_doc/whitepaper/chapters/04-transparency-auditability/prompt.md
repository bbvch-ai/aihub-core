# Kapitel 04: Plattform-Transparenz und Prüfbarkeit

## Kapitelziel

Dieses Kapitel legt dar, wie die Plattform durchgängige Transparenz und lückenlose Überwachbarkeit (Observability) über
sämtliche Systemgrenzen und KI-Interaktionen hinweg gewährleistet. Es wird erläutert, wie durch einen „White-Box“-Ansatz
komplexe Entscheidungsketten der KI bis auf den einzelnen Verarbeitungsschritt und die genutzte Datenquelle (Data
Lineage) verständlich und auditierbar gemacht werden, um regulatorische Anforderungen sowie interne
Compliance-Richtlinien sicher zu erfüllen. Der Abschnitt beschreibt zudem, wie unveränderliche Audit-Trails und
Mechanismen zur menschlichen Überprüfung (Human-in-the-Loop) die Risikominimierung bei kritischen Entscheidungen
unterstützen und eine präzise Kostenkontrolle ermöglichen. Abschließend wird aufgezeigt, wie sich diese Analyse- und
Protokolldaten standardkonform in bestehende Monitoring-Landschaften integrieren lassen, um eine langfristige
forensische Auswertbarkeit und Qualitätssicherung sicherzustellen.

## Kernaussagen

- Nachvollziehbarkeit (Explainability): Die Plattformarchitektur überwindet den „Black-Box“-Ansatz, indem sie die
  einzelnen Verarbeitungsschritte und Reasoning-Prozesse der KI transparent macht und so eine klare Nachvollziehbarkeit
  von Antworten ermöglicht.
- Revisionssichere Protokollierung (Audit): Das System erstellt unveränderliche Audit-Trails für sämtliche Interaktionen
  und Systemaufrufe, um eine lückenlose Beweiskette für interne Revisionen oder regulatorische Prüfungen
  bereitzustellen.
- Datenherkunft (Data Lineage): Zur Validierung von RAG-Antworten wird exakt protokolliert, welche spezifischen
  Dokumente, Versionen oder Chunks als Quellinformation für eine KI-Entscheidung herangezogen wurden.
- Überwachbarkeit (Observability): Die Plattform unterstützt offene Standards (wie OpenTelemetry) und ermöglicht den
  Export von Log-Daten, um eine nahtlose Integration in bestehende zentrale Monitoring- und SIEM-Landschaften der
  Organisation zu gewährleisten.
- Menschliche Kontrolle (Human-in-the-Loop): Kritische Entscheidungsprozesse können durch „Human-in-the-Loop“-Workflows
  abgesichert werden, wobei menschliche Eingriffe oder Korrekturen ebenfalls revisionssicher dokumentiert werden.
- Kostentransparenz (FinOps): Detaillierte Monitoring-Funktionen erfassen die Token-Nutzung und LLM-Aufrufe, um eine
  präzise Kostenkontrolle und eine verursachergerechte Verrechnung auf Abteilungs- oder Projektebene zu ermöglichen.

## Umfang

max. 1200 Wörter, 4 Seiten

## Business-Fragen, die das Kapitel beantwortet

- Wie kann ich nachvollziehen, wie die AI zu einer bestimmten Antwort gekommen ist?
- Werden alle AI-Entscheidungen protokolliert und sind diese Protokolle einsehbar?
- Was unterscheidet die Workflow-basierte Architektur von Black-Box-AI-Systemen?
- Kann ich die Reasoning-Prozesse der AI nachvollziehen?
- Wie transparent sind LLM-Aufrufe (Prompts, Responses)?
- Welche Tools und externe Systeme ruft die AI auf?
- Wie erfüllt die Plattform Audit-Trail-Anforderungen für regulierte Branchen?
- Sind Logs unveränderlich und manipulationssicher?
- Wie lange werden Audit-Trails aufbewahrt?
- Kann ich Audit-Trails für regulatorische Prüfungen exportieren?
- Wie weise ich nach, dass Datenverarbeitung rechtmäßig erfolgt ist?
- Unterstützt die Plattform Auskunftsrechte nach revDSG (Art. 25)?
- Wie kann ich nachvollziehen, welche Dokumente für eine AI-Antwort verwendet wurden?
- Wird die Herkunft und Verarbeitung von Dokumenten lückenlos dokumentiert?
- Wie werden Dokumentversionen verfolgt?
- Kann ich sehen, welche Dokument-Chunks in welchen Antworten verwendet wurden?
- Welche Monitoring-Tools sind in die Plattform integriert?
- Wie überwache ich die Performance und Kosten der AI-Nutzung?
- Kann ich Dashboards und Alerts für kritische Metriken konfigurieren?
- Werden moderne Standards wie OpenTelemetry unterstützt?
- Kann ich Logs in unsere bestehenden Monitoring-Systeme exportieren?
- Wie stelle ich sicher, dass kritische AI-Entscheidungen von Menschen überprüft werden?
- Werden menschliche Überprüfungen und Overrides dokumentiert?
- Wie integriere ich Nutzer-Feedback zur Qualitätsverbesserung?
- Gibt es Eskalationsmechanismen bei problematischen AI-Outputs?
- Wie werden AI-Kosten (Token-Nutzung, LLM-Aufrufe) nachverfolgt?
- Kann ich Kosten pro User, Abteilung oder Projekt aufschlüsseln?
- Wie identifiziere ich teure Queries zur Optimierung?
