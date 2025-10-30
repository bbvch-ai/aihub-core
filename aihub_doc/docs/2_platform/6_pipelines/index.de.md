---
title: Datenpipelines
source_sha: fac1d871a9130e64c95627a6b45bf60b7c18c61d94e7433e7c7f0b009a547885
---

# Datenpipelines: Das Wissen der KI schaffen

Ein KI-Agent ist nur so intelligent wie die Informationen, auf die er zugreifen kann. Rohdaten einer Organisation –
verteilt über PDFs, SharePoint-Seiten und Netzlaufwerke – liegen nicht in einem Format vor, das eine KI ohne Weiteres
nutzen kann. Die Schicht der **Datenpipelines** ist der leistungsstarke Motor, der diese Lücke schließt, indem sie Ihre
unterschiedlichen Dokumente und Datenquellen in eine strukturierte, durchsuchbare und KI-bereite **Wissensbasis**
umwandelt.

Stellen Sie sich eine Datenpipeline wie eine automatisierte Wissensfabrik vor. Sie nimmt Rohmaterialien (Ihre Dokumente)
und führt sie durch eine hochentwickelte Montagelinie, um ein verfeinertes Produkt (eine indizierte, durchsuchbare
Wissensbasis) zu erzeugen, das Ihre Agenten nutzen können, um präzise, kontextbezogene Antworten zu liefern.

## Von Dokumenten zu Intelligenz: Der Pipeline-Prozess

Im Kern ist eine Datenpipeline ein automatisierter Workflow, der Ihre Informationen aufnimmt, verarbeitet und indiziert.
Obwohl dieser Prozess hochgradig angepasst werden kann, folgt jede Pipeline einer Reihe grundlegender Schritte, um
sicherzustellen, dass Ihre Daten korrekt für die KI-Nutzung vorbereitet werden.

::: info Das Ziel einer Pipeline
Das durchgängige Ziel ist es, unstrukturierte Dokumente in einen strukturierten **Vektorindex** umzuwandeln. Dieser
Index ermöglicht es einem KI-Agenten, Informationen basierend auf semantischer Bedeutung zu suchen, nicht nur nach
Stichwörtern, was die Grundlage eines effektiven RAG-Systems ist.
:::

Hier sind die wichtigsten Phasen einer typischen Datenerfassungspipeline:

**1. Verbinden & Erfassen** Der erste Schritt besteht darin, sich mit Ihren Daten zu verbinden, wo immer sie sich
befinden. Die Plattform bietet Konnektoren für eine Vielzahl von Unternehmenssystemen, die es Pipelines ermöglichen,
Dokumente von Quellen wie Microsoft SharePoint, Netzlaufwerken oder Webseiten automatisch zu überwachen und abzurufen.

**2. Parsen & Verstehen** Sobald ein Dokument abgerufen wurde, muss die Pipeline dessen Inhalt und Struktur verstehen.
Sie verwendet fortschrittliche Parsing-Techniken, um Text, Tabellen und Metadaten aus verschiedenen Formaten wie PDF,
Word und Excel zu extrahieren. Entscheidend ist, dass sie die ursprüngliche semantische Struktur des Dokuments –
Überschriften, Listen und Abschnitte – bewahrt, was für den Kontext von entscheidender Bedeutung ist.

**3. Zerlegen & Segmentieren** LLMs haben ein begrenztes Kontextfenster, daher können sie nicht ganze große Dokumente
auf einmal verarbeiten. Die Pipeline zerlegt die Dokumente intelligent in kleinere, semantisch bedeutsame „Chunks“. Dies
ist nicht nur eine zufällige Aufteilung; das System versucht, Chunks zu erstellen, die eine kohärente Idee oder ein
Thema darstellen, um sicherzustellen, dass die Teile für sich allein sinnvoll sind.

**4. Einbetten & Vektorisieren** Hier geschieht die Magie für die KI-Suche. Die Pipeline übersetzt die Bedeutung jedes
Text-„Chunks“ in ein numerisches Format, das als **Vektoreinbettung** bezeichnet wird. Diese Vektoren erfassen die
semantische Essenz des Textes und ermöglichen es der KI, Chunks mit ähnlichen Bedeutungen zu finden, selbst wenn sie
nicht dieselben Schlüsselwörter teilen.

**5. Indizieren & Speichern** Schließlich werden diese Vektoreinbettungen zusammen mit dem Originaltext und den
Metadaten in einer spezialisierten **Vektordatenbank** gespeichert und indiziert. Dies schafft die endgültige,
durchsuchbare Wissensbasis, die Ihre RAG-Agenten nutzen werden, um Informationen zu finden.

## Die Kraft der Automatisierung: Lebendiges Wissen

Ein Hauptmerkmal der Datenpipelines der Plattform ist, dass dies kein einmaliger, manueller Prozess ist. Pipelines sind
darauf ausgelegt, **automatisiert und kontinuierlich** zu sein.

Sie können eine Pipeline so konfigurieren, dass sie eine Datenquelle, wie einen SharePoint-Ordner, auf Änderungen
überwacht. Wenn ein Dokument hinzugefügt, aktualisiert oder gelöscht wird, wird die Pipeline automatisch ausgelöst und
synchronisiert die Änderungen mit der Wissensbasis.

::: tip Einrichten und vergessen
Diese kontinuierliche Synchronisierung stellt sicher, dass das Wissen Ihrer KI immer aktuell ist. Wenn eine Richtlinie
in SharePoint aktualisiert wird, stellt die Pipeline sicher, dass der Agent sofort Zugriff auf die neue Version hat,
ohne manuelles Eingreifen. Ihre Wissensbasis wird zu einer lebendigen, atmenden Entität, die sich mit Ihrer Organisation
weiterentwickelt.
:::

## Orchestrierung und Zuverlässigkeit: Auf Dagster aufgebaut

Um diese komplexen, mehrstufigen Workflows zu verwalten, verwendet der Swiss AI Hub **Dagster**, einen
industrietauglichen Datenorchestrierer. Dagster agiert als Dirigent für Ihre Datenpipelines und stellt sicher, dass
jeder Prozess zuverlässig, effizient und transparent abläuft.

Dagster ist verantwortlich für:

- **Planung und Auslösung**: Ausführung von Pipelines nach einem Zeitplan oder als Reaktion auf Ereignisse.
- **Fehlerbehandlung**: Anmutiges Management von Fehlern und Wiederholungsversuchen, um sicherzustellen, dass
  vorübergehende Probleme Ihre Daten nicht beschädigen.
- **Beobachtbarkeit (Observability)**: Bereitstellung eines vollständigen, überprüfbaren Protokolls jeder
  Pipeline-Ausführung, damit Sie genau sehen können, wie ein Dokument verarbeitet wurde und Probleme beheben können.

Diese robuste Grundlage bedeutet, dass Sie Ihren Datenpipelines vertrauen können, auch in einer Produktionsumgebung und
in großem Maßstab zuverlässig zu funktionieren.

## Der strategische Vorteil: Warum diese Architektur wichtig ist

Die Datenpipeline-Architektur der Plattform bietet mehrere entscheidende Vorteile für jede Unternehmens-KI-Strategie:

::: details Eine entkoppelte Architektur
Die Trennung der Datenerfassung (Pipelines) vom KI-Betrieb (Agenten) ist eine bewusste Designentscheidung. Sie
ermöglicht es Ihren Teams, unabhängig voneinander zu arbeiten. Das Data Engineering kann sich auf den Aufbau robuster
Pipelines und die Anbindung neuer Datenquellen konzentrieren, während KI-Entwickler sich auf die Entwicklung
intelligenter Agentenlogik konzentrieren können. Die Agenten konsumieren einfach die hochwertigen Wissensbasen, die die
Pipelines produzieren, ohne die Komplexität ihrer Erstellung kennen zu müssen.
:::

::: details Umfassende Beobachtbarkeit und Governance
Im Gegensatz zu einem „Black Box“-System wird jeder Schritt der Pipeline verfolgt und protokolliert. Wenn ein Agent eine
seltsame Antwort gibt, können Sie diese über den Abrufprozess bis zum genauen Dokument-„Chunk“ und sogar bis zur
Pipeline-Ausführung zurückverfolgen, die ihn verarbeitet hat. Dieser „Glass Box“-Ansatz ist unerlässlich für das
Debugging, die Compliance und den Aufbau von organisationalem Vertrauen.
:::

::: details Konsistenz und Qualitätskontrolle
Indem Sie die Datenverarbeitung als Code innerhalb einer Pipeline definieren, stellen Sie sicher, dass jedes Dokument
konsistent und wiederholbar behandelt wird. Sie können Qualitätsprüfungen, Validierungsregeln und
Sicherheitsüberprüfungen direkt in Ihre Pipelines einbetten, um zu gewährleisten, dass nur qualitativ hochwertige,
konforme Informationen in Ihre Wissensbasen gelangen.
:::
