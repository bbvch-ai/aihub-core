---
title: Datenpipelines
index: 6
source_sha: "2d3ad5721cffe57bab64d81214f455b1732bf7a8bb9a8b43c96de1076d8df243"
---

# Datenpipelines: Das Wissen der KI schaffen

![Systemübersicht - Datenpipelines](./media/architecture/system_overview/system-overview-highlight-pipelines.png)

Ein KI-Agent ist nur so intelligent wie die Informationen, auf die er zugreifen kann. Rohe Unternehmensdaten – verteilt über PDFs, SharePoint-Seiten und Netzlaufwerke – liegen nicht in einem Format vor, das eine KI direkt nutzen kann. Die Schicht der **Datenpipelines** ist die leistungsstarke Engine, die diese Lücke schließt und Ihre verstreuten Dokumente und Datenquellen in eine strukturierte, durchsuchbare und KI-bereite **Wissensbasis** umwandelt.

Stellen Sie sich eine Datenpipeline als eine automatisierte Fabrik für Wissen vor. Sie nimmt Rohmaterialien (Ihre Dokumente) und führt sie durch eine hochentwickelte Montagelinie, um ein veredeltes Produkt (eine indizierte, durchsuchbare Wissensbasis) zu erzeugen, das Ihre Agenten nutzen können, um präzise, kontextbewusste Antworten zu liefern.

## Von Dokumenten zu Intelligenz: Der Pipeline-Prozess

Im Kern ist eine Datenpipeline ein automatisierter Workflow, der Ihre Informationen aufnimmt, verarbeitet und indiziert. Obwohl dieser Prozess stark angepasst werden kann, folgt jede Pipeline einer Reihe grundlegender Schritte, um sicherzustellen, dass Ihre Daten korrekt für die KI-Nutzung vorbereitet werden.

::: info Das Ziel einer Pipeline
Der übergeordnete Zweck ist die Umwandlung unstrukturierter Dokumente in einen strukturierten **Vektorindex**. Dieser Index ermöglicht es einem KI-Agenten, Informationen basierend auf semantischer Bedeutung und nicht nur auf Schlüsselwörtern zu suchen, was die Grundlage eines effektiven RAG-Systems ist.
:::

Hier ist ein Überblick über die wichtigsten Phasen einer typischen Datenerfassungs-Pipeline:

**1. Verbinden & Erfassen**
Der erste Schritt besteht darin, sich mit Ihren Daten zu verbinden, wo immer diese sich befinden. Die Plattform bietet Konnektoren für eine Vielzahl von Unternehmenssystemen, die es Pipelines ermöglichen, Dokumente von Quellen wie Microsoft SharePoint, Netzlaufwerken oder Webseiten automatisch zu überwachen und abzurufen.

**2. Parsen & Verstehen**
Sobald ein Dokument abgerufen wurde, muss die Pipeline dessen Inhalt und Struktur verstehen. Sie nutzt fortschrittliche Parsing-Techniken, um Text, Tabellen und Metadaten aus verschiedenen Formaten wie PDF, Word und Excel zu extrahieren. Entscheidend ist, dass sie die ursprüngliche semantische Struktur des Dokuments – Überschriften, Listen und Abschnitte – bewahrt, was für den Kontext unerlässlich ist.

**3. Zerlegen & Segmentieren**
LLMs haben ein begrenztes Kontextfenster, daher können sie nicht ganze große Dokumente auf einmal verarbeiten. Die Pipeline zerlegt die Dokumente intelligent in kleinere, semantisch bedeutungsvolle „Chunks“. Dies ist nicht nur eine zufällige Aufteilung; das System versucht, Chunks zu erstellen, die eine kohärente Idee oder ein Thema repräsentieren, um sicherzustellen, dass die Teilstücke für sich genommen Sinn ergeben.

**4. Einbetten & Vektorisieren**
Hier geschieht die Magie für die KI-Suche. Die Pipeline übersetzt die Bedeutung jedes Text-Chunks in ein numerisches Format, das als **Vektor-Embedding** bezeichnet wird. Diese Vektoren erfassen die semantische Essenz des Textes und ermöglichen es der KI, Chunks mit ähnlichen Bedeutungen zu finden, selbst wenn sie nicht dieselben Schlüsselwörter enthalten.

**5. Indizieren & Speichern**
Schließlich werden diese Vektor-Embeddings zusammen mit dem Originaltext und den Metadaten in einer spezialisierten **Vektordatenbank** gespeichert und indiziert. Dadurch entsteht die endgültige, durchsuchbare Wissensbasis, die Ihre RAG-Agenten verwenden werden, um Informationen zu finden.

## Die Kraft der Automatisierung: Lebendiges Wissen

Ein zentrales Merkmal der Datenpipelines der Plattform ist, dass dies kein einmaliger, manueller Prozess ist. Pipelines sind so konzipiert, dass sie **automatisiert und kontinuierlich** ablaufen.

Sie können eine Pipeline so konfigurieren, dass sie eine Datenquelle, wie einen SharePoint-Ordner, auf Änderungen überwacht. Wenn ein Dokument hinzugefügt, aktualisiert oder gelöscht wird, wird die Pipeline automatisch ausgelöst und synchronisiert die Änderungen mit der Wissensbasis.

::: tip Einrichten und vergessen
Diese kontinuierliche Synchronisierung stellt sicher, dass das Wissen Ihrer KI immer aktuell ist. Wenn eine Richtlinie in SharePoint aktualisiert wird, stellt die Pipeline sicher, dass der Agent sofort Zugriff auf die neue Version hat, ohne dass manuelle Eingriffe erforderlich sind. Ihre Wissensbasis wird zu einer lebendigen Entität, die sich mit Ihrer Organisation weiterentwickelt.
:::

## Orchestrierung und Zuverlässigkeit: Basierend auf Dagster

Um diese komplexen, mehrstufigen Workflows zu verwalten, verwendet der Swiss AI Hub **Dagster**, einen industrietauglichen Daten-Orchestrator. Dagster fungiert als Dirigent für Ihre Datenpipelines und stellt sicher, dass jeder Prozess zuverlässig, effizient und transparent abläuft.

Dagster ist verantwortlich für:
-   **Planung und Auslösung**: Ausführung von Pipelines nach Zeitplan oder als Reaktion auf Ereignisse.
-   **Fehlerbehandlung**: Anmutige Verwaltung von Fehlern und Wiederholungsversuchen, um sicherzustellen, dass vorübergehende Probleme Ihre Daten nicht beschädigen.
-   **Beobachtbarkeit**: Bereitstellung eines vollständigen, auditierbaren Protokolls jeder Pipeline-Ausführung, damit Sie genau sehen können, wie ein Dokument verarbeitet wurde, und Probleme beheben können.

Diese robuste Grundlage bedeutet, dass Sie Ihren Datenpipelines vertrauen können, dass sie in einer Produktionsumgebung zuverlässig funktionieren, selbst in großem Maßstab.

## Der strategische Vorteil: Warum diese Architektur wichtig ist

Die Datenpipeline-Architektur der Plattform bietet mehrere entscheidende Vorteile für jede Unternehmens-KI-Strategie:

::: details Eine entkoppelte Architektur
Die Trennung der Datenaufnahme (Pipelines) vom KI-Betrieb (Agenten) ist eine bewusste Designentscheidung. Sie ermöglicht Ihren Teams, unabhängig zu arbeiten. Dateningenieure können sich auf den Aufbau robuster Pipelines und die Anbindung neuer Datenquellen konzentrieren, während KI-Entwickler sich auf die Entwicklung intelligenter Agentenlogik konzentrieren können. Die Agenten konsumieren einfach die hochwertigen Wissensbasen, die die Pipelines produzieren, ohne die Komplexität ihrer Entstehung kennen zu müssen.
:::

::: details Vollständige Beobachtbarkeit und Governance
Im Gegensatz zu einem „Black-Box“-System wird jeder Schritt der Pipeline verfolgt und protokolliert. Wenn ein Agent eine ungewöhnliche Antwort liefert, können Sie diese über den Abrufprozess bis zum genauen Dokument-Chunk und sogar bis zur Pipeline-Ausführung zurückverfolgen, die ihn verarbeitet hat. Dieser „Glass-Box“-Ansatz ist unerlässlich für Debugging, Compliance und den Aufbau von organisatorischem Vertrauen.
:::

::: details Konsistenz und Qualitätskontrolle
Indem Sie die Datenverarbeitung als Code innerhalb einer Pipeline definieren, stellen Sie sicher, dass jedes Dokument auf konsistente, wiederholbare Weise behandelt wird. Sie können Qualitätsprüfungen, Validierungsregeln und Sicherheitsüberprüfungen direkt in Ihre Pipelines einbetten und so garantieren, dass nur hochwertige, konforme Informationen in Ihre Wissensbasen gelangen.
