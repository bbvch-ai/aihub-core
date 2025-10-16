---
title: Grundlagen
index: 2
source_sha: "3b6609f94a70bfeceb7825ee33b4edd3156b299a062702b663de75044730b376"
---

# Pipeline-Grundlagen

Datenpipelines sind das Rückgrat des Wissens Ihrer KI, verantwortlich für die automatisierte und kontinuierliche Synchronisation von Informationen zwischen Ihren Quellsystemen und der Wissensbasis der KI. Sie sind die robusten, zuverlässigen Workflows, die sicherstellen, dass Ihre KI-Agenten mit stets aktuellen, präzisen und sicheren Informationen arbeiten.

Dieser Abschnitt erläutert die Kernprinzipien der Datenpipeline-Architektur der Plattform und erklärt, wie sie aufgebaut sind, was sie leisten können und warum sie für KI auf Unternehmensebene unerlässlich sind.

## Der Zweck einer Pipeline: Kontinuierliche Synchronisation

In einem dynamischen Geschäftsumfeld ändern sich Informationen ständig. Eine neue Richtlinie wird veröffentlicht, ein technisches Handbuch wird aktualisiert, ein Projektstatusbericht wird überarbeitet. Eine statische Wissensbasis, die nur periodisch aktualisiert wird, wird schnell zu einer Belastung und führt zu KI-gestützten Entscheidungen, die auf veralteten Informationen basieren.

Datenpipelines lösen dieses Problem durch **kontinuierliche Synchronisation**. Sie sind persistente, automatisierte Prozesse, die Ihre ausgewählten Datenquellen überwachen, wie z.B. eine SharePoint-Website oder ein Netzlaufwerk. Wenn ein Dokument hinzugefügt, geändert oder gelöscht wird, erkennt die Pipeline die Änderung automatisch und leitet sie durch die gesamte Verarbeitungskette, wodurch sichergestellt wird, dass die Wissensbasis der KI den Zustand Ihrer Quellsysteme perfekt widerspiegelt.

::: info Was ist eine „KI-bereite“ Wissensbasis?
Eine KI-bereite Wissensbasis ist nicht nur eine Sammlung von Dateien. Es ist eine hochstrukturierte Vektordatenbank, in der Dokumente geparst, in sinnvolle Abschnitte zerlegt und in numerische Darstellungen (Embeddings) umgewandelt wurden. Dies ermöglicht es KI-Agenten, semantische Suchen basierend auf Bedeutung und nicht nur auf Schlüsselwörtern durchzuführen. Der gesamte Prozess der Erstellung und Pflege dieser spezialisierten Datenbank wird von Datenpipelines verwaltet.
:::

## Aufbau auf einer Grundlage von Code und Kontrolle

Die Pipelines des Swiss AI Hub basieren auf **Dagster**, einem modernen, unternehmensgerechten Orchestrierungs-Framework. Dies ist eine bewusste Wahl, die immense Flexibilität und Kontrolle bietet. Da Pipelines als Code (Python) definiert werden, sind sie keine einfachen „Connect-the-dots“-Workflows, sondern leistungsstarke, programmierbare Assets.

Dieser codebasierte Ansatz ermöglicht ausgeklügelte Funktionen, die für viele rein visuelle Plattformen unerreichbar sind:
- **Benutzerdefinierte Verarbeitungslogik**: Sie können spezialisierte Schritte implementieren, die auf Ihre einzigartigen Inhaltstypen, Geschäftsregeln oder Qualitätsstandards zugeschnitten sind.
- **Bedingte Workflows**: Der Pfad der Pipeline kann sich basierend auf dem Inhalt, der Quelle oder der Klassifizierung eines Dokuments ändern. Zum Beispiel könnte ein Vertrag einen zusätzlichen PII-Redaktionsschritt durchlaufen, den ein öffentliches Handbuch überspringen würde.
- **Robuste Fehlerbehandlung**: Sie können eine präzise Logik zur Behandlung von Netzwerkproblemen, Datenanomalien oder temporären Systemausfällen definieren, wodurch Pipelines widerstandsfähig sind und bei häufigen Problemen keine manuellen Eingriffe erfordern.

Dies macht Ihre Pipelines zu wiederverwendbaren Assets, die das spezifische Wissen Ihrer Organisation darüber, wie mit ihren Daten umgegangen werden soll, kodieren.

## Lifecycle Management: Mehr als nur das Hinzufügen von Daten

Ein wirklich synchronisiertes System muss den gesamten Lebenszyklus von Informationen verwalten. Unsere Pipelines gewährleisten eine vollständige Übereinstimmung mit Ihren Quellsystemen.

-   **Wenn ein Dokument hinzugefügt wird**, verarbeitet die Pipeline es und fügt die entsprechenden Embeddings zur Wissensbasis hinzu.
-   **Wenn ein Dokument geändert wird**, entfernt die Pipeline intelligent alle veralteten Embeddings, die mit der alten Version verknüpft sind, bevor die neuen hinzugefügt werden.
-   **Wenn ein Dokument gelöscht wird**, entfernt die Pipeline alle zugehörigen Embeddings aus der Wissensbasis.

Dieses rigorose Lifecycle-Management ist entscheidend. Es verhindert, dass KI-Agenten Informationen aus alten Versionen von Dokumenten oder, schlimmer noch, aus Dokumenten abrufen, die offiziell zurückgezogen wurden.

## Enterprise-Konnektivität und Erweiterbarkeit

Die Plattform bietet eine umfangreiche Auswahl an vorgefertigten Konnektoren für die Systeme, in denen das Wissen Ihrer Organisation bereits vorhanden ist. Dies ermöglicht eine nahtlose Integration, ohne dass komplexe Datenmigrationsprojekte erforderlich sind.

::: details Unterstützte Datenquellenkategorien
- **Enterprise-Kollaborationsplattformen**: Native Verbindung zu Quellen wie Microsoft SharePoint, OneDrive, Confluence und Jira.
- **Dateisysteme**: Daten von Netzlaufwerken, lokalem Speicher oder Cloud-Speicher wie Azure Blob und S3 aufnehmen.
- **Webquellen**: Inhalte von öffentlichen Websites, technischen Dokumentationsportalen oder Branchen-Newsfeeds scrapen und verarbeiten.
:::

Entscheidend ist, dass die Architektur erweiterbar ist. Wenn Sie ein proprietäres internes System oder eine spezialisierte Datenbank haben, können Sie einen benutzerdefinierten Konnektor entwickeln, der es der Plattform ermöglicht, jede für Ihre KI-Workflows relevante Informationsquelle zu integrieren.

## Governance und Qualitätssicherung: Ein Security-First-Ansatz

Datenpipelines sind mehr als nur Datenbeweger; sie sind die erste Verteidigungslinie für die Qualität und Sicherheit des Wissens Ihrer KI. Sie integrieren ausgeklügelte Governance- und Qualitätssicherungsmechanismen direkt in den Workflow.

-   **Inhaltsvalidierung**: Pipelines können eingehende Daten auf Qualität und Vollständigkeit prüfen. Ein Dokument, dem ein kritischer Abschnitt fehlt, könnte zur menschlichen Überprüfung unter Quarantäne gestellt werden, anstatt automatisch aufgenommen zu werden.
-   **Sicherheitsscanning**: Sie können automatisierte Prüfungen auf bösartige Inhalte oder Richtlinienverstöße integrieren, um zu verhindern, dass schädliche Informationen in die Wissensbasis gelangen.
-   **Datenbereinigung**: Pipelines können automatisch Transformationsregeln anwenden, um sensible Informationen (wie Namen oder Sozialversicherungsnummern) zu schwärzen oder Datenklassifizierungsrichtlinien durchzusetzen, bevor Inhalte für Agenten zugänglich werden.

Jede Aktion, die eine Pipeline ausführt – von der anfänglichen Abfrage bis zur abschließenden Qualitätsprüfung – wird protokolliert, wodurch ein umfassender Audit-Trail entsteht, der Compliance-Berichte und forensische Analysen unterstützt. Dies stellt sicher, dass Sie stets eine klare Aufzeichnung darüber haben, wie das Wissen Ihrer KI aufgebaut wurde.
