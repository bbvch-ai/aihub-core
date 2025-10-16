---
title: Datenpipelines
index: 6
source_sha: "bc4c04ad35b34e24d6404b2a4ebc339d205eae0f92ca828215e89393e4bacd90"
---

# Datenpipelines: Das Wissen der KI erschaffen

Ein KI-Agent ist nur so intelligent wie die Informationen, auf die er zugreifen kann. Rohe Unternehmensdaten – verteilt auf PDFs, SharePoint-Sites und Netzlaufwerke – liegen nicht in einem Format vor, das eine KI ohne Weiteres nutzen kann. Die Schicht der **Datenpipelines** ist die leistungsstarke Engine, die diese Lücke schließt und Ihre verstreuten Dokumente und Datenquellen in eine strukturierte, durchsuchbare und KI-taugliche **Wissensbasis** umwandelt.

Stellen Sie sich eine Datenpipeline als eine automatisierte Fabrik für Wissen vor. Sie nimmt Rohmaterialien (Ihre Dokumente) und führt sie durch eine ausgeklügelte Montagelinie, um ein veredeltes Produkt (eine indizierte, durchsuchbare Wissensbasis) zu erzeugen, das Ihre Agenten nutzen können, um präzise, kontextbezogene Antworten zu liefern.

## Von Dokumenten zu Intelligenz: Der Pipeline-Prozess

Im Kern ist eine Datenpipeline ein automatisierter Workflow, der Ihre Informationen aufnimmt, verarbeitet und indiziert. Obwohl dieser Prozess stark angepasst werden kann, folgt jede Pipeline einer Reihe grundlegender Schritte, um sicherzustellen, dass Ihre Daten korrekt für die KI-Nutzung vorbereitet werden.

::: info Das Ziel einer Pipeline
Das durchgängige Ziel ist es, unstrukturierte Dokumente in einen strukturierten **Vektorindex** umzuwandeln. Dieser Index ermöglicht es einem KI-Agenten, Informationen basierend auf semantischer Bedeutung zu suchen, nicht nur nach Schlüsselwörtern, was die Grundlage eines effektiven RAG-Systems ist.
:::

Hier ist ein Blick auf die Schlüsselphasen einer typischen Datenaufnahmepipeline:

**1. Verbinden & Aufnehmen**
Der erste Schritt ist die Verbindung zu Ihren Daten, wo immer sie sich befinden. Die Plattform bietet Konnektoren für eine Vielzahl von Unternehmenssystemen, die es Pipelines ermöglichen, Dokumente von Quellen wie Microsoft SharePoint, Netzlaufwerken oder Webseiten automatisch zu überwachen und abzurufen.

**2. Parsen & Verstehen**
Sobald ein Dokument abgerufen wurde, muss die Pipeline dessen Inhalt und Struktur verstehen. Sie verwendet fortschrittliche Parsing-Techniken, um Text, Tabellen und Metadaten aus verschiedenen Formaten wie PDF, Word und Excel zu extrahieren. Entscheidend ist, dass sie die ursprüngliche semantische Struktur des Dokuments – Überschriften, Listen und Abschnitte – bewahrt, was für den Kontext unerlässlich ist.

**3. Segmentieren & Aufteilen**
LLMs haben ein begrenztes Kontextfenster, sodass sie nicht ganze große Dokumente auf einmal verarbeiten können. Die Pipeline zerlegt die Dokumente intelligent in kleinere, semantisch bedeutungsvolle „Chunks“ (Teilstücke). Dies ist nicht nur eine zufällige Aufteilung; das System versucht, Chunks zu erstellen, die eine kohärente Idee oder ein Thema repräsentieren, um sicherzustellen, dass die Teile für sich allein sinnvoll sind.

**4. Einbetten & Vektorisieren**
Hier geschieht die Magie für die KI-Suche. Die Pipeline übersetzt die Bedeutung jedes Text-Chunks in ein numerisches Format, das als **Vektoreinbettung** bezeichnet wird. Diese Vektoren erfassen die semantische Essenz des Textes, wodurch die KI Chunks mit ähnlichen Bedeutungen finden kann, selbst wenn sie nicht dieselben Schlüsselwörter teilen.

**5. Indizieren & Speichern**
Schließlich werden diese Vektoreinbettungen zusammen mit dem Originaltext und den Metadaten in einer spezialisierten **Vektordatenbank** gespeichert und indiziert. Dies schafft die finale, durchsuchbare Wissensbasis, die Ihre RAG-Agenten nutzen werden, um Informationen zu finden.

## Die Kraft der Automatisierung: Lebendiges Wissen

Ein zentrales Merkmal der Datenpipelines der Plattform ist, dass dies kein einmaliger, manueller Prozess ist. Pipelines sind so konzipiert, dass sie **automatisiert und kontinuierlich** sind.

Sie können eine Pipeline so konfigurieren, dass sie eine Datenquelle, wie einen SharePoint-Ordner, auf Änderungen überwacht. Wenn ein Dokument hinzugefügt, aktualisiert oder gelöscht wird, wird die Pipeline automatisch ausgelöst und synchronisiert die Änderungen mit der Wissensbasis.

::: tip Einrichten und vergessen
Diese kontinuierliche Synchronisation stellt sicher, dass das Wissen Ihrer KI immer aktuell ist. Wenn eine Richtlinie in SharePoint aktualisiert wird, stellt die Pipeline sicher, dass der Agent sofort Zugriff auf die neue Version hat, ohne dass ein manuelles Eingreifen erforderlich ist. Ihre Wissensbasis wird zu einer lebendigen Entität, die sich mit Ihrer Organisation weiterentwickelt.
:::

## Orchestrierung und Zuverlässigkeit: Auf Dagster aufgebaut

Um diese komplexen, mehrstufigen Workflows zu verwalten, verwendet der Swiss AI Hub **Dagster**, einen datenorchestrator in Industriequalität. Dagster fungiert als Dirigent für Ihre Datenpipelines und stellt sicher, dass jeder Prozess zuverlässig, effizient und transparent abläuft.

Dagster ist verantwortlich für:
-   **Planung und Auslösung**: Ausführung von Pipelines nach einem Zeitplan oder als Reaktion auf Ereignisse.
-   **Fehlerbehandlung**: Anmutige Verwaltung von Fehlern und Wiederholungsversuchen, um sicherzustellen, dass temporäre Probleme Ihre Daten nicht beschädigen.
-   **Beobachtbarkeit**: Bereitstellung eines vollständigen, auditierbaren Protokolls jedes Pipeline-Laufs, damit Sie genau nachvollziehen können, wie ein Dokument verarbeitet wurde, und Probleme beheben können.

Diese robuste Grundlage bedeutet, dass Sie Ihren Datenpipelines vertrauen können, auch in einer Produktionsumgebung und bei massivem Umfang zuverlässig zu arbeiten.

## Der strategische Vorteil: Warum diese Architektur wichtig ist

Die Datenpipeline-Architektur der Plattform bietet mehrere entscheidende Vorteile für jede Unternehmens-KI-Strategie:

::: details Eine entkoppelte Architektur
Die Trennung der Datenaufnahme (Pipelines) von der KI-Operation (Agenten) ist eine bewusste Designentscheidung. Sie ermöglicht es Ihren Teams, unabhängig voneinander zu arbeiten. Data Engineering kann sich auf den Aufbau robuster Pipelines und die Anbindung neuer Datenquellen konzentrieren, während KI-Entwickler sich auf die Erstellung intelligenter Agentenlogik konzentrieren können. Die Agenten konsumieren einfach die hochwertigen Wissensbasen, die die Pipelines produzieren, ohne die Komplexität ihrer Entstehung kennen zu müssen.
:::

::: details Vollständige Beobachtbarkeit und Governance
Im Gegensatz zu einem „Black Box“-System wird jeder Schritt der Pipeline verfolgt und protokolliert. Wenn ein Agent eine merkwürdige Antwort liefert, können Sie diese über den Abrufprozess bis zum genauen Dokumenten-Chunk und sogar bis zum Pipeline-Lauf, der ihn verarbeitet hat, zurückverfolgen. Dieser „Glass Box“-Ansatz ist für die Fehlersuche, Compliance und den Aufbau von organisationalem Vertrauen unerlässlich.
:::

::: details Konsistenz und Qualitätskontrolle
Indem Sie die Datenverarbeitung als Code innerhalb einer Pipeline definieren, stellen Sie sicher, dass jedes Dokument auf eine konsistente, wiederholbare Weise behandelt wird. Sie können Qualitätsprüfungen, Validierungsregeln und Sicherheits-Scans direkt in Ihre Pipelines einbetten und so garantieren, dass nur hochwertige, konforme Informationen in Ihre Wissensbasen gelangen.
