---
title: Containersicherheit
source_sha: 1e2e740bf41262098fceca82cb7beb4d2d7f4b803e80eec1580e2359eaeeaf8d
---

# Containersicherheit

Der Schweizer Swiss AI Hub nutzt Containerisierung (Docker) für alle Dienste mit grundlegenden Sicherheitsvorkehrungen.

## Implementierungsstatus

| Sicherheitskontrolle               | Status                           |
| ---------------------------------- | -------------------------------- |
| Ausführung als Nicht-Root-Benutzer | Implementiert                    |
| Multi-Stage-Builds                 | Implementiert                    |
| Minimale Basis-Images              | Implementiert                    |
| Seccomp Profiles                   | Nicht konfiguriert               |
| AppArmor/SELinux                   | Nicht konfiguriert               |
| Capability Dropping                | Nicht konfiguriert               |
| Read-Only Root Filesystem          | Nicht konfiguriert               |
| Network Segmentation               | Grundlegend (einzelnes Netzwerk) |

## Implementierte Kontrollen

### Ausführung als Nicht-Root-Benutzer

Jeder Container läuft als nicht privilegierter Benutzer (UID 1000, GID 1000). Alle Anwendungsprozesse laufen ohne
Root-Rechte ab, was den Schaden durch Container-Escape-Schwachstellen begrenzt und eine Privilegieneskalation
verhindert.

### Multi-Stage-Builds

Container verwenden Multi-Stage-Builds, die Build- und Laufzeitumgebungen trennen. Die Builder-Phase kompiliert
Abhängigkeiten mit Build-Tools, während die Laufzeitphase nur die notwendigen Artefakte kopiert und Build-Tools aus dem
finalen Image ausschließt. Dies reduziert die Angriffsfläche und die Image-Größe.

### Minimale Basis-Images

Basis-Images verwenden die Slim-Variante (~150MB) anstelle des vollständigen Debian (~1GB). Dies bietet weniger Pakete,
eine kleinere Angriffsfläche und eine reduzierte CVE-Exposition, während die Kompatibilität mit Python-Paketen erhalten
bleibt.

### Regelmäßige Basis-Image-Updates

Container-Images werden für jede Version neu aus dem Quellcode erstellt, um sicherzustellen, dass die Basis-Images mit
den neuesten Sicherheitspatches aktuell bleiben. Images folgen den Prinzipien der unveränderlichen Infrastruktur und
werden niemals direkt (in-place) gepatcht.

## Verwandte Dokumentation

- [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) - Container-Orchestrierung
- [Eingabevalidierung](../2_input_validation/) - Verhinderung bösartiger Eingaben
- [Datenverschlüsselung](../5_data_encryption/) - Datenschutz
