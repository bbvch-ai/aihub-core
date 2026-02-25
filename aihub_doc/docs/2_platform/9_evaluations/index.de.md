---
title: Agenten-Evaluierungen
source_sha: 6b9e16c7120a95ddaa10eacf1a96ac448b4bf7f28a2a0d4bfe5dcd384998cb61
---

# Agenten-Evaluierungen

Agenten-Evaluierungen testen und messen die Qualität von KI-Agents vor und nach dem Deployment. Sie erhalten Daten
darüber, ob Ihre Agents präzise, vollständige und prägnante Antworten liefern.

Evaluierungen testen Agents anhand vordefinierter Fragen mit bekannten korrekten Antworten. Sie stellen die Fragen und
erwarteten Antworten bereit, und das System misst, wie gut Ihr Agent performt.

Vorteile von Evaluierungen:

- Überprüfen Sie die Agent-Performance vor und nach dem Deployment
- Erhalten Sie messbare Bewertungen anstelle subjektiver Meinungen
- Verfolgen Sie Qualitätsänderungen, während Sie Wissensdatenbanken und Prompts aktualisieren
- Führen Sie Audit-Trails für regulatorische Anforderungen

## Datasets

Datasets sind Sammlungen von Testfragen mit Referenzantworten.

Decken Sie repräsentative Fragen ab, die Ihr Agent erhalten wird. Fügen Sie klare, präzise Referenzantworten und Edge
Cases hinzu. Beginnen Sie mit mindestens 10 Frage-Antwort-Paaren. 20-50 Paare funktionieren besser.

::: details Beispiel-Dataset-Struktur
- Frage: „Wie setze ich mein Passwort zurück?“
- Referenzantwort: „Klicken Sie auf der Anmeldeseite auf ‚Passwort vergessen‘, geben Sie Ihre E-Mail-Adresse ein und
  folgen Sie dem Reset-Link, der an Ihren Posteingang gesendet wird.“
:::

Um ein Dataset zu erstellen, navigieren Sie zum Evaluierungs-Service (unter `Services > Evaluations`), geben Sie einen
Namen und eine Beschreibung an, fügen Sie Fragen und erwartete Antworten hinzu und speichern Sie dann.

![Dataset Overview](../../../media/evaluation/dataset_overview.png) *Dataset-Übersicht mit allen Evaluierungs-Datasets
und Erstellungsdaten*

![Creating a Dataset](../../../media/evaluation/dataset_create.png) *Hinzufügen von Testfragen mit erwarteten Antworten*

::: tip
Beginnen Sie mit 20-30 Fragen, die einfache und komplexe Szenarien abdecken. Aktualisieren Sie Datasets, während sich
Ihr Agent weiterentwickelt. Organisieren Sie nach Thema oder Anwendungsfall.
:::

## Experimente ausführen

Experimente testen Ihren Agenten anhand eines Datasets und erstellen Qualitätsbewertungen.

Um ein Experiment auszuführen, wählen Sie einen Agenten aus, wählen Sie ein Test-Dataset, starten Sie das Experiment und
überprüfen Sie dann die Bewertungen und die Analyse.

![Creating an Experiment](../../../media/evaluation/experiment_create.png) *Erstellen eines Experiments durch Auswahl
eines Agenten und Datasets*

![Experiment Overview](../../../media/evaluation/experiment_overview.png) *Experiment-Übersicht, die vergangene
Experimente auflistet – klicken Sie für Details*

![Running an Experiment](../../../media/evaluation/experiment_running.png) *Experiment-Fortschritt während der
Ausführung*

Führen Sie Experimente aus, bevor Sie einen neuen Agenten deployen, nachdem Sie signifikante Änderungen an der
Konfiguration oder der Wissensdatenbank vorgenommen haben, und regelmäßig (wöchentlich oder monatlich) zur
Qualitätsüberwachung.

### Wie KI-Richter arbeiten

Jede Frage wird an Ihren Agenten gesendet. Drei KI-Richter (LLMs) bewerten die Antwort im Vergleich zur Referenzantwort.
Die Ergebnisse werden gemittelt und als Sternebewertungen angezeigt.

### Evaluierungsmetriken

Drei Metriken, bewertet von 0-5 Sternen:

| Metrik          | Beschreibung                                                                                                            | Bewertungsleitfaden                                                         |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Korrektheit     | Faktische Genauigkeit im Vergleich zur Referenzantwort. Frei von Fehlinformationen, Halluzinationen oder Widersprüchen. | 5: Entspricht Referenz<br/>3: Einige Fehler<br/>0: Falsch/irreführend       |
| Vollständigkeit | Beantwortet alle Teile der Anfrage, einschließlich mehrteiliger Fragen und impliziter Bedürfnisse.                      | 5: Alle Teile beantwortet<br/>3: Einige Aspekte fehlen<br/>0: Unvollständig |
| Prägnanz        | Effizient und direkt. Vermeidet irrelevante Abschweifungen, Redundanz oder übermäßiges Füllmaterial.                    | 5: Auf den Punkt<br/>3: Ausführlich<br/>0: Übermäßig                        |

Bewertungsskalen:

- 4-5 Sterne: Produktionsreif.
- 3-4 Sterne: Funktioniert gut, kann aber kleinere Probleme aufweisen. Überprüfen Sie fehlschlagende Testfälle.
- Unter 3 Sternen: Vor dem Deployment genau überprüfen.

### Ergebnisse anzeigen

![Experiment Results](../../../media/evaluation/experiment_result.png) *Experimentergebnisse, die Gesamtmetriken und
detaillierte Aufschlüsselung pro Frage zeigen*

Die Ergebnisseite zeigt Sternebewertungen für die drei Metriken oben. Darunter befindet sich eine Tabelle mit jeder
Testfrage, Referenzantwort, der Antwort des Agenten, Bewertungen und der Antwortlatenz.

Erweitern Sie Fragen, um den vollständigen Text anzuzeigen. Niedrige Korrektheitsbewertungen bedeuten in der Regel
Lücken in der Wissensdatenbank oder Retrieval-Probleme. Niedrige Vollständigkeitsbewertungen deuten darauf hin, dass der
Agent Teile von mehrteiligen Fragen übersieht. Niedrige Prägnanzbewertungen bedeuten übermäßig ausführliche Antworten.

Aktualisieren Sie die Wissensdatenbank, System-Prompts oder Retrieval-Einstellungen Ihres Agenten basierend auf den
Ergebnissen. Führen Sie das Experiment erneut aus, um Verbesserungen zu überprüfen.

::: tip
Langfuse kann für eine tiefere Untersuchung genutzt werden, einschließlich Konversations-Traces, Kostenattribution und
Roh-Telemetriedaten. Während der Entwicklung können Sie Langfuse unter `http://localhost:6006` aufrufen.
:::

## Nicht implementierte Funktionen

Die folgenden Funktionen sind derzeit nicht implementiert:

- Bias-Monitoring und Modell-Drift-Erkennung: Keine automatisierte Bias-Erkennung, Fairness-Metriken oder
  Drift-Erkennung. Das Evaluierungs-Framework und OpenTelemetry-Tracing bieten grundlegende Fähigkeiten, die erweitert
  werden könnten.

- Produktions-A/B-Testing: Keine integrierte Traffic-Aufteilung oder paralleles Testen von Agent-Varianten in
  Produktion. Der Pre-Deployment-Vergleich mittels Experimenten wird unterstützt.
