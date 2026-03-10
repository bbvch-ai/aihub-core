---
title: Eingabevalidierung
source_sha: 4d97de8c18c8e8f2ceb6b2fd511b94dd93ae42a31a91766606d6a1d78285937e
---

# Eingabevalidierung

Der Swiss AI Hub implementiert eine Eingabevalidierung, um vor gängigen Angriffsvektoren wie Path Traversal,
MIME-Typ-Verwechslung und fehlerhaften Daten zu schützen.

## Validierung von Datei-Uploads

### Whitelist für Dateitypen

Die Plattform beschränkt Uploads auf etwa 40 genehmigte Dateierweiterungen aus mehreren Kategorien: Dokumentformate
(PDF, Office, Text, Markdown), Bildformate (JPEG, PNG, TIFF, WebP), Audioformate (WAV, MP3) und strukturierte Daten
(JSON, XML).

### Validierung des MIME-Typs

Die Plattform validiert, dass der bereitgestellte Content-Typ dem erwarteten MIME-Typ für die Dateierweiterung
entspricht. Dies verhindert Angriffe durch MIME-Typ-Verwechslung, bei denen bösartige Dateien sich mit falschen
MIME-Typen tarnen.

### Validierung von Dateinamen

Dateinamen müssen mit alphanumerischen Zeichen beginnen und werden validiert, um folgendes zu blockieren:

- Path Traversal-Versuche (`..`, `/`, `\`, Null-Bytes)
- Erweiterungs-Spoofing (maximal 3 durch Punkte getrennte Teile, 10-Zeichen-Begrenzung für Erweiterungen)

### Validierung der Dateigröße

Dateien müssen größer als 0 Bytes sein. Leere Dateien werden abgelehnt. Maximale Größenbeschränkungen werden auf
Anwendungs- oder Reverse Proxy-Ebene durchgesetzt.

## Validierung von Namespace- und Datenbanknamen

Datenbank- und Namespace-Namen folgen ähnlichen Validierungsregeln, um Path Traversal in logischen Speicherpfaden zu
verhindern.

## Wovor die Eingabevalidierung schützt

- Path Traversal-Angriffe
- MIME-Typ-Verwechslung
- Erweiterungs-Spoofing
- Null-Byte-Injection
- Uploads ausführbarer Dateien
- Ressourcenerschöpfung (mittels Größenbeschränkungen)

## Verwandte Dokumentation

- [Authentifizierung & Autorisierung](../1_authentication/) – Benutzeridentität und Zugriffssteuerung
- [Container-Sicherheit](../3_container_security/) – Isolierte Dateiverarbeitung
- [RBAC](../../11_access_management/2_permissions/) – Berechtigungsbasierte Upload-Beschränkungen
