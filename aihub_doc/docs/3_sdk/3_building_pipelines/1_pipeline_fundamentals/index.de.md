---
title: Grundlagen von Pipelines
source_sha: 6b09107f90bd34b8f90e78d8c5c492d732b4423bf1573598d397602432ef34d2
---

# Grundlagen von Pipelines

Das AI-Hub Pipeline SDK basiert auf [Dagster](https://docs.dagster.io/). Diese Seite stellt die wesentlichen Bausteine
vor, die jede Pipeline bilden.

## Assets: Die Daten

Ein **Asset** ist das zentrale Konzept in einer Pipeline. Es repräsentiert eine spezifische Dateneinheit, wie z.B. eine
Menge von geparsten Dokumenten oder eine Sammlung von Vektor-Embeddings. Der Code, den Sie für ein Asset schreiben, ist
die Funktion, die diese Daten produziert.

- **`@asset` / `@graph_asset`**: Diese Decorators definieren eine Funktion als Asset. Ein `graph_asset` ist ein
  spezieller Typ, der aus mehreren kleineren Operationen (`@op`) besteht, die miteinander verbunden sind.
- **Rolle**: Assets definieren das „Was“ Ihrer Pipeline – die Transformationen, die Rohdateien in wertvolle, AI-fähige
  Daten umwandeln.

## I/O Manager

Ein **I/O Manager** verwaltet die physische Speicherung und den Abruf von Assets. Sie sind die „Verrohrung“, die ein
Asset mit dem nächsten verbindet.

- **Was sie tun**: Wenn ein Asset Daten produziert (z.B. ein `RefDocDocument`), ist sein I/O Manager dafür
  verantwortlich, diese in einem spezifischen Speichersystem (wie MongoDB) zu speichern. Wenn ein nachgelagertes Asset
  diese Daten benötigt, weiß der I/O Manager, wie er sie laden kann.
- **Rolle**: I/O Manager abstrahieren die Speicherlogik. Ihr Asset-Code muss nicht wissen, *wo* oder *wie* Daten
  gespeichert werden, was Ihre Pipeline hochmodular und einfach zu rekonfigurieren macht.

## Resources: Die externen Verbindungen

Ein **Resource** verwaltet die Verbindung zu einem externen System, wie einer Datenbank, einer API oder einem
Dateispeicher.

- **Was sie tun**: Resources kümmern sich um die Konfiguration, Authentifizierung und Verbindungs-Clients, die für die
  Interaktion mit der Außenwelt erforderlich sind. Zum Beispiel verwaltet die `MongoDocumentStoreResource` den
  Verbindungsstring und den Client für die Kommunikation mit MongoDB.
- **Rolle**: Resources trennen die Logik Ihrer Pipeline von ihrer Umgebungskonfiguration, wodurch derselbe Pipeline-Code
  nahtlos in Entwicklung, Test und Produktion ausgeführt werden kann.

______________________________________________________________________

## Architektonische Kernprinzipien

- Anstatt ganze Pipelines nach einem festen Zeitplan auszuführen, verwendet das SDK **beobachtbare Quell-Assets**. Diese
  Assets überwachen eine Datenquelle (wie einen S3-Bucket) und lösen die nachgelagerte Verarbeitung nur dann aus, wenn
  eine Datei hinzugefügt oder geändert wird. Dies ist hocheffizient und spart Zeit und Rechenressourcen.
- Jedes Dokument wird in seiner eigenen **Partition** verarbeitet. Das bedeutet, dass ein Fehler in einem Dokument nicht
  die gesamte Pipeline zum Stillstand bringt. Die anderen Dokumente werden unabhängig voneinander weiterverarbeitet.
  Dies ermöglicht auch eine massive Parallelisierung, da Dagster viele Partitionen gleichzeitig verarbeiten kann.
- Um Boilerplate-Code zu reduzieren und Konsistenz zu gewährleisten, stützt sich das SDK stark auf das
  **Factory-Pattern**. Anstatt komplexe Asset- und Resource-Definitionen von Grund auf neu zu schreiben, verwenden Sie
  einfache Factory-Funktionen (z.B. `documents_factory`, `default_definitions`), die vollständig konfigurierte
  Pipeline-Komponenten für Sie generieren.

## Nächste Schritte

Nachdem Sie nun die grundlegenden Komponenten verstanden haben, erkunden Sie die
**[Wichtige Pipeline-Muster](../2_core_patterns/)**, um zu sehen, wie diese Konzepte im Code implementiert werden, um
leistungsstarke Workflows zu erstellen.
