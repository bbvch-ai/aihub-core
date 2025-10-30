---
title: Input-/Output-Guards
source_sha: 077376293b329dca469b09a1ce2f42d525d0176240f08ac57444aa8dc28c38e4
---

# LLM-Guards

Guards überprüfen KI-Agenten-Interaktionen in Echtzeit. Sie fangen unangemessene Fragen ab, bevor der Agent sie sieht,
und filtern Antworten, bevor Nutzer sie erhalten. Im Gegensatz zu Evaluationen, die Agenten vor der Bereitstellung
testen, laufen Guards während Live-Konversationen.

## Wie Guards funktionieren

Guards überprüfen Konversationen an zwei Punkten:

Input-Guards analysieren Benutzerfragen, bevor der Agent sie verarbeitet. Sie filtern themenfremde Anfragen heraus,
blockieren Richtlinienverstöße oder bitten um Klärung.

Output-Guards prüfen Agentenantworten vor der Zustellung. Sie überprüfen die Qualität, redigieren vertrauliche
Informationen und fangen Halluzinationen oder schädliche Inhalte ab.

## Verfügbare Guards

Der AI-Hub enthält mehrere Guards, die spezifische Risiken adressieren. Welche Guards Sie aktivieren können, hängt davon
ab, wie Ihr Agent erstellt wurde.

### Input-Guards

**Agentenbeschreibungs-Guard**

Überprüft, ob Fragen zur Funktion des Agenten passen. Ein Agent für Finanz-Compliance würde „Wie ist das Wetter?“
blockieren und erklären, dass er nur Finanzfragen bearbeitet.

**Few-Shot-Guard**

Erzwingt benutzerdefinierte Richtlinien durch Beispiele. Wenn Ihr Unternehmen die Nutzung von Arbeitsassistenten für
Unterhaltungszwecke verbietet, würden Sie Beispiele wie „Empfehlen Sie einen Film“ (blockiert) und „Empfehlen Sie ein
Projektmanagement-Tool“ (erlaubt) bereitstellen. Der Guard lernt, ähnliche Muster zu erkennen.

### Output-Guards

**Ausreichender-Kontext-Guard**

Überprüft, ob der Agent genügend Informationen hat, um präzise zu antworten. Besonders nützlich für RAG-Agenten, die
Informationen aus Wissensdatenbanken abrufen. Wenn ein Benutzer eine detaillierte technische Frage stellt, die
abgerufenen Dokumente jedoch nicht genügend Details enthalten, stoppt der Guard die Antwort und teilt dem Benutzer mit,
dass die Informationen nicht verfügbar sind.

::: tip Hinweis zur Konfiguration
Einige Agenten (wie der RAG-Agent) können den Ausreichender-Kontext-Guard automatisch verwenden, um Antworten ohne
ausreichende Belege zu verhindern.
:::

**Guard für sensible Informationen**

Findet und entfernt vertrauliche oder persönlich identifizierbare Informationen aus Antworten. Wenn ein Agent ein
Dokument abruft, das eine Mitarbeiter-E-Mail enthält, redigiert der Guard diese, bevor der Benutzer sie sieht, und
ersetzt sie durch `[REDACTED]`.

## Wann Guards verwendet werden sollten

Der Zweck, die Zielgruppe und das Risikoprofil Ihres Agenten bestimmen, welche Guards sinnvoll sind.

Verwenden Sie Guards für:

- Kundenorientierte Agenten, die externen Benutzern zugänglich sind
- Compliance-kritische Bereiche wie Gesundheitswesen, Finanzen oder Recht
- Agenten mit Zugriff auf sensible Daten oder interne Datenbanken
- Mehrzweck-Agenten, bei denen die Kontrolle des Umfangs wichtig ist

Sie benötigen möglicherweise weniger Guards für:

- Interne Tools für vertrauenswürdige Mitarbeiter in kontrollierten Umgebungen
- Agenten mit engem Umfang und hochspezialisierten Zwecken
- Entwicklungs- oder Testumgebungen, in denen Geschwindigkeit wichtiger ist als Sicherheit

## Konfiguration

Guards werden während der Entwicklung in Agenten integriert. Wie viel Kontrolle Sie haben, hängt vom Design des Agenten
ab. Einige Agenten werden mit obligatorischen Guards ausgeliefert, die Sie nicht deaktivieren können. Andere ermöglichen
es Ihnen, spezifische Guards über die Konfigurationsoberfläche ein- oder auszuschalten. Einige unterstützen überhaupt
keine Anpassung.
