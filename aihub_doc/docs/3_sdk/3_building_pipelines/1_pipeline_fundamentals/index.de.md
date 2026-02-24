```markdown
---
title: Pipeline-Grundlagen
source_sha: "3b86f4e32f2d1c7626ad0324347dc35f908718252cc2a00835c40215f507ea2e"
---

# Pipeline-Grundlagen

Das AI-Hub Pipeline SDK basiert auf [Dagster](https://docs.dagster.io/). Diese Seite stellt die wesentlichen Bausteine vor, aus denen jede Pipeline besteht.

## Assets: Die Daten

Ein **Asset** ist das zentrale Konzept in einer Pipeline. Es repräsentiert eine spezifische Dateneinheit, wie zum Beispiel eine Menge geparster Dokumente oder eine Sammlung von Vektor-Embeddings. Der Code, den Sie für ein Asset schreiben, ist die Funktion, die diese Daten produziert.

- **`@asset` / `@graph_asset`**: Diese Dekoratoren definieren eine Funktion als Asset. Ein `graph_asset` ist ein spezieller Typ, der aus mehreren kleineren Operationen (`@op`) zusammengesetzt ist, die miteinander verbunden sind.
- **Rolle**: Assets definieren das „Was“ Ihrer Pipeline – die Transformationen, die Rohdateien in wertvolle, KI-bereite Daten umwandeln.

## I/O Manager

Ein **I/O Manager** verwaltet die physische Speicherung und den Abruf von Assets. Sie sind die „Verrohrung“, die ein Asset mit dem nächsten verbindet.

- **Was sie tun**: Wenn ein Asset Daten produziert (z.B. ein `RefDocDocument`), ist sein I/O Manager dafür verantwortlich, diese in einem spezifischen Speichersystem (wie MongoDB) zu speichern. Wenn ein nachgeschaltetes Asset diese Daten benötigt, weiß der I/O Manager, wie er sie laden muss.
- **Rolle**: I/O Manager abstrahieren die Speicherlogik. Ihr Asset-Code muss nicht wissen, *wo* oder *wie* Daten gespeichert werden, was Ihre Pipeline hochmodular und einfach rekonfigurierbar macht.

## Ressourcen: Die externen Verbindungen

Eine **Ressource** verwaltet die Verbindung zu einem externen System, wie einer Datenbank, einer API oder einem Dateispeicher.

- **Was sie tun**: Ressourcen kümmern sich um die Konfiguration, Authentifizierung und die benötigten Verbindungs-Clients, um mit der Außenwelt zu interagieren. Zum Beispiel verwaltet die `MongoDocumentStoreResource` die Verbindungszeichenfolge und den Client für die Kommunikation mit MongoDB.
- **Rolle**: Ressourcen trennen die Logik Ihrer Pipeline von ihrer Umgebungskonfiguration, wodurch derselbe Pipeline-Code nahtlos in Entwicklung, Test und Produktion ausgeführt werden kann.

______________________________________________________________________

## Architekturprinzipien

- Anstatt ganze Pipelines nach einem festen Zeitplan auszuführen, verwendet das SDK **observable source assets**. Diese Assets überwachen eine Datenquelle (wie einen S3-Bucket) und lösen die nachgeschaltete Verarbeitung nur aus, wenn eine Datei hinzugefügt oder geändert wird. Dies ist hoch effizient und spart Zeit und Rechenressourcen.
- Jedes Dokument wird in einer eigenen **Partition** verarbeitet. Das bedeutet, dass ein Fehler in einem Dokument nicht die gesamte Pipeline stoppt. Die anderen Dokumente werden unabhängig voneinander weiterverarbeitet. Dies ermöglicht auch eine massive Parallelisierung, da Dagster viele Partitionen gleichzeitig verarbeiten kann.
- Um Boilerplate-Code zu reduzieren und Konsistenz zu gewährleisten, setzt das SDK stark auf das **Factory Pattern**. Anstatt komplexe Asset- und Ressourcendefinitionen von Grund auf neu zu schreiben, verwenden Sie einfache Factory-Funktionen (z.B. `documents_factory`, `default_definitions`), die vollständig konfigurierte Pipeline-Komponenten für Sie generieren.

## Nächste Schritte

Nachdem Sie nun die grundlegenden Komponenten verstanden haben, erkunden Sie die **[Core Pipeline Patterns](../2_core_patterns/)**, um zu sehen, wie diese Konzepte im Code implementiert werden, um leistungsstarke Workflows zu erstellen.
```
