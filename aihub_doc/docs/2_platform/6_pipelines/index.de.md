---
title: Datenpipelines
source_sha: 42860344d056379f479c1587eeae57ad51cdf970886a9312286cf4ccd950bb0a
---

# Datenpipelines: Schaffung der Wissensbasis für die KI

Ein KI-Agent ist nur so intelligent wie die Informationen, auf die er zugreifen kann. Rohdaten aus Unternehmen –
verteilt über PDFs, SharePoint-Websites und Netzlaufwerke – liegen nicht in einem Format vor, das eine KI direkt nutzen
kann. Die Schicht der **Datenpipelines** ist der leistungsstarke Motor, der diese Lücke schließt, indem er Ihre
unterschiedlichen Dokumente und Datenquellen in eine strukturierte, durchsuchbare und KI-bereite **Wissensbasis**
umwandelt.

Stellen Sie sich eine Datenpipeline als automatisierte Fabrik für Wissen vor. Sie nimmt Rohmaterialien (Ihre Dokumente)
und führt sie durch eine ausgeklügelte Montagelinie, um ein veredeltes Produkt (eine indizierte, durchsuchbare
Wissensbasis) zu erzeugen, das Ihre Agenten nutzen können, um präzise, kontextbezogene Antworten zu liefern.

## Vom Dokument zur Intelligenz: Der Pipeline-Prozess

Im Kern ist eine Datenpipeline ein automatisierter Workflow, der Ihre Informationen aufnimmt, verarbeitet und indiziert.
Obwohl dieser Prozess stark angepasst werden kann, folgt jede Pipeline einer Reihe grundlegender Schritte, um
sicherzustellen, dass Ihre Daten korrekt für die KI-Nutzung vorbereitet werden.

::: info Das Ziel einer Pipeline
Das durchgängige Ziel ist es, unstrukturierte Dokumente in einen strukturierten **Vektorindex** umzuwandeln. Dieser
Index ermöglicht es einem KI-Agenten, Informationen basierend auf semantischer Bedeutung und nicht nur auf
Schlüsselwörtern zu suchen, was die Grundlage eines effektiven RAG-Systems ist.
:::

Hier ist ein Überblick über die wichtigsten Phasen einer typischen Datenaufnahme-Pipeline:

**1. Verbinden & Aufnehmen** Der erste Schritt besteht darin, sich mit Ihren Daten zu verbinden, wo immer sie sich
befinden. Die Plattform bietet Konnektoren für eine Vielzahl von Unternehmenssystemen, die es Pipelines ermöglichen,
Dokumente aus Quellen wie Microsoft SharePoint, Netzlaufwerken oder Webseiten automatisch zu überwachen und abzurufen.

**2. Parsen & Verstehen** Sobald ein Dokument abgerufen wurde, muss die Pipeline dessen Inhalt und Struktur verstehen.
Sie nutzt fortschrittliche Parsing-Techniken, um Text, Tabellen und Metadaten aus verschiedenen Formaten wie PDF, Word
und Excel zu extrahieren. Entscheidend ist, dass sie die ursprüngliche semantische Struktur des Dokuments –
Überschriften, Listen und Abschnitte – bewahrt, was für den Kontext von entscheidender Bedeutung ist.

**3. Aufteilen & Segmentieren** LLMs haben ein begrenztes Kontextfenster, sodass sie nicht ganze große Dokumente auf
einmal verarbeiten können. Die Pipeline zerlegt die Dokumente intelligent in kleinere, semantisch bedeutungsvolle
„Chunks“. Dies ist nicht nur eine zufällige Aufteilung; das System versucht, Chunks zu erstellen, die eine kohärente
Idee oder ein Thema repräsentieren, um sicherzustellen, dass die Teile für sich allein sinnvoll sind.

**4. Einbetten & Vektorisieren** Hier geschieht die Magie für die KI-Suche. Die Pipeline übersetzt die Bedeutung jedes
Text-Chunks in ein numerisches Format, das als **Vektoreinbettung** bezeichnet wird. Diese Vektoren erfassen die
semantische Essenz des Textes und ermöglichen es der KI, Chunks mit ähnlichen Bedeutungen zu finden, auch wenn sie nicht
dieselben Schlüsselwörter teilen.

**5. Indizieren & Speichern** Schließlich werden diese Vektoreinbettungen zusammen mit dem Originaltext und den
Metadaten in einer spezialisierten **Vektordatenbank** gespeichert und indiziert. Dies schafft die endgültige,
durchsuchbare Wissensbasis, die Ihre RAG-Agenten nutzen werden, um Informationen zu finden.

## Die Kraft der Automatisierung: Lebendiges Wissen

Ein Hauptmerkmal der Datenpipelines der Plattform ist, dass dies kein einmaliger, manueller Prozess ist. Pipelines sind
so konzipiert, dass sie **automatisiert und kontinuierlich** sind.

Sie können eine Pipeline so konfigurieren, dass sie eine Datenquelle, wie einen SharePoint-Ordner, auf Änderungen
überwacht. Wenn ein Dokument hinzugefügt, aktualisiert oder gelöscht wird, wird die Pipeline automatisch ausgelöst und
synchronisiert die Änderungen mit der Wissensbasis.

::: tip Einrichten und vergessen
Diese kontinuierliche Synchronisation stellt sicher, dass das Wissen Ihrer KI stets aktuell ist. Wenn eine Richtlinie in
SharePoint aktualisiert wird, stellt die Pipeline sicher, dass der Agent sofort Zugriff auf die neue Version hat, ohne
dass ein manuelles Eingreifen erforderlich ist. Ihre Wissensbasis wird zu einer lebendigen Entität, die sich mit Ihrer
Organisation weiterentwickelt.
:::

## Orchestrierung und Zuverlässigkeit: Basierend auf Dagster

Um diese komplexen, mehrstufigen Workflows zu verwalten, verwendet der Swiss AI Hub **Dagster**, einen Datenorchestrator
in Industriequalität. Dagster fungiert als Dirigent für Ihre Datenpipelines und stellt sicher, dass jeder Prozess
zuverlässig, effizient und transparent abläuft.

Dagster ist verantwortlich für:

- **Planung und Auslösung**: Ausführung von Pipelines nach Zeitplan oder als Reaktion auf Ereignisse.
- **Fehlerbehandlung**: Fehler und Wiederholungsversuche elegant verwalten und sicherstellen, dass vorübergehende
  Probleme Ihre Daten nicht beschädigen.
- **Observability**: Bereitstellung eines vollständigen, überprüfbaren Protokolls jeder Pipeline-Ausführung, damit Sie
  genau sehen können, wie ein Dokument verarbeitet wurde, und eventuelle Probleme beheben können.

Diese robuste Grundlage bedeutet, dass Sie Ihren Datenpipelines vertrauen können, auch im großen Maßstab, zuverlässig in
einer Produktionsumgebung zu arbeiten.

## Der strategische Vorteil: Warum diese Architektur wichtig ist

Die Datenpipeline-Architektur der Plattform bietet mehrere entscheidende Vorteile für jede KI-Strategie eines
Unternehmens:

::: details Eine entkoppelte Architektur
Die Trennung der Datenaufnahme (Pipelines) vom KI-Betrieb (Agenten) ist eine bewusste Designentscheidung. Sie ermöglicht
es Ihren Teams, unabhängig voneinander zu arbeiten. Data Engineering kann sich auf den Aufbau robuster Pipelines und die
Anbindung neuer Datenquellen konzentrieren, während KI-Entwickler sich auf die Entwicklung intelligenter Agentenlogik
konzentrieren können. Die Agenten konsumieren einfach die hochwertigen Wissensbasen, die die Pipelines erzeugen, ohne
die Komplexität ihrer Erstellung kennen zu müssen.
:::

::: details Umfassende Observability und Governance
Im Gegensatz zu einem „Black-Box“-System wird jeder Schritt der Pipeline verfolgt und protokolliert. Wenn ein Agent eine
seltsame Antwort liefert, können Sie diese bis zum genauen Dokument-Chunk und sogar bis zur Pipeline-Ausführung, die ihn
verarbeitet hat, zurückverfolgen. Dieser „Glass-Box“-Ansatz ist essenziell für Debugging, Compliance und den Aufbau von
organisatorischem Vertrauen.
:::

::: details Konsistenz und Qualitätskontrolle
Indem Sie die Datenverarbeitung als Code innerhalb einer Pipeline definieren, stellen Sie sicher, dass jedes Dokument
konsistent und wiederholbar verarbeitet wird. Sie können Qualitätsprüfungen, Validierungsregeln und Sicherheitsscans
direkt in Ihre Pipelines einbetten, um zu gewährleisten, dass nur hochwertige, konforme Informationen in Ihre
Wissensbasen gelangen.
:::
