---
title: Grundlagen
source_sha: ec3534331862eaf786404c4661fbaafc89bc30094b60d88829ab5004f7bff01a
---

# Grundlagen von Pipelines

Daten-Pipelines sind das Rückgrat des Wissens Ihrer KI und verantwortlich für die automatisierte und kontinuierliche
Synchronisierung von Informationen zwischen Ihren Quellsystemen und der KI-Wissensbasis. Sie sind die robusten,
zuverlässigen Workflows, die sicherstellen, dass Ihre KI-Agenten mit stets aktuellen, präzisen und sicheren
Informationen arbeiten.

Dieser Abschnitt beleuchtet die Kernprinzipien der Daten-Pipeline-Architektur der Plattform, erklärt, wie sie aufgebaut
sind, was sie leisten können und warum sie für KI auf Unternehmensebene unerlässlich sind.

## Der Zweck einer Pipeline: Kontinuierliche Synchronisierung

In einem dynamischen Geschäftsumfeld ändern sich Informationen ständig. Eine neue Richtlinie wird veröffentlicht, ein
technisches Handbuch wird aktualisiert, ein Projektstatusbericht wird überarbeitet. Eine statische Wissensbasis, die nur
periodisch aktualisiert wird, wird schnell zu einer Belastung, was zu KI-gesteuerten Entscheidungen auf der Grundlage
veralteter Informationen führt.

Daten-Pipelines lösen dieses Problem durch **kontinuierliche Synchronisierung**. Sie sind persistente, automatisierte
Prozesse, die Ihre festgelegten Datenquellen, wie eine SharePoint-Website oder ein Netzlaufwerk, überwachen. Wenn ein
Dokument hinzugefügt, geändert oder gelöscht wird, erkennt die Pipeline die Änderung automatisch und verbreitet sie
durch die gesamte Verarbeitungskette, wodurch sichergestellt wird, dass die Wissensbasis der KI den Zustand Ihrer
Quellsysteme perfekt widerspiegelt.

::: info Was ist eine „KI-bereite“ Wissensbasis?
Eine KI-bereite Wissensbasis ist nicht nur eine Sammlung von Dateien. Es ist eine hochstrukturierte Vektordatenbank, in
der Dokumente geparst, in sinnvolle Abschnitte zerlegt und in numerische Darstellungen (Embeddings) umgewandelt wurden.
Dies ermöglicht es KI-Agenten, semantische Suchen basierend auf Bedeutung und nicht nur auf Schlüsselwörtern
durchzuführen. Der gesamte Prozess der Erstellung und Pflege dieser spezialisierten Datenbank wird von Daten-Pipelines
verwaltet.
:::

## Aufgebaut auf einer Grundlage von Code und Kontrolle

Die Pipelines des Swiss AI Hubs basieren auf **Dagster**, einem modernen, unternehmenstauglichen
Orchestrierungs-Framework. Dies ist eine bewusste Entscheidung, die immense Flexibilität und Kontrolle bietet. Weil
Pipelines als Code (Python) definiert sind, sind sie keine einfachen „Punkt-zu-Punkt“-Workflows, sondern
leistungsstarke, programmierbare Assets.

Dieser codebasierte Ansatz ermöglicht anspruchsvolle Funktionen, die vielen rein visuellen Plattformen vorenthalten
bleiben:

- **Benutzerdefinierte Verarbeitungslogik**: Sie können spezialisierte Schritte implementieren, die auf Ihre
  einzigartigen Inhaltstypen, Geschäftsregeln oder Qualitätsstandards zugeschnitten sind.
- **Bedingte Workflows**: Der Pfad der Pipeline kann sich basierend auf dem Inhalt, der Quelle oder der Klassifizierung
  eines Dokuments ändern. Zum Beispiel könnte ein Vertrag einen zusätzlichen PII-Redaktionsschritt durchlaufen, den ein
  öffentliches Handbuch überspringen würde.
- **Robuste Fehlerbehandlung**: Sie können präzise Logik zur Behandlung von Netzwerkproblemen, Datenanomalien oder
  temporären Systemausfällen definieren, um sicherzustellen, dass Pipelines widerstandsfähig sind und bei häufigen
  Problemen keine manuelle Intervention erfordern.

Dies macht Ihre Pipelines zu wiederverwendbaren Assets, die das spezifische Wissen Ihrer Organisation über den Umgang
mit ihren Daten kodieren.

## Lifecycle Management: Mehr als nur Daten hinzufügen

Ein wirklich synchronisiertes System muss den gesamten Lebenszyklus von Informationen verwalten. Unsere Pipelines wahren
die vollständige Übereinstimmung mit Ihren Quellsystemen.

- **Wenn ein Dokument hinzugefügt wird**, verarbeitet die Pipeline es und fügt die entsprechenden Embeddings zur
  Wissensbasis hinzu.
- **Wenn ein Dokument geändert wird**, entfernt die Pipeline intelligent alle veralteten Embeddings, die mit der alten
  Version verknüpft sind, bevor sie die neuen hinzufügt.
- **Wenn ein Dokument gelöscht wird**, bereinigt die Pipeline alle zugehörigen Embeddings aus der Wissensbasis.

Dieses rigorose Lifecycle-Management ist entscheidend. Es verhindert, dass KI-Agenten Informationen aus alten Versionen
von Dokumenten abrufen oder, schlimmer noch, aus Dokumenten, die offiziell zurückgezogen wurden.

## Enterprise-Konnektivität und Erweiterbarkeit

Die Plattform bietet eine umfangreiche Auswahl an vorgefertigten Konnektoren für die Systeme, in denen das Wissen Ihrer
Organisation bereits vorhanden ist. Dies ermöglicht eine nahtlose Integration, ohne komplexe Datenmigrationsprojekte zu
erfordern.

::: details Unterstützte Datenquellen-Kategorien
- **Enterprise-Kollaborationsplattformen**: Native Verbindung zu Quellen wie Microsoft SharePoint, OneDrive, Confluence
  und Jira.
- **Dateisysteme**: Daten von Netzlaufwerken, lokalem Speicher oder Cloud-Speicher wie Azure Blob und S3 ingestieren.
- **Web-Quellen**: Inhalte von öffentlichen Websites, technischen Dokumentationsportalen oder Branchen-Newsfeeds scrapen
  und verarbeiten.
:::

Entscheidend ist, dass die Architektur erweiterbar ist. Wenn Sie ein proprietäres internes System oder eine
spezialisierte Datenbank haben, können Sie einen benutzerdefinierten Konnektor entwickeln, wodurch die Plattform jede
für Ihre KI-Workflows relevante Informationsquelle integrieren kann.

## Governance und Qualitätssicherung: Ein sicherheitsorientierter Ansatz

Daten-Pipelines sind mehr als nur Datenbeweger; sie sind die erste Verteidigungslinie für die Qualität und Sicherheit
des Wissens Ihrer KI. Sie integrieren ausgeklügelte Governance- und Qualitätssicherungsmechanismen direkt in den
Workflow.

- **Inhaltsvalidierung**: Pipelines können eingehende Daten auf Qualität und Vollständigkeit prüfen. Ein Dokument, dem
  ein kritischer Abschnitt fehlt, könnte zur menschlichen Überprüfung unter Quarantäne gestellt werden, anstatt
  automatisch ingestiert zu werden.
- **Sicherheitsscans**: Automatisierte Prüfungen auf bösartige Inhalte oder Richtlinienverstöße können integriert
  werden, wodurch verhindert wird, dass schädliche Informationen in die Wissensbasis gelangen.
- **Datenbereinigung**: Pipelines können automatisch Transformationsregeln anwenden, um sensible Informationen (wie
  Namen oder Sozialversicherungsnummern) zu schwärzen oder Datenklassifizierungsrichtlinien durchzusetzen, bevor Inhalte
  für Agenten zugänglich werden.

Jede von einer Pipeline durchgeführte Aktion – von der anfänglichen Abfrage bis zur abschließenden Qualitätsprüfung –
wird protokolliert, wodurch ein umfassender Audit-Trail entsteht, der Compliance-Berichterstattung und forensische
Analysen unterstützt. Dies stellt sicher, dass Sie immer eine klare Aufzeichnung darüber haben, wie das Wissen Ihrer KI
aufgebaut wurde.
