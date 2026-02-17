---
title: Updates & Wartung
source_sha: 75edbd01ec8cbdb88255267d3146fbf060bc1e9c44d59348d656dfe219e41686
---

# Updates und Wartung

## Architektur

Der AI-Hub trennt Kernplattformkomponenten von kundenspezifischem Code. Die Kernplattform (dieses Repository) enthält
gemeinsame Basis-Komponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte Agents,
Pipelines und Prozesse. Beide verwenden unabhängige semantische Versionierung und können separat aktualisiert werden.

Kundencode fixiert eine spezifische Core-Version über `pyproject.toml`:

```toml
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue
Core-Versionen übernehmen.

---

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und architektonische Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheits-Patches

Drei Versionstags sind verfügbar:

| Tag       | Beschreibung               | Stabilität |
| --------- | -------------------------- | ---------- |
| `latest`  | Letztes stabiles Release   | Hoch       |
| `nightly` | Letzter Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versions-Tag  | Höchst     |

Kundencode verwendet eigene unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` gemerged wird, berechnet CI/CD die neue
Version und erstellt einen Git-Tag. Dies löst Komponenten-Builds für betroffene Services aus. Docker-Images werden unter
`ghcr.io/bbvch-ai/aihub-core/*` mit dem Versions-Tag veröffentlicht. Ein Changelog wird automatisch generiert.

Beispiel Core-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kundencode folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/aihub-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-<customer>/pipeline:v1.2.3
```

---

## Updates

### Core-Plattform-Updates

Abwärtskompatible Core-Updates (Patch- und Minor-Versionen) können deployed werden, indem die Image-Tags in
`docker-compose.yml` aktualisiert, neue Images gepullt und Services neu gestartet werden. Kundencode läuft unverändert
weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundencode muss aktualisiert werden, um mit der
neuen Core-Version zu funktionieren. Core- und Kundencode werden gemeinsam während eines Wartungsfensters aktualisiert.

### Kundencode-Updates

Kundencode kann unabhängig aktualisiert werden, wenn die Core-Versionsfixierung unverändert bleibt. Aktualisieren Sie
die Kunden-Image-Tags in `docker-compose.yml`, pullen Sie die neuen Images und starten Sie die Kunden-Services neu.

Wenn Kundencode eine neue Core-Version übernimmt, aktualisieren Sie die Core-Versionsfixierung in `pyproject.toml`,
rebuilden Sie die Kunden-Images und deployen Sie dann Core- und Kunden-Updates gemeinsam.

---

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot
wieder her und setzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versions-Tags

Wenn Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie die Image-Tags in
`docker-compose.yml` auf die vorherigen Versionen zurücksetzen, diese Images pullen und die Services neu starten.

Core- und Kundencode können unabhängig voneinander zurückgesetzt werden, wenn sie separat aktualisiert wurden. Wenn
beide zusammen aktualisiert wurden, setzen Sie zuerst den Core, dann den Kundencode zurück.

---

## Kompatibilität

Kundencode fixiert spezifische Core-Versionen, um die Stabilität zu gewährleisten. Eine Kompatibilitätsmatrix verfolgt,
welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status      | Hinweise               |
| ------------- | ------------ | ----------- | ---------------------- |
| v1.0.0        | v0.1.2       | Legacy      | End of Life            |
| v1.1.0        | v1.2.3       | Unterstützt | Aktuelle Produktion    |
| v1.2.0        | v1.2.3       | Unterstützt | Neueste Features       |
| v2.0.0        | v2.3.4       | Testphase   | Nächstes Major Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze für die
Kompatibilitätstests vor Produktions-Updates verwenden.

---

## Monitoring

Der Observability-Stack umfasst Phoenix für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional
SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kunden-Services
(Agents, Pipelines, Prozesse) während und nach Updates.

---

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Per-Instanz-Architektur
- [Multi-Tenancy](../../16_multi_tenancy/) - Logische Trennung innerhalb von Instanzen
- [Backup und Recovery](../4_backup_and_recovery/) - Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) - Komponentenabhängigkeiten
