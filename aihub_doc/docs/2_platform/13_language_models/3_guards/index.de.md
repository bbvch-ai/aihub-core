---
title: Input/Output-Wächter
source_sha: 734885eb50682cebb736b1bc7b64fa89954873c41059b6e3fb561d7fc2ee741b
---

# LLM-Wächter

Wächter überprüfen KI-Agenten-Interaktionen in Echtzeit. Sie fangen unpassende Fragen ab, bevor der Agent sie sieht, und
überprüfen Antworten, bevor Benutzer sie erhalten. Im Gegensatz zu Evaluierungen, die Agenten vor der Bereitstellung
testen, laufen Wächter während Live-Gesprächen.

## Wie Wächter funktionieren

Wächter überprüfen Konversationen an zwei Punkten:

Input-Wächter analysieren Benutzerfragen, bevor der Agent sie verarbeitet. Sie filtern themenfremde Anfragen heraus,
blockieren Richtlinienverstöße oder bitten um Klärung.

Output-Wächter prüfen Agentenantworten vor der Auslieferung. Sie überprüfen die Qualität, redigieren sensible
Informationen und fangen Halluzinationen oder schädliche Inhalte ab.

## Verfügbare Wächter

Der AI-Hub enthält mehrere Wächter, die spezifische Risiken adressieren. Welche Wächter Sie aktivieren können, hängt
davon ab, wie Ihr Agent gebaut wurde.

### Input-Wächter

**Agentenbeschreibungs-Wächter**

Prüft, ob Fragen zur Funktion des Agenten passen. Ein Finanz-Compliance-Agent würde „Wie ist das Wetter?“ blockieren und
erklären, dass er nur Finanzfragen bearbeitet.

**Few-Shot-Wächter**

Erzwingt benutzerdefinierte Richtlinien anhand von Beispielen. Wenn Ihr Unternehmen die Nutzung von Arbeitsassistenten
für Unterhaltungszwecke verbietet, würden Sie Beispiele wie „Empfehlen Sie einen Film“ (blockiert) und „Empfehlen Sie
ein Projektmanagement-Tool“ (erlaubt) bereitstellen. Der Wächter lernt, ähnliche Muster zu erkennen.

### Output-Wächter

**Kontext-Hinreichend-Wächter**

Prüft, ob der Agent über genügend Informationen verfügt, um präzise zu antworten. Besonders nützlich für RAG-Agenten,
die Informationen aus Wissensdatenbanken abrufen. Wenn ein Benutzer eine detaillierte technische Frage stellt, die
abgerufenen Dokumente jedoch nicht genügend Details enthalten, stoppt der Wächter die Antwort und teilt dem Benutzer
mit, dass die Informationen nicht verfügbar sind.

::: tip Konfigurationshinweis
Einige Agenten (wie der RAG-Agent) können den Kontext-Hinreichend-Wächter automatisch verwenden, um Antworten ohne
ausreichende Beweise zu verhindern.
:::

**Wächter für sensible Informationen**

Findet und entfernt vertrauliche oder persönlich identifizierbare Informationen aus Antworten. Wenn ein Agent ein
Dokument mit einer Mitarbeiter-E-Mail abruft, redigiert der Wächter diese, bevor der Benutzer sie sieht, und ersetzt sie
durch `[REDACTED]`.

## Wann Wächter eingesetzt werden sollten

Zweck, Zielgruppe und Risikostufe Ihres Agenten bestimmen, welche Wächter sinnvoll sind.

Verwenden Sie Wächter für:

- Kundenorientierte Agenten, die externen Benutzern zugänglich sind
- Compliance-kritische Bereiche wie Gesundheitswesen, Finanzen oder Recht
- Agenten mit Zugriff auf sensible Daten oder interne Datenbanken
- Mehrzweck-Agenten, bei denen die Kontrolle des Anwendungsbereichs wichtig ist

Sie benötigen möglicherweise weniger Wächter für:

- Interne Tools für vertrauenswürdige Mitarbeiter in kontrollierten Umgebungen
- Agenten mit engem Anwendungsbereich und hochspezialisierten Zwecken
- Entwicklungs- oder Testumgebungen, in denen Geschwindigkeit wichtiger ist als Sicherheit

## Konfiguration

Wächter werden während der Entwicklung in Agenten integriert. Wie viel Kontrolle Sie haben, hängt vom Design des Agenten
ab. Einige Agenten werden mit obligatorischen Wächtern ausgeliefert, die Sie nicht deaktivieren können. Andere
ermöglichen es Ihnen, bestimmte Wächter über die Konfigurationsoberfläche ein- oder auszuschalten. Einige unterstützen
überhaupt keine Anpassung.
