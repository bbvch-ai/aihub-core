---
title: Eingabevalidierung
source_sha: f7259ebb3f6ff9bb418a9a1a65f9de4371ed5214fcb349c6b489b37d834d2aff
---

# Eingabevalidierung

Der Swiss AI Hub implementiert eine Eingabevalidierung, um vor gängigen Angriffsvektoren wie Pfad-Traversal,
MIME-Typ-Verwechslung und fehlerhaften Daten zu schützen.

## Validierung von Datei-Uploads

### Dateityp-Whitelist

Die Plattform beschränkt Uploads auf etwa 40 zugelassene Dateierweiterungen in verschiedenen Kategorien: Dokumentformate
(PDF, Office, Text, Markdown), Bildformate (JPEG, PNG, TIFF, WebP), Audioformate (WAV, MP3) und strukturierte Daten
(JSON, XML).

### MIME-Typ-Validierung

Die Plattform validiert, dass der bereitgestellte Content-Typ mit dem erwarteten MIME-Typ für die Dateierweiterung
übereinstimmt. Dies verhindert MIME-Typ-Verwechslungsangriffe, bei denen sich bösartige Dateien mit inkorrekten
MIME-Typen tarnen.

### Dateinamenvalidierung

Dateinamen müssen mit alphanumerischen Zeichen beginnen und werden validiert, um Folgendes zu blockieren:

- Pfad-Traversal-Versuche (`..`, `/`, `\`, Null-Bytes)
- Erweiterungs-Spoofing (maximal 3 durch Punkte getrennte Teile, 10-Zeichen-Erweiterungsbegrenzung)

### Dateigrössenvalidierung

Dateien müssen grösser als 0 Bytes sein. Leere Dateien werden abgelehnt. Maximale Grössenbeschränkungen werden auf
Anwendungs- oder Reverse-Proxy-Ebene erzwungen.

## Validierung von Namespace- und Datenbanknamen

Datenbank- und Namespace-Namen folgen ähnlichen Validierungsregeln, um Pfad-Traversal in logischen Speicherpfaden zu
verhindern.

## Wovor die Eingabevalidierung schützt

- Pfad-Traversal-Angriffe
- MIME-Typ-Verwechslung
- Erweiterungs-Spoofing
- Null-Byte-Injection
- Uploads ausführbarer Dateien
- Ressourcenerschöpfung (mittels Grössenbegrenzungen)

## Verwandte Dokumentation

- [Authentifizierung & Autorisierung](../1_authentication/) - Benutzeridentität und Zugriffssteuerung
- [Container-Sicherheit](../3_container_security/) - Isolierte Dateiverarbeitung
- [RBAC](../../11_access_management/2_permissions/) - Berechtigungsbasierte Upload-Beschränkungen
