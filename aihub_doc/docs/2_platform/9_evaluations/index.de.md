---
title: Agenten-Evaluierungen
source_sha: "941d34318d931bd3bccaad6381ba4e39fec0953ca7b2d04b23ed884596d48626"
---

# Agenten-Evaluierungen

Agenten-Evaluierungen testen und messen die Qualität von KI-Agenten vor und nach der Bereitstellung. Sie erhalten Daten darüber, ob Ihre Agenten genaue, vollständige und prägnante Antworten liefern.

Evaluierungen testen Agenten anhand vordefinierter Fragen mit bekannten korrekten Antworten. Sie stellen die Fragen und erwarteten Antworten bereit, und das System misst, wie gut Ihr Agent abschneidet.

Vorteile von Evaluierungen:
- Überprüfung der Agentenleistung vor und nach der Bereitstellung
- Erhalten Sie messbare Bewertungen anstelle subjektiver Meinungen
- Verfolgen Sie Qualitätsänderungen, während Sie Wissensdatenbanken und Prompts aktualisieren
- Pflegen Sie Audit-Trails für regulatorische Anforderungen

## Datensätze

Datensätze sind Sammlungen von Testfragen mit Referenzantworten.

Behandeln Sie repräsentative Fragen, die Ihr Agent erhalten wird. Fügen Sie klare, genaue Referenzantworten und Grenzfälle hinzu. Beginnen Sie mit mindestens 10 Frage-Antwort-Paaren. 20-50 Paare funktionieren besser.

::: details Beispielstruktur eines Datensatzes
- Frage: „Wie setze ich mein Passwort zurück?"
- Referenzantwort: „Klicken Sie auf der Anmeldeseite auf ‚Passwort vergessen‘, geben Sie Ihre E-Mail-Adresse ein und folgen Sie dem an Ihren Posteingang gesendeten Link zum Zurücksetzen."
:::

Um einen Datensatz zu erstellen, navigieren Sie zum Evaluierungsdienst (unter `Services > Evaluations`), geben Sie einen Namen und eine Beschreibung ein, fügen Sie Fragen und erwartete Antworten hinzu und speichern Sie dann.

![Datensatz-Übersicht](../../../media/evaluation/dataset_overview.png)
*Übersicht der Datensätze, die alle Evaluierungs-Datensätze mit Erstellungsdaten zeigt*

![Erstellen eines Datensatzes](../../../media/evaluation/dataset_create.png)
*Hinzufügen von Testfragen mit erwarteten Antworten*

::: tip
Beginnen Sie mit 20-30 Fragen, die einfache und komplexe Szenarien abdecken. Aktualisieren Sie Datensätze, wenn sich Ihr Agent weiterentwickelt. Organisieren Sie sie nach Thema oder Anwendungsfall.
:::

## Experimente durchführen

Experimente testen Ihren Agenten anhand eines Datensatzes und erstellen Qualitätsbewertungen.

Um ein Experiment durchzuführen, wählen Sie einen Agenten aus, wählen Sie einen Testdatensatz, starten Sie das Experiment und überprüfen Sie dann die Bewertungen und die Analyse.

![Erstellen eines Experiments](../../../media/evaluation/experiment_create.png)
*Erstellen eines Experiments durch Auswahl eines Agenten und Datensatzes*

![Experiment-Übersicht](../../../media/evaluation/experiment_overview.png)
*Übersicht der Experimente, die vergangene Experimente auflistet – klicken Sie für Details*

![Durchführen eines Experiments](../../../media/evaluation/experiment_running.png)
*Fortschritt des Experiments während der Ausführung*

Führen Sie Experimente durch, bevor Sie einen neuen Agenten bereitstellen, nach signifikanten Änderungen an der Konfiguration oder Wissensdatenbank und regelmäßig (wöchentlich oder monatlich) zur Qualitätsüberwachung.

### Wie KI-Juroren funktionieren

Jede Frage wird an Ihren Agenten gesendet. Drei KI-Juroren (LLMs) bewerten die Antwort anhand der Referenzantwort. Die Ergebnisse werden gemittelt und als Sternebewertungen angezeigt.

### Evaluierungsmetriken

Drei Metriken, bewertet von 0-5 Sternen:

| Metrik | Beschreibung | Bewertungsrichtlinie |
|--------|-------------|--------------|
| Korrektheit | Faktische Genauigkeit im Vergleich zur Referenzantwort. Frei von Fehlinformationen, Halluzinationen oder Widersprüchen. | 5: Entspricht der Referenz<br/>3: Einige Fehler<br/>0: Falsch/Irreführend |
| Vollständigkeit | Behandelt alle Teile der Anfrage, einschließlich mehrteiliger Fragen und impliziter Bedürfnisse. | 5: Alle Teile beantwortet<br/>3: Einige Aspekte übersehen<br/>0: Unvollständig |
| Prägnanz | Effizient und direkt. Vermeidet irrelevante Abschweifungen, Redundanz oder übermäßiges Füllmaterial. | 5: Auf den Punkt<br/>3: Ausführlich<br/>0: Exzessiv |

Bewertungsbereiche:

- 4-5 Sterne: Produktionsreif.
- 3-4 Sterne: Funktioniert gut, kann aber kleinere Probleme aufweisen. Überprüfen Sie fehlschlagende Testfälle.
- Unter 3 Sternen: Vor der Bereitstellung genau überprüfen.

### Ergebnisse anzeigen

![Experimentergebnisse](../../../media/evaluation/experiment_result.png)
*Experimentergebnisse, die die Gesamtmetriken und eine detaillierte Aufschlüsselung pro Frage zeigen*

Die Ergebnisseite zeigt oben Sternebewertungen für die drei Metriken. Darunter befindet sich eine Tabelle mit jeder Testfrage, Referenzantwort, der Antwort des Agenten, den Bewertungen und der Antwortlatenz.

Erweitern Sie Fragen, um den vollständigen Text anzuzeigen. Niedrige Korrektheitsbewertungen bedeuten in der Regel Lücken in der Wissensdatenbank oder Probleme beim Abruf. Niedrige Vollständigkeitsbewertungen deuten darauf hin, dass der Agent Teile mehrteiliger Fragen übersieht. Niedrige Prägnanzbewertungen bedeuten übermäßig ausführliche Antworten.

Aktualisieren Sie die Wissensdatenbank, System-Prompts oder Abrufeinstellungen Ihres Agenten basierend auf den Ergebnissen. Führen Sie das Experiment erneut durch, um Verbesserungen zu überprüfen.

::: tip
Phoenix kann für tiefere Untersuchungen, einschließlich Konversations-Traces und roher Telemetriedaten, aufgerufen werden.
:::

## Was nicht implementiert ist

Die folgenden Funktionen sind derzeit nicht implementiert:

- Überwachung von Verzerrungen und Erkennung von Modell-Drift: Keine automatisierte Verzerrungserkennung, Fairness-Metriken oder Drift-Erkennung. Das Evaluierungs-Framework und das OpenTelemetry-Tracing bieten grundlegende Funktionen, die erweitert werden könnten.

- Produktions-A/B-Tests: Keine integrierte Traffic-Aufteilung oder parallele Tests von Agentenvarianten in der Produktion. Der Vergleich vor der Bereitstellung mittels Experimenten wird unterstützt.
