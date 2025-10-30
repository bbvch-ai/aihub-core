---
title: Containersicherheit
source_sha: 07e8d4352d6adbe3bb6552f0c0830721006e018879fd9bea7074338c7b72be14
---

# Containersicherheit

Der Schweizer AI-Hub verwendet für alle Dienste Containerisierung (Docker) mit implementierter grundlegender
Sicherheitshärtung.

## Implementierungsstatus

| Sicherheitskontrolle               | Status                           |
| ---------------------------------- | -------------------------------- |
| Ausführung als Nicht-Root-Benutzer | Implementiert                    |
| Multi-Stage-Builds                 | Implementiert                    |
| Minimale Basis-Images              | Implementiert                    |
| Seccomp-Profile                    | Nicht konfiguriert               |
| AppArmor/SELinux                   | Nicht konfiguriert               |
| Dropping von Capabilities          | Nicht konfiguriert               |
| Nur-Lese-Root-Dateisystem          | Nicht konfiguriert               |
| Netzwerksegmentierung              | Grundlegend (einzelnes Netzwerk) |

## Implementierte Kontrollen

### Ausführung als Nicht-Root-Benutzer

Jeder Container wird als nicht-privilegierter Benutzer ausgeführt (UID 1000, GID 1000). Alle Anwendungsprozesse laufen
ohne Root-Rechte, wodurch der Schaden durch Container-Escape-Schwachstellen begrenzt und eine Privilegienerhöhung
verhindert wird.

### Multi-Stage-Builds

Container verwenden Multi-Stage-Builds, die Build- und Laufzeitumgebungen trennen. Die Builder-Stufe kompiliert
Abhängigkeiten mit Build-Tools, während die Laufzeit-Stufe nur die notwendigen Artefakte kopiert und Build-Tools vom
finalen Image ausschließt. Dies reduziert die Angriffsfläche und die Image-Größe.

### Minimale Basis-Images

Basis-Images verwenden die Slim-Variante (~150MB) anstelle des vollständigen Debian (~1GB). Dies bietet weniger Pakete,
eine kleinere Angriffsfläche und ein reduziertes CVE-Risiko, während die Kompatibilität mit Python-Paketen erhalten
bleibt.

### Regelmäßige Aktualisierungen der Basis-Images

Container-Images werden für jedes Release aus dem Quellcode neu erstellt, wodurch sichergestellt wird, dass die
Basis-Images mit den neuesten Sicherheitspatches aktuell bleiben. Images folgen den Prinzipien der unveränderlichen
Infrastruktur und werden niemals direkt (in-place) gepatcht.

## Verwandte Dokumentation

- [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) – Container-Orchestrierung
- [Eingabevalidierung](../2_input_validation/) – Verhinderung bösartiger Eingaben
- [Datenverschlüsselung](../5_data_encryption/) – Datenschutz
