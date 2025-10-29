---
title: Pipeline-Grundlagen
source_sha: "daf3baf2ab41fadeb40bd93671df5627bac3b95a71cac5135344b63f25b2d9f3"
---

# Pipeline-Grundlagen

Das AI-Hub Pipeline SDK basiert auf [Dagster](https://docs.dagster.io/). Diese Seite stellt die wesentlichen Bausteine vor, die jede Pipeline bilden.

## Assets: Die Daten

Ein **Asset** ist das zentrale Konzept in einer Pipeline. Es repräsentiert eine bestimmte Menge von Daten, wie zum Beispiel einen Satz geparster Dokumente oder eine Sammlung von Vektor-Embeddings. Der Code, den Sie für ein Asset schreiben, ist die Funktion, die diese Daten erzeugt.

  * **`@asset` / `@graph_asset`**: Diese Decorators definieren eine Funktion als Asset. Ein `graph_asset` ist ein spezieller Typ, der aus mehreren kleineren Operationen (`@op`) besteht, die miteinander verbunden sind.
  * **Rolle**: Assets definieren das „Was“ Ihrer Pipeline – die Transformationen, die Rohdateien in wertvolle, KI-bereite Daten umwandeln.

## I/O-Manager

Ein **I/O-Manager** verwaltet die physische Speicherung und den Abruf von Assets. Sie sind die „Verbindung“, die ein Asset mit dem nächsten verbindet.

  * **Funktion**: Wenn ein Asset Daten produziert (z.B. ein `RefDocDocument`), ist sein I/O-Manager dafür verantwortlich, diese in einem bestimmten Speichersystem (wie MongoDB) zu speichern. Wenn ein nachgeschaltetes Asset diese Daten benötigt, weiß der I/O-Manager, wie er sie laden muss.
  * **Rolle**: I/O-Manager abstrahieren die Speicherlogik. Ihr Asset-Code muss nicht wissen, *wo* oder *wie* Daten gespeichert werden, wodurch Ihre Pipeline hochmodular und einfach rekonfigurierbar wird.

## Ressourcen: Die externen Verbindungen

Eine **Ressource** verwaltet die Verbindung zu einem externen System, wie einer Datenbank, einer API oder einem Dateispeicher.

  * **Funktion**: Ressourcen verwalten die Konfiguration, Authentifizierung und die benötigten Verbindungsklienten, um mit der Außenwelt zu interagieren. Zum Beispiel verwaltet die `MongoDocumentStoreResource` den Verbindungsstring und den Klienten für die Kommunikation mit MongoDB.
  * **Rolle**: Ressourcen trennen die Logik Ihrer Pipeline von ihrer Umgebungskonfiguration, wodurch derselbe Pipeline-Code nahtlos in Entwicklung, Test und Produktion ausgeführt werden kann.

-----

## Wesentliche Architekturprinzipien

- Anstatt ganze Pipelines nach einem festen Zeitplan auszuführen, verwendet das SDK **beobachtbare Quell-Assets**. Diese Assets überwachen eine Datenquelle (wie einen S3-Bucket) und lösen die nachgeschaltete Verarbeitung nur aus, wenn eine Datei hinzugefügt oder geändert wird. Dies ist hoch effizient und spart Zeit und Rechenressourcen.
- Jedes Dokument wird in einer eigenen **Partition** verarbeitet. Das bedeutet, dass ein Fehler in einem Dokument nicht die gesamte Pipeline stoppt. Die anderen Dokumente werden unabhängig voneinander weiterverarbeitet. Dies ermöglicht auch massive Parallelität, da Dagster viele Partitionen gleichzeitig verarbeiten kann.
- Um Boilerplate-Code zu reduzieren und Konsistenz zu gewährleisten, stützt sich das SDK stark auf das **Factory-Muster**. Anstatt komplexe Asset- und Ressourcendefinitionen von Grund auf neu zu schreiben, verwenden Sie einfache Factory-Funktionen (z.B. `documents_factory`, `default_definitions`), die vollständig konfigurierte Pipeline-Komponenten für Sie generieren.

## Nächste Schritte

Nachdem Sie nun die grundlegenden Komponenten verstanden haben, erkunden Sie die **[Core Pipeline Patterns](../2_core_patterns/)**, um zu sehen, wie diese Konzepte im Code implementiert werden, um leistungsstarke Workflows zu erstellen.
