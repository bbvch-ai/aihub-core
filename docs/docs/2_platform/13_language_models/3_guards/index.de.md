---
title: LLM-Guards
source_sha: 0e3c34177b02b1d8d26314b3bf360cc16e3f964c64f9a8ceae5e11e518caf2d3
---

# LLM-Guards

Guards überprüfen KI-Agent-Interaktionen in Echtzeit. Sie fangen unangemessene Fragen ab, bevor der Agent sie sieht, und
überprüfen Antworten, bevor Benutzer sie erhalten. Im Gegensatz zu Evaluierungen, die Agents vor dem Deployment testen,
laufen Guards während Live-Konversationen.

## Wie Guards funktionieren

Guards überprüfen Konversationen an zwei Stellen:

Input-Guards analysieren Benutzerfragen, bevor der Agent sie verarbeitet. Sie filtern themenfremde Anfragen heraus,
blockieren Richtlinienverstösse oder bitten um Klärung.

Output-Guards überprüfen Agent-Antworten vor der Zustellung. Sie verifizieren die Qualität, redigieren sensible
Informationen und fangen Halluzinationen oder schädliche Inhalte ab.

::: tip Vollständiger PII-Schutz
Guards arbeiten auf Agent-Ebene. Für PII-Schutz auf Plattformebene, der sensible Informationen in Benutzereingaben
abfängt, bevor sie einen Agent erreichen, siehe [Datenanonymisierung](../2_anonymization/), die die Presidio-Integration
behandelt. Verwenden Sie beide Schichten für eine mehrschichtige Verteidigung (Defense-in-Depth).
:::

## Verfügbare Guards

Der Swiss AI Hub enthält mehrere Guards, die spezifische Risiken adressieren. Welche Guards Sie aktivieren können, hängt
davon ab, wie Ihr Agent erstellt wurde.

### Input-Guards

Agent-Beschreibungs-Guard: Überprüft, ob Fragen mit der Funktion des Agenten übereinstimmen. Ein Finanz-Compliance-Agent
würde „Wie ist das Wetter?“ blockieren und erklären, dass er nur Finanzfragen bearbeitet.

Few-shot-Guard: Erzwingt benutzerdefinierte Richtlinien anhand von Beispielen. Wenn Ihr Unternehmen die Nutzung von
Arbeitsassistenten für Unterhaltungszwecke verbietet, würden Sie Beispiele wie „Empfehlen Sie einen Film“ (blockiert)
und „Empfehlen Sie ein Projektmanagement-Tool“ (erlaubt) bereitstellen. Der Guard lernt, ähnliche Muster zu erkennen.

### Output-Guards

Kontext-hinreichend-Guard: Überprüft, ob der Agent über genügend Informationen verfügt, um präzise zu antworten.
Besonders nützlich für RAG-Agents, die aus Wissensdatenbanken ziehen. Wenn ein Benutzer eine detaillierte technische
Frage stellt, die abgerufenen Dokumente jedoch nicht genügend Details enthalten, stoppt der Guard die Antwort und teilt
dem Benutzer mit, dass die Informationen nicht verfügbar sind.

::: tip Hinweis zur Konfiguration
Einige Agents (wie der RAG-Agent) können den Kontext-hinreichend-Guard automatisch verwenden, um Antworten ohne
ausreichende Evidenz zu verhindern.
:::

Guard für sensible Informationen: Erkennt und redigiert vertrauliche oder persönlich identifizierbare Informationen
(PII) in Agent-Antworten. Dieser fängt PII ab, die in abgerufenen Dokumenten erscheinen. Wenn ein Agent beispielsweise
ein Dokument abruft, das eine Mitarbeiter-E-Mail-Adresse enthält, redigiert der Guard diese, bevor der Benutzer sie
sieht, und ersetzt sie durch `[REDACTED]`.

## Wann Guards eingesetzt werden sollten

| Agent-Typ                                                         | Empfohlene Guards                                                                      |
| :---------------------------------------------------------------- | :------------------------------------------------------------------------------------- |
| Kundenorientierte Agents                                          | Agent-Beschreibungs-Guard, Few-shot-Guard (für Richtlinien), Kontext-hinreichend-Guard |
| Compliance-kritische Bereiche (Gesundheitswesen, Finanzen, Recht) | Alle Guards + [Presidio PII-Schutz](../2_anonymization/)                               |
| Interne Wissensassistenten                                        | Agent-Beschreibungs-Guard, Kontext-hinreichend-Guard                                   |
| Spezialisierte Agents mit engem Anwendungsbereich                 | Kontext-hinreichend-Guard (minimale Leitplanken erforderlich)                          |
| Entwicklungs-/Testumgebungen                                      | Optional (Geschwindigkeit hat Vorrang vor Sicherheit)                                  |

## Beziehung zu Presidio

Guards und [Presidio-Anonymisierung](../2_anonymization/) arbeiten auf verschiedenen Ebenen, um vollständigen PII-Schutz
zu bieten:

| Ebene                          | Komponente                                       | Zweck                                                                     |
| :----------------------------- | :----------------------------------------------- | :------------------------------------------------------------------------ |
| LiteLLM-Proxy (Plattformebene) | Presidio                                         | Entfernt PII aus Benutzerfragen, bevor sie externe LLM-Anbieter erreichen |
| Agent (Anwendungsebene)        | Input-Guards                                     | Validiert die Angemessenheit und den Umfang der Frage                     |
| Agent (Anwendungsebene)        | Output-Guards (Guard für sensible Informationen) | Erkennt PII in Antworten aus abgerufenen Dokumenten                       |

Presidio schützt **Benutzereingaben** davor, an externe Anbieter gesendet zu werden. Der Guard für sensible
Informationen schützt **Agent-Antworten**, die PII aus Ihren Wissensdatenbankdokumenten enthalten könnten. Beide sind
für einen vollständigen PII-Schutz erforderlich.

## Konfiguration

Guards werden während der Entwicklung in Agents integriert. Wie viel Kontrolle Sie haben, hängt vom Design des Agenten
ab. Einige Agents werden mit obligatorischen Guards ausgeliefert, die Sie nicht deaktivieren können. Andere ermöglichen
es Ihnen, spezifische Guards über die Konfigurationsoberfläche ein- oder auszuschalten. Einige unterstützen überhaupt
keine Anpassung.
