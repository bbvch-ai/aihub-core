---
title: Schutzmechanismen für Eingabe/Ausgabe
source_sha: 40acd1cfd98a6135a00b1124254a0708bd9be654dfcbd0b179d72b0df4a0a4a5
---

# LLM-Schutzmechanismen

Schutzmechanismen (Guards) überprüfen Interaktionen von KI-Agenten in Echtzeit. Sie fangen unangemessene Fragen ab,
bevor der Agent sie sieht, und filtern Antworten, bevor Benutzer sie erhalten. Im Gegensatz zu Evaluationen, die Agenten
vor der Bereitstellung testen, laufen Schutzmechanismen während Live-Gesprächen.

## Funktionsweise der Schutzmechanismen

Schutzmechanismen überprüfen Konversationen an zwei Punkten:

Eingangs-Schutzmechanismen analysieren Benutzerfragen, bevor der Agent sie verarbeitet. Sie filtern themenfremde
Anfragen heraus, blockieren Richtlinienverstöße oder bitten um Klärung.

Ausgangs-Schutzmechanismen prüfen Agentenantworten vor der Auslieferung. Sie verifizieren die Qualität, redigieren
sensible Informationen und fangen Halluzinationen oder schädliche Inhalte ab.

::: tip Umfassender PII-Schutz
Schutzmechanismen arbeiten auf Agenten-Ebene. Für PII-Schutz auf Plattform-Ebene, der sensible Informationen in
Benutzereingaben abfängt, bevor sie einen Agenten erreichen, siehe [Datenanonymisierung](../2_anonymization/), die die
Presidio-Integration behandelt. Verwenden Sie beide Schichten für eine mehrstufige Verteidigung („Defense-in-Depth“).
:::

## Verfügbare Schutzmechanismen

Der Swiss AI Hub enthält mehrere Schutzmechanismen, die spezifische Risiken adressieren. Welche Schutzmechanismen Sie
aktivieren können, hängt davon ab, wie Ihr Agent erstellt wurde.

### Eingangs-Schutzmechanismen

Agentenbeschreibungs-Schutzmechanismus: Überprüft, ob Fragen zur Funktion des Agenten passen. Ein Agent für
Finanz-Compliance würde „Wie ist das Wetter?“ blockieren und erklären, dass er nur Finanzfragen bearbeitet.

Few-shot-Schutzmechanismus: Setzt benutzerdefinierte Richtlinien durch Beispiele durch. Wenn Ihr Unternehmen die Nutzung
von Arbeitsassistenten für Unterhaltungszwecke verbietet, würden Sie Beispiele wie „Empfehlen Sie einen Film“
(blockiert) und „Empfehlen Sie ein Projektmanagement-Tool“ (erlaubt) bereitstellen. Der Schutzmechanismus lernt,
ähnliche Muster zu erkennen.

### Ausgangs-Schutzmechanismen

Kontext-Ausreichend-Schutzmechanismus: Überprüft, ob der Agent genügend Informationen hat, um genau zu antworten.
Besonders nützlich für RAG-Agenten, die Informationen aus Wissensdatenbanken abrufen. Wenn ein Benutzer eine
detaillierte technische Frage stellt, die abgerufenen Dokumente jedoch nicht genügend Details enthalten, stoppt der
Schutzmechanismus die Antwort und teilt dem Benutzer mit, dass die Informationen nicht verfügbar sind.

::: tip Konfigurationshinweis
Einige Agenten (wie der RAG-Agent) können den Kontext-Ausreichend-Schutzmechanismus automatisch verwenden, um Antworten
ohne ausreichende Belege zu verhindern.
:::

Schutzmechanismus für sensible Informationen: Erkennt und redigiert vertrauliche oder persönlich identifizierbare
Informationen (PII) in Agentenantworten. Dies fängt PII ab, die in abgerufenen Dokumenten erscheinen. Wenn ein Agent
beispielsweise ein Dokument abruft, das eine E-Mail-Adresse eines Mitarbeiters enthält, redigiert der Schutzmechanismus
diese, bevor der Benutzer sie sieht, und ersetzt sie durch `[REDACTED]`.

## Wann Schutzmechanismen eingesetzt werden sollten

| Agententyp                                                       | Empfohlene Schutzmechanismen                                                                                                |
| :--------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| Kundenorientierte Agenten                                        | Agentenbeschreibungs-Schutzmechanismus, Few-shot-Schutzmechanismus (für Richtlinien), Kontext-Ausreichend-Schutzmechanismus |
| Compliance-kritische Domänen (Gesundheitswesen, Finanzen, Recht) | Alle Schutzmechanismen + [Presidio PII-Schutz](../2_anonymization/)                                                         |
| Interne Wissensassistenten                                       | Agentenbeschreibungs-Schutzmechanismus, Kontext-Ausreichend-Schutzmechanismus                                               |
| Spezialisierte Agenten mit engem Anwendungsbereich               | Kontext-Ausreichend-Schutzmechanismus (minimale Leitplanken erforderlich)                                                   |
| Entwicklungs-/Testumgebungen                                     | Optional (Geschwindigkeit hat Vorrang vor Sicherheit)                                                                       |

## Beziehung zu Presidio

Schutzmechanismen und [Presidio-Anonymisierung](../2_anonymization/) arbeiten auf verschiedenen Ebenen, um vollständigen
PII-Schutz zu bieten:

| Ebene                           | Komponente                                                                | Zweck                                                                       |
| :------------------------------ | :------------------------------------------------------------------------ | :-------------------------------------------------------------------------- |
| LiteLLM Proxy (Plattform-Ebene) | Presidio                                                                  | Entfernt PII aus Benutzerfragen, bevor diese externe LLM-Anbieter erreichen |
| Agent (Anwendungs-Ebene)        | Eingangs-Schutzmechanismen                                                | Validiert die Angemessenheit und den Umfang der Frage                       |
| Agent (Anwendungs-Ebene)        | Ausgangs-Schutzmechanismen (Schutzmechanismus für sensible Informationen) | Erkennt PII in Antworten aus abgerufenen Dokumenten                         |

Presidio schützt **Benutzereingaben** davor, an externe Anbieter gesendet zu werden. Der Schutzmechanismus für sensible
Informationen schützt **Agentenantworten**, die PII aus Ihren Wissensdatenbankdokumenten enthalten könnten. Beide sind
für einen vollständigen PII-Schutz erforderlich.

## Konfiguration

Schutzmechanismen werden während der Entwicklung in Agenten integriert. Wie viel Kontrolle Sie haben, hängt vom Design
des Agenten ab. Einige Agenten werden mit obligatorischen Schutzmechanismen ausgeliefert, die Sie nicht deaktivieren
können. Andere ermöglichen es Ihnen, spezifische Schutzmechanismen über die Konfigurationsschnittstelle zu aktivieren
oder zu deaktivieren. Einige unterstützen überhaupt keine Anpassung.
