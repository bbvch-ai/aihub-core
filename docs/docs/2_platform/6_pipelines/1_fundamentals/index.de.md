---
title: Grundlagen
source_sha: 4f9f292510e109f3a897da5f0ed758ba7fd640ae3f32a316e9b3893647432918
---

# Grundlagen von Pipelines

## Implementierung mit Dagster

Pipelines werden als Python-Code mit Dagster definiert. Dieser Ansatz ermöglicht:

- Kundenspezifische Verarbeitungslogik für bestimmte Inhaltstypen, Geschäftsregeln oder Qualitätsstandards
- Bedingte Workflows, bei denen die Verarbeitungswege je nach Dokumentinhalt, Quelle oder Klassifizierung variieren
- Fehlerbehandlung für Netzwerkprobleme, Datenanomalien oder Systemausfälle

Pipeline-Code ist über verschiedene Datenquellen und Agenten hinweg wiederverwendbar. Teams können Pipelines erstellen
und ändern, ohne den Agenten-Code anpassen zu müssen.

## Datenquellen

Die Plattform umfasst einen vorgefertigten SharePoint-Konnektor für die automatisierte Synchronisierung mit
SharePoint-Sites und Dokumentenbibliotheken. Dokumente können auch manuell über die Benutzeroberfläche zur Verarbeitung
hochgeladen werden.

Benutzerdefinierte Konnektoren für zusätzliche Quellen erfordern die Implementierung von I/O-Managern und Operationen,
die spezifisch für Ihre Datenquelle sind, unter Verwendung des [Pipeline-SDKs](../../../3_sdk/3_building_pipelines/).

## Qualitäts- und Sicherheitskontrollen

Pipelines können Validierungs- und Sicherheitsschritte umfassen:

- Die Inhaltsvalidierung prüft eingehende Daten auf Qualität und Vollständigkeit. Dokumente, die die Validierung nicht
  bestehen, können zur Überprüfung unter Quarantäne gestellt werden.
- Das Security Scanning prüft auf bösartige Inhalte oder Richtlinienverstöße vor der Aufnahme.
- Die Datenbereinigung wendet Transformationsregeln an, um sensible Informationen zu redigieren oder
  Klassifizierungsrichtlinien durchzusetzen.

Alle Pipeline-Aktionen werden protokolliert, wodurch eine Audit-Spur von der Dokumentenabfrage über die Verarbeitung bis
zur Speicherung entsteht.
