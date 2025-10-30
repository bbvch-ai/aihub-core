---
title: Eingabevalidierung
source_sha: 9d6f8b9cbc248b56d2e102c013efec5a1d2a991bd5583c1fb7f651d33baf4b96
---

# Eingabevalidierung

Der Swiss AI-Hub implementiert Eingabevalidierung zum Schutz vor gängigen Angriffsvektoren wie Path Traversal,
MIME-Typ-Verwechslung und fehlerhaften Daten.

## Validierung von Dateiuploads

### Whitelist für Dateitypen

Die Plattform beschränkt Uploads auf etwa 40 genehmigte Dateierweiterungen in mehreren Kategorien: Dokumentformate (PDF,
Office, Text, Markdown), Bildformate (JPEG, PNG, TIFF, WebP), Audioformate (WAV, MP3) und strukturierte Daten (JSON,
XML).

### MIME-Typ-Validierung

Die Plattform validiert, dass der bereitgestellte Inhaltstyp dem erwarteten MIME-Typ der Dateierweiterung entspricht.
Dies verhindert MIME-Typ-Verwechslungsangriffe, bei denen sich bösartige Dateien mit falschen MIME-Typen tarnen.

### Dateinamenvalidierung

Dateinamen müssen mit alphanumerischen Zeichen beginnen und werden validiert, um folgendes zu blockieren:

- Path Traversal-Versuche (`..`, `/`, `\`, Null-Bytes)
- Erweiterungs-Spoofing (maximal 3 durch Punkte getrennte Teile, 10 Zeichen Begrenzung für die Erweiterung)

### Dateigrößenvalidierung

Dateien müssen größer als 0 Bytes sein. Leere Dateien werden abgelehnt. Maximale Größenbeschränkungen werden auf
Anwendungs- oder Reverse-Proxy-Ebene erzwungen.

## Validierung von Namespace- und Datenbanknamen

Datenbank- und Namespace-Namen folgen ähnlichen Validierungsregeln, um Path Traversal in logischen Speicherpfaden zu
verhindern.

## Wovor die Eingabevalidierung schützt

- Path Traversal-Angriffe
- MIME-Typ-Verwechslung
- Erweiterungs-Spoofing
- Null-Byte-Injektion
- Uploads ausführbarer Dateien
- Ressourcenerschöpfung (mittels Größenbeschränkungen)

## Verwandte Dokumentation

- [Authentifizierung & Autorisierung](../1_authentication/) - Benutzeridentität und Zugriffssteuerung
- [Container-Sicherheit](../3_container_security/) - Isolierte Dateiverarbeitung
- [RBAC](../../11_access_management/2_permissions/) - Berechtigungsbasierte Upload-Beschränkungen
