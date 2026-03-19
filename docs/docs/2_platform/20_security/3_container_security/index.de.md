---
title: Container-Sicherheit
source_sha: "4de371da81a3f7c29c560a9062e898789573bdae89a9a9e757fffff0e25dd8de"
---

# Container-Sicherheit

Der Swiss AI Hub verwendet Containerisierung (Docker) für alle Services mit implementierter grundlegender Sicherheitshärtung.

## Implementierungsstatus

| Sicherheitskontrolle            | Status                 |
| :------------------------------ | :--------------------- |
| Ausführung als Nicht-Root-Benutzer | Implementiert          |
| Multi-Stage-Builds              | Implementiert          |
| Minimale Basis-Images           | Implementiert          |
| Seccomp-Profile                 | Nicht konfiguriert     |
| AppArmor/SELinux                | Nicht konfiguriert     |
| Capability Dropping             | Nicht konfiguriert     |
| Nur-Lese-Root-Dateisystem       | Nicht konfiguriert     |
| Netzwerksegmentierung           | Grundlegend (einzelnes Netzwerk) |

## Implementierte Kontrollen

### Ausführung als Nicht-Root-Benutzer

Jeder Container läuft als nicht-privilegierter Benutzer (UID 1000, GID 1000). Alle Anwendungsprozesse laufen ohne Root-Berechtigungen ab, wodurch Schäden durch Container-Escape-Schwachstellen begrenzt und eine Privilegieneskalation verhindert werden.

### Multi-Stage-Builds

Container verwenden Multi-Stage-Builds, die Build- und Laufzeitumgebungen trennen. Die Builder-Phase kompiliert Abhängigkeiten mit Build-Tools, während die Laufzeitphase nur notwendige Artefakte kopiert und Build-Tools aus dem finalen Image ausschließt. Dies reduziert die Angriffsfläche und die Image-Größe.

### Minimale Basis-Images

Basis-Images verwenden die Slim-Variante (~150MB) anstelle des vollen Debian (~1GB). Dies bietet weniger Pakete, eine kleinere Angriffsfläche und eine reduzierte CVE-Exposition, während die Kompatibilität mit Python-Paketen erhalten bleibt.

### Regelmäßige Updates der Basis-Images

Container-Images werden für jedes Release aus dem Quellcode neu erstellt, um sicherzustellen, dass die Basis-Images mit Sicherheits-Patches aktuell bleiben. Images folgen den Prinzipien der unveränderlichen Infrastruktur und werden niemals direkt (in place) gepatcht.

## Verwandte Dokumentation

- [Bereitstellungsoptionen](../../3_deployment_guide/1_deployment_options/) - Container-Orchestrierung
- [Eingabeprüfung](../2_input_validation/) - Verhinderung bösartiger Eingaben
- [Datenverschlüsselung](../5_data_encryption/) - Datenschutz
